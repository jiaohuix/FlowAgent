""" updated @240906
InputUser: interact manually
LLMSimulatedUserWithProfile
"""
import re, random
from typing import List, Tuple
from .base import BaseUser
from ..data import UserOutput, UserProfile, OOWIntention, Role, Message, LogUtils, init_client, LLM_CFG
from utils.jinja_templates import jinja_render
from utils.wrappers import retry_wrapper
from easonsi.llm.openai_client import OpenAIClient, Formater


class DummyUser(BaseUser):
    names: List[str] = ["dummy_user"]
    user_template_fn: str = ""
    
    def __init__(self, **args) -> None:
        super().__init__(**args)
        
    def process(self, *args, **kwargs) -> UserOutput:
        """ 
        1. generate user query (free style?)
        """
        self.conv.add_message(
            Message(role=Role.USER, content="user query...", conversation_id=self.conv.conversation_id, utterance_id=self.conv.current_utterance_id),
        )
        return UserOutput()


class InputUser(BaseUser):
    names = ["manual", "input_user", "InputUser"]
    user_template_fn: str = ""
    
    def process(self, *args, **kwargs) -> UserOutput:
        user_input = ""
        while not user_input.strip():
            user_input = LogUtils.format_user_input("[USER] ")
        self.conv.add_message(
            Message(Role.USER, user_input, conversation_id=self.conv.conversation_id, utterance_id=self.conv.current_utterance_id)
        )
        return UserOutput(response_content=user_input.strip())


class LLMSimulatedUserWithProfile(BaseUser):
    user_profile: UserProfile = None
    names = ["llm_profile", "LLMSimulatedUserWithProfile"]
    user_template_fn: str = "flowagent/user_llm.jinja"
    
    def __init__(self, **args) -> None:
        super().__init__(**args)
        self.llm = init_client(llm_cfg=LLM_CFG[self.cfg.user_llm_name])
        assert self.cfg.user_profile_id is not None, "cfg.user_profile or cfg.user_profile_id is None!"
        self.user_profile = self.workflow.user_profiles[self.cfg.user_profile_id]

    def process(self, *args, **kwargs) -> UserOutput:
        """ mian process logic.
        gen prompt -> query & process -> gen message
        """
        prompt = self._gen_prompt()
        @retry_wrapper(retry=self.cfg.user_retry_limit, step_name="user_process", log_fn=print)
        def process_with_retry(prompt):
            llm_response, prediction = self._process(prompt)
            return llm_response, prediction
        llm_response, prediction = process_with_retry(prompt)
        msg = Message(
            Role.USER, prediction.response_content, prompt=prompt, llm_response=llm_response,
            conversation_id=self.conv.conversation_id, utterance_id=self.conv.current_utterance_id
        )
        self.conv.add_message(msg)
        self.cnt_user_queries += 1  # stat
        return prediction

    def _gen_prompt(self) -> str:
        prompt = jinja_render(
            self.user_template_fn,  # "flowagent/user_llm.jinja": assistant_description, user_profile, history_conversation
            assistant_description=self.workflow.task_description,
            user_profile=self.user_profile.to_str(),
            history_conversation=self.conv.to_str()
        )
        return prompt
    
    def _process(self, prompt:str=None) -> Tuple[str, UserOutput]:
        llm_response = self.llm.query_one(prompt)
        prediction = self.parse_user_output(llm_response)
        return llm_response, prediction

    @staticmethod
    def parse_user_output(s: str) -> UserOutput:
        if "```" in s:
            s = Formater.parse_codeblock(s, type="").strip()
        pattern = r"(Response):\s*(.*?)(?=\n\w+:|\Z)"
        matches = re.findall(pattern, s, re.DOTALL)
        if not matches:
            response = s
        else:
            result = {key: value.strip() for key, value in matches}
            assert UserOutput.response_str in result, f"Response not in prediction: {s}"
            response = result[UserOutput.response_str]
        return UserOutput(response_content=response)


class LLMSimulatedUserWithOOW(LLMSimulatedUserWithProfile):
    names = ["llm_oow", "LLMSimulatedUserWithOOW"]
    user_template_fn: str = "flowagent/user_llm_oow.jinja"
    
    def _gen_prompt(self, oow_intention: OOWIntention=None) -> str:
        profile_dict = self.user_profile.profile
        profile_dict["additional_constraints"] = oow_intention.to_str() if oow_intention else ""
        prompt = jinja_render(
            self.user_template_fn,  # "flowagent/user_llm.jinja": assistant_description, user_profile, history_conversation
            assistant_description=self.workflow.task_description,
            user_profile=self.user_profile.to_str(profile=profile_dict),
            history_conversation=self.conv.to_str()
        )
        return prompt
    
    def process(self, *args, **kwargs) -> UserOutput:
        """ mian process logic.
        [random] -> gen prompt -> query & process -> gen message
        """
        # 1. random select a oow
        if_oow = random.random() < self.cfg.user_oow_ratio
        if if_oow:
            oow_intention = self.workflow.user_oow_intentions[self.cfg.user_profile_id % len(self.workflow.user_oow_intentions)]
            # print(f"  >> using oow: {oow_intention.name}")
        else: oow_intention = None
        # 2. prompting & processing
        prompt = self._gen_prompt(oow_intention)
        @retry_wrapper(retry=self.cfg.user_retry_limit, step_name="user_process", log_fn=print)
        def process_with_retry(prompt):
            llm_response, prediction = self._process(prompt)
            return llm_response, prediction
        llm_response, prediction = process_with_retry(prompt)
        # 3. note to add type! 
        msg = Message(
            Role.USER, prediction.response_content, prompt=prompt, llm_response=llm_response,
            conversation_id=self.conv.conversation_id, utterance_id=self.conv.current_utterance_id,
            type="" if not if_oow else oow_intention.name   # TODO the detailed OOW type? 
        )
        self.conv.add_message(msg)
        self.cnt_user_queries += 1  # stat
        return prediction



