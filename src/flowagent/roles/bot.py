""" updated 240924
- [x] add pdl bot
    - [ ] check performance diff for JSON / React output
"""
import re, datetime, json
from typing import List, Tuple
from .base import BaseBot
from ..data import BotOutput, BotOutputType, Message, Role, init_client, LLM_CFG, LogUtils
from utils.jinja_templates import jinja_render
from utils.wrappers import retry_wrapper
from easonsi.llm.openai_client import OpenAIClient, Formater

class DummyBot(BaseBot):
    names: List[str] = ["dummy_bot"]
    bot_template_fn: str = ""
    
    # def __init__(self, **args) -> None:
    #     super().__init__(**args)

    def process(self, *args, **kwargs) -> BotOutput:
        """ 
        1. generate ReAct format output by LLM
        2. parse to BotOutput
        """
        self.cnt_bot_actions += 1
        
        if (self.cnt_bot_actions % 2) == 0:
            bot_output = BotOutput(action="calling api!")
            self.conv.add_message(
                Message(role=Role.BOT, content="bot action..."),
            )
        else:
            bot_output = BotOutput(response="bot response...")
            self.conv.add_message(
                Message(role=Role.BOT, content="bot response..."),
            )
        return bot_output


class ReactBot(BaseBot):
    """ ReactBot
    prediction format: 
        (Thought, Response) for response node
        (Thought, Action, Action Input) for call api node
    """
    llm: OpenAIClient = None
    bot_template_fn: str = "flowagent/bot_flowbench.jinja"
    names = ["ReactBot", "react_bot"]
    
    def __init__(self, **args) -> None:
        super().__init__(**args)
        self.llm = init_client(llm_cfg=LLM_CFG[self.cfg.bot_llm_name])
        
    def process(self, *args, **kwargs) -> BotOutput:
        """ mian process logic.
        gen prompt -> query & process -> gen message
        """
        prompt = self._gen_prompt()
        @retry_wrapper(retry=self.cfg.bot_retry_limit, step_name="bot_process", log_fn=print)
        def process_with_retry(prompt):
            llm_response, prediction = self._process(prompt)
            return llm_response, prediction
        llm_response, prediction = process_with_retry(prompt)
        
        if prediction.action_type==BotOutputType.RESPONSE:
            msg_content = prediction.response
        else:
            msg_content = f"<Call API> {prediction.action}({prediction.action_input})"
        msg = Message(
            Role.BOT, msg_content, prompt=prompt, llm_response=llm_response,
            conversation_id=self.conv.conversation_id, utterance_id=self.conv.current_utterance_id
        )
        self.conv.add_message(msg)
        self.cnt_bot_actions += 1  # stat
        return prediction

    def _gen_prompt(self) -> str:
        prompt = jinja_render(
            self.bot_template_fn,     # "flowagent/bot_flowbench.jinja": task_description, workflow, toolbox, current_time, history_conversation
            task_description=self.workflow.task_description,
            workflow=self.workflow.workflow,
            toolbox=self.workflow.toolbox,
            current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            history_conversation=self.conv.to_str(),
        )
        return prompt

    def _process(self, prompt:str=None) -> Tuple[str, BotOutput]:
        llm_response = self.llm.query_one(prompt)
        prediction = self.parse_react_output(llm_response)
        return llm_response, prediction
    
    @staticmethod
    def parse_react_output(s: str) -> BotOutput:
        if "```" in s:
            s = Formater.parse_codeblock(s, type="").strip()
        pattern = r"(?P<field>Thought|Action|Action Input|Response):\s*(?P<value>.*?)(?=\n(Thought|Action|Action Input|Response):|\Z)"
        matches = re.finditer(pattern, s, re.DOTALL)
        result = {match.group('field'): match.group('value').strip() for match in matches}
        
        # validate result
        # assert BotOutput.thought_str in result, f"Thought not in prediction! LLM output:\n" + LogUtils.format_infos_basic(s)
        thought = result.get(BotOutput.thought_str, "")
        if BotOutput.action_str in result:        # Action
            assert BotOutput.action_input_str in result, f"Action Input not in prediction! LLM output:\n" + LogUtils.format_infos_basic(s)
            try: # NOTE: ensure the input is in json format! 
                result[BotOutput.action_input_str] = json.loads(result[BotOutput.action_input_str]) # eval: NameError: name 'null' is not defined
            except Exception as e:
                raise RuntimeError(f"Action Input not in json format! LLM output:\n" + LogUtils.format_infos_basic(s))
            if result[BotOutput.action_str].startswith("API_"):
                result[BotOutput.action_str] = result[BotOutput.action_str][4:]
            output = BotOutput(action=result[BotOutput.action_str], action_input=result[BotOutput.action_input_str], thought=thought)
        else:
            assert BotOutput.response_str in result, f"Response not in prediction! LLM output:\n" + LogUtils.format_infos_basic(s)
            output = BotOutput(response=result[BotOutput.response_str], thought=thought)
        return output


class PDLBot(ReactBot):
    """ 
    prediction format: 
        (Thought, Response) for response node
        (Thought, Action, Action Input) for call api node
    """
    llm: OpenAIClient = None
    bot_template_fn: str = "flowagent/bot_pdl.jinja"
    names = ["PDLBot", "pdl_bot"]
    
    def _gen_prompt(self) -> str:
        # valid_apis = self.workflow.pdl.get_valid_apis()
        # valid_apis_str = "There are no valid apis now!" if not valid_apis else f"you can call {valid_apis}"
        state_infos = {
            "Current time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            # "Current state": self.workflow.pdl.current_state,
            # "Current valid apis": valid_apis_str,
        }
        prompt = jinja_render(
            self.bot_template_fn,       # "flowagent/bot_pdl.jinja"
            api_infos=self.workflow.toolbox,
            PDL=self.workflow.pdl.to_str_wo_api(),  # .to_str()
            conversation=self.conv.to_str(), 
            current_state="\n".join(f"{k}: {v}" for k,v in state_infos.items()),
        )
        return prompt
    
    def _process(self, prompt:str=None) -> Tuple[str, BotOutput]:
        llm_response = self.llm.query_one(prompt)
        # transform json -> react format? 
        prediction = self.parse_react_output(llm_response)
        return llm_response, prediction
    
    # @staticmethod
    # def parse_json_output(s: str) -> BotOutput:
    #     parsed_response = Formater.parse_llm_output_json(s)
    #     assert "action_type" in parsed_response, f"parsed_response: {parsed_response}"
    #     action_type = ActionType[parsed_response["action_type"]]
    #     action_metas = APICalling_Info(name=action_name, kwargs=action_parameters)
    