""" Main judge/evaluation process: 
updated @240918

- [x] add "Tool Invocation" metrics in FlowBench
"""

import re, yaml
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from easonsi.llm.openai_client import OpenAIClient, Formater

from ..data import (
    Config, Role, Message, Conversation, 
    Workflow, DBManager, DataManager, UserProfile,
    BaseLogger, LogUtils, LLM_CFG, init_client
)
from utils.jinja_templates import jinja_render
from utils.wrappers import retry_wrapper


class Judger:
    """ abstraction of judging / evaluation
    USAGE:
        judger = Judger(cfg)
        judger.start_judge()
    """
    cfg: Config = None
    db: DBManager = None
    logger: BaseLogger = None
    
    def __init__(self, cfg:Config) -> None:
        self.cfg = cfg
        self.db = DBManager(cfg.db_uri, cfg.db_name, cfg.db_message_collection_name)
        self.logger = BaseLogger()
        self.llm = init_client(llm_cfg=LLM_CFG[self.cfg.judge_model_name])

    def judge(self, mode: str="session", verbose=True) -> Dict:
        """ judge process:
        1. check if judged
        2. collect related infos
        3. judge
        4. record the result
        """
        # 0. check if judged
        assert self.cfg.judge_conversation_id is not None, "judge_conversation_id is None"
        if self.cfg.judge_force_rejudge: # whether forcing rejudge
            # remove the judge result if it has been judged
            res = self.db.delete_evaluations({ "conversation_id": self.cfg.judge_conversation_id })
        else:
            query_res = self.db.query_evaluations({ "conversation_id": self.cfg.judge_conversation_id }) # donot need {"exp_version"} becased conversaion_id 1:1 map to exp_version
            if len(query_res) > 0:
                self.logger.log(f"  <judge> {self.cfg.judge_conversation_id} has already been judged", with_print=verbose)
                return query_res[0] # out_dict

        # 1.1. get the simultead conversation
        simulated_conversation = self.db.query_messages_by_conversation_id(self.cfg.judge_conversation_id)
        assert len(simulated_conversation) > 0, "simulated conversation is empty"
        
        # 1.2. get the workflow infos
        workflow = Workflow(self.cfg)
        
        # 2. judge: call the judge model & parse the output
        self.logger.log(f"  <judge> start to judge {self.cfg.judge_conversation_id}", with_print=verbose)

        out_dict = {
            "conversation_id": self.cfg.judge_conversation_id,
            "exp_version": self.cfg.exp_version,  # these infos can also be found in `db.config`
            **{ k:v for k,v in self.cfg.to_dict().items() if k.startswith("workflow") },

            "num_turns": len(simulated_conversation),       # //2
        }
        # NOTE: standardize the judge results
        # output format: `judge_session_result, judge_session_stat`
        if mode == "session":
            out_dict |= self._judge_session(workflow, simulated_conversation)
            out_dict |= self._judge_stat_session(workflow, simulated_conversation)
        elif mode == "turn":
            out_dict |= self._judge_turn(workflow, simulated_conversation)
            out_dict |= self._judge_stat_turn(workflow, simulated_conversation)
        else: raise ValueError(f"invalid mode: {mode}")
        
        # 2.2. save the judge result to db
        self.db.insert_evaluation(out_dict)
        self.logger.log(f"  <judge> {self.cfg.judge_conversation_id} has been judged", with_print=verbose)
        return out_dict
    
    def _judge_session(
        self, workflow: Workflow, simulated_conversation: Conversation,
    ) -> Dict[str, Any]:
        """ 
        output format:
            judge_session_result: Dict of results
            judge_session_details: Dict of detailed infos
        """
        # 1. format the prompt
        _user_profile = workflow.user_profiles[self.cfg.user_profile_id]
        prompt = jinja_render(
            "flowagent/eval_session.jinja",
            user_target=_user_profile.to_str(),
            workflow_info=workflow.to_str(),
            session=simulated_conversation.to_str(),  # NOTE: format the conversation
        )
        # 2. query & parse the output
        @retry_wrapper(retry=self.cfg.judge_retry_limit, step_name="judge_session", log_fn=print)
        def judge_session(prompt):
            llm_response, _model_name, _usage = self.llm.query_one(prompt, return_usage=True)
            # 2. parse
            _slots=['Result', 'Total number of goals', 'Number of accomplished goals', 'Reason']
            _slots_to_check = _slots[:-1] # 'Reason' is not necessary
            jr = self._parse_react_output(llm_response, slots=_slots, slots_to_check=_slots_to_check)
            # 3. validate
            for s in ['Total number of goals', 'Number of accomplished goals']: 
                jr[s] = int(jr[s])
            assert jr['Result'] in ['yes', 'no']
            return jr, llm_response, _model_name, _usage
        jr, llm_response, _model_name, _usage = judge_session(prompt)
        # 3. formatted output
        return {
            "judge_session_result": jr,
            "judge_session_details": {
                "model": _model_name,   # judge model & detailed infos
                "usage": _usage,
                "prompt": prompt,
                "llm_response": llm_response,
            }
        }
    
    def _judge_turn(self, 
        workflow: Workflow, simulated_conversation: Conversation,
    ) -> Dict[str, Any]:
        out = {
            "judge_turn_result": [],
            "judge_turn_details": []
        }
        for i, msg in enumerate(simulated_conversation):
            if msg.role != Role.BOT: continue
            
            prompt = jinja_render(
                "flowagent/eval_single_with_reference.jinja",
                session=simulated_conversation[:i].to_str(),
                workflow_info=workflow.to_str(),
                reference_input=msg.content, predicted_input=msg.content_predict,
            )
            @retry_wrapper(retry=self.cfg.judge_retry_limit, step_name="judge_turn", log_fn=print)
            def judge_turn(prompt):
                llm_response, _model_name, _usage = self.llm.query_one(prompt, return_usage=True)
                jr = self._parse_react_output(llm_response, slots=['Score'], slots_to_check=['Score'])
                return jr, llm_response, _model_name, _usage
            jr, llm_response, _model_name, _usage = judge_turn(prompt)
            jr.update({
                "utterance_id": i,
                "type": simulated_conversation.get_message_by_idx(i-1).type
            })
            out["judge_turn_result"].append(jr)
            out["judge_turn_details"].append({
                "model": _model_name,   # judge model & detailed infos
                "usage": _usage,
                "prompt": prompt,
                "llm_response": llm_response,
            })
        return out
    
    def _judge_stat_session(self, workflow: Workflow, simulated_conversation: Conversation) -> Dict[str, Any]:
        _user_profile = workflow.user_profiles[self.cfg.user_profile_id]
        apis_gt = _user_profile.required_apis
        assert apis_gt is not None, "user_profile.required_apis is None"
        # stat called apis. 
        apis_pred = simulated_conversation.get_called_apis()
        return {
            "judge_session_stat": {
                "apis_gt": apis_gt,
                "apis_pred": apis_pred
            }
        }
    
    def _judge_stat_turn(self, workflow: Workflow, simulated_conversation: Conversation) -> Dict[str, Any]:
        apis_gt, apis_pred = [], []  # record the api calls for each BOT turn
        for i,msg in enumerate(simulated_conversation):
            if msg.role != Role.BOT: continue
            if msg.apis:
                api_call = msg.apis[0]
                _api_gt = (api_call.name, api_call.params)
            else: _api_gt = None
            if msg.is_api_calling(msg.content_predict):
                name, params = msg.get_api_infos(msg.content_predict)
                _api_pred = (name, params)
            else: _api_pred = None
            apis_gt.append(_api_gt)
            apis_pred.append(_api_pred)
        return {
            "judge_turn_stat": {
                "apis_gt": apis_gt,
                "apis_pred": apis_pred
            }
        }
    
    @staticmethod
    def _parse_react_output(s: str, slots:List[str], slots_to_check:List[str]=None) -> Dict[str, str]:
        if s.strip().startswith("```"):
            s = Formater.parse_codeblock(s, type="").strip()
        _slots = '|'.join(slots)    # Status Code|Data)
        pattern = f"(?P<field>{_slots}):\s*(?P<value>.*?)(?=\n({_slots}):|\Z)"
        matches = re.finditer(pattern, s, re.DOTALL)
        result = {match.group('field'): match.group('value').strip() for match in matches}
        # validate result
        if slots_to_check:
            assert all(key in result for key in slots_to_check), f"{slots_to_check} not all in prediction: \n" + LogUtils.format_infos_basic(s)
        return result
    
    def start_judge(self, mode: str="session", verbose=True):
        assert mode in ["session", "turn"], f"invalid mode: {mode}"
        infos = {
            "conversation_id": self.cfg.judge_conversation_id,
            "judge_model_name": self.cfg.judge_model_name,
            "exp_version": self.cfg.exp_version,
            **{ k:v for k,v in self.cfg.to_dict().items() if k.startswith("workflow") },
            "config": self.cfg.to_dict(),
        }
        self.logger.log(LogUtils.format_infos_with_tabulate(infos), with_print=verbose)
        
        res = self.judge(verbose=verbose, mode=mode)
        
        self.logger.log(LogUtils.format_infos_with_tabulate(res), with_print=verbose)
        return res
    