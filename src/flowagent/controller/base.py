""" updated @240919
"""

from abc import abstractmethod
from typing import List
import datetime
import pandas as pd
from ..data import (
    Config, DBManager, DataManager, Workflow, LogUtils,
    Role, Message, Conversation, BaseLogger
)
from ..roles import InputUser, BaseBot, BaseUser, BaseAPIHandler

class BaseController:
    """ main loop of a simulated conversation
    USAGE:
        controller = XXXController(cfg)
        controller.start_conversation()
    """
    cfg: Config = None
    user: BaseUser = None
    bot: BaseBot = None
    api: BaseAPIHandler = None
    logger: BaseLogger = None
    conv: Conversation = None       # global variable for conversation
    data_manager: DataManager = None        # remove it? 
    workflow: Workflow = None
    conversation_id: str = None
    
    # bot_types: List[str] = None    # to build WORKFLOW_TYPE2CONTROLLER
    
    def __init__(self, cfg:Config) -> None:
        self.cfg = cfg
        self.data_manager = DataManager(cfg)
        self.logger = BaseLogger()
        self.conversation_id = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        self.conv = Conversation(conversation_id=self.conversation_id)
    
        if self.cfg.log_to_db:
            self.db = DBManager(self.cfg.db_uri, self.cfg.db_name, self.cfg.db_message_collection_name)
    
    @abstractmethod
    def conversation(self, verbose:bool=True) -> Conversation:
        raise NotImplementedError()
    
    @abstractmethod
    def conversation_teacher_forcing(self, verbose:bool=True) -> Conversation:
        raise NotImplementedError()
    
    def start_conversation(self, verbose=True):
        infos = {
            "conversation_id": self.conversation_id,
            "exp_version": self.cfg.exp_version,
            "config": self.cfg.to_dict(),
        }
        self.logger.log(LogUtils.format_infos_with_tabulate(infos), with_print=verbose)

        # 1. check if has been run!
        if self._check_if_already_run():
            self.logger.log(f"NOTE: the experiment has already been run!", with_print=verbose)
            return infos, None  # the returned results haven't been used
        # 2. run the conversation
        conversation = self.conversation(verbose=verbose)
        # 3. record the conversation
        self._record_to_db(conversation, verbose=verbose)

        conversation_df = pd.DataFrame(conversation.to_list())[['role', 'content']].set_index('role')
        self.logger.log(LogUtils.format_infos_with_tabulate(conversation_df), with_print=verbose)
        return infos, conversation
    
    def start_conversation_teacher_forcing(self, verbose=True):
        infos = {
            "conversation_id": self.conversation_id,
            "exp_version": self.cfg.exp_version,
            "config": self.cfg.to_dict(),
        }
        self.logger.log(LogUtils.format_infos_with_tabulate(infos), with_print=verbose)

        # 1. check if has been run!
        if self._check_if_already_run():
            self.logger.log(f"NOTE: the experiment has already been run!", with_print=verbose)
            return infos, None  # the returned results haven't been used
        # 2. run the conversation
        conversation = self.conversation_teacher_forcing(verbose=verbose)
        # 3. record the conversation
        self._record_to_db(conversation, verbose=verbose)
        
        conversation_df = pd.DataFrame(conversation.to_list())[['role', 'content']].set_index('role')
        self.logger.log(LogUtils.format_infos_with_tabulate(conversation_df), with_print=verbose)
        return infos, conversation
    
    def _check_if_already_run(self) -> bool:
        query = {  # identify a single exp
            "exp_version": self.cfg.exp_version,
            "exp_mode": self.cfg.exp_mode,
            **{ k:v for k,v in self.cfg.to_dict().items() if k.startswith("workflow") },
            "user_profile_id": self.cfg.user_profile_id
        }
        if self.cfg.simulate_force_rerun: 
            res = self.db.delete_run_experiments(query)
            return False
        else:
            query_res = self.db.query_run_experiments(query)
            return len(query_res) > 0
    
    def _record_to_db(self, conversation:Conversation, verbose=True):
        if not self.cfg.log_to_db: return 
        
        # 1. insert conversation
        res = self.db.insert_conversation(conversation)
        self.logger.log(f"  <db> Inserted conversation with {len(res.inserted_ids)} messages", with_print=verbose)
        
        # 2. insert configuration
        infos_dict = {
            "conversation_id": self.conversation_id, "exp_version": self.cfg.exp_version,
            **self.cfg.to_dict()
        }
        res = self.db.insert_config(infos_dict)
        self.logger.log(f"  <db> Inserted config", with_print=verbose)
    
    
    def log_msg(self, msg:Message, verbose=True):
        """ log message to logger and stdout """
        _content = msg.to_str()      # or msg is str?
        self.logger.log(_content, with_print=False)
        if verbose and not (    # for InputUser, no need to print
            isinstance(self.user, InputUser) and (msg.role == Role.USER)
        ): 
            self.logger.log_to_stdout(_content, color=msg.role.color)
