import datetime, os, re, yaml, copy, pathlib, time
from enum import Enum, auto
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple, Union


class BotOutputType(Enum):
    RESPONSE = ("RESPONSE", "response to the user")
    ACTION = ("ACTION", "call an API")

    def __init__(self, actionname, description):
        self.actionname = actionname
        self.description = description


@dataclass
class UserOutput:
    response_content: str = None
    
    response_str = "Response"
    end_flag = "[END]"
    
    @property
    def is_end(self) -> bool:
        return self.end_flag in self.response_content

@dataclass
class BotOutput:
    thought: str = None
    action: str = None                      # api name
    action_input: Union[str, Dict] = None   # api paras
    response: str = None
    
    thought_str = "Thought"
    action_str = "Action"
    action_input_str = "Action Input"
    response_str = "Response"
    
    @property
    def action_type(self) -> BotOutputType:
        if self.action is not None:
            return BotOutputType.ACTION
        else:
            assert self.response is not None, "both action and response are None!"
            return BotOutputType.RESPONSE

@dataclass
class APIOutput:
    name: str = None
    request: Union[str, Dict] = None
    response_status_code: bool = None
    response_data: Union[str, Dict] = None
    
    response_status_str = "status_code"
    response_data_str = "data"
    
    response_status_str_react = "Status Code"
    response_data_str_react = "Data"