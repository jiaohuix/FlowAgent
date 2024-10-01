from typing import Dict
from enum import Enum
from .base import BaseRole, BaseAPIHandler, BaseBot, BaseUser
from .api import DummyAPIHandler
from .user import DummyUser, InputUser
from .bot import DummyBot, PDLBot

def build_attr_list_map(base_class: BaseRole, name_to_class_dict: Dict[str, BaseRole], attr: str="names"):
    for cls in base_class.__subclasses__():
        for name in cls.__dict__[attr]:
            name_to_class_dict[name] = cls
        # recursive!
        build_attr_list_map(cls, name_to_class_dict)

USER_NAME2CLASS:Dict[str, BaseUser] = {}
build_attr_list_map(BaseUser, USER_NAME2CLASS)
BOT_NAME2CLASS: Dict[str, BaseBot] = {}
build_attr_list_map(BaseBot, BOT_NAME2CLASS)
API_NAME2CLASS:Dict[str, BaseAPIHandler] = {}
build_attr_list_map(BaseAPIHandler, API_NAME2CLASS)

def build_attr_map(base_class: BaseRole, name_to_class_dict: Dict[str, BaseRole], attr: str="names"):
    for cls in base_class.__subclasses__():
        name_to_class_dict[cls.__dict__[attr]] = cls
        # recursive!
        build_attr_map(cls, name_to_class_dict, attr)
USER_NAME2TEMPLATE:Dict[str, str] = {}
build_attr_map(BaseUser, USER_NAME2TEMPLATE, attr="user_template_fn")
BOT_NAME2TEMPLATE:Dict[str, str] = {}
build_attr_map(BaseBot, BOT_NAME2TEMPLATE, attr="bot_template_fn")
API_NAME2TEMPLATE:Dict[str, str] = {}
build_attr_map(BaseAPIHandler, API_NAME2TEMPLATE, attr="api_template_fn")

# for typer
def create_enum(name, values):
    return Enum(name, {key: key for key in values})
UserMode = create_enum('UserMode', USER_NAME2CLASS.keys())
BotMode = create_enum('BotMode', BOT_NAME2CLASS.keys())
ApiMode = create_enum('ApiMode', API_NAME2CLASS.keys())
