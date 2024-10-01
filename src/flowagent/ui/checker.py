""" CLI data checker
updated @240920

"""

import json
from enum import Enum, auto
from dataclasses import dataclass, asdict, field
import pandas as pd
from ..data import DBManager, Config, DataManager, LogUtils





class CmdType(Enum):
    EXP = ("EXP", "show run experiment infos by `exp_version`")
    CONV = ("CONV", "show single conversation by `conversation_id`")
    UTTER = ("UTTER", "show single utterance by `utterance_id`")
    HELP = ("HELP", "show detailed command infos")
    EXIT = ("EXIT", "quit")

    def __init__(self, cmdname, description):
        self.cmdname = cmdname
        self.description = description
    
    @classmethod
    def get_cmd_infos(cls):
        infos = []
        for idx, cmd in enumerate(cls):
            infos.append(f"{idx} ({cmd.cmdname})")
        return ", ".join(infos)
    
    @classmethod
    def get_cmd_detailed_infos(cls):
        infos = []
        for idx, cmd in enumerate(cls):
            infos.append(f"{idx}. {cmd.cmdname}: {cmd.description}")
        info_str = "\n".join(infos)
        return info_str

    @classmethod
    def from_index(cls, index):
        try:
            return list(cls)[index]
        except IndexError:
            raise ValueError(f"Invalid index {index}. Valid indices are 0 to {len(cls) - 1}.")


class CLIChecker():
    selected_exp_version: str = None
    run_exps_df: pd.DataFrame = None    # run exp infos
    
    selected_conversation_id: str = None
    conv_cfg: Config = None             # selected conversation
    conv_df: pd.DataFrame = None        # selected conversation
    
    data_manager: DataManager = None    # NOTE: DataManager <- workflow_dataset
    db: DBManager = None

    def __init__(self, cfg: Config = None) -> None:
        if cfg is None:
            cfg = Config.from_yaml(DataManager.normalize_config_name("default.yaml"))
        self.db = DBManager(cfg.db_uri, cfg.db_name, cfg.db_message_collection_name)
        self.data_manager = DataManager(cfg)

    def query_run_experiments(self, exp_version: str, **customized_query):
        # STEP 1: select `exp_version`, show run exps infos
        self.selected_exp_version = exp_version
        query = {
            'exp_version': exp_version,
        }
        if customized_query: query.update(customized_query)
        run_experiments = self.db.query_run_experiments(query)
        self.run_exps_df = pd.DataFrame(run_experiments).drop(columns=['_id']).set_index('conversation_id')
        _selected_cols = ['workflow_dataset', 'workflow_type', 'workflow_id', 'user_profile_id']
        select_df = self.run_exps_df[_selected_cols]
        print(LogUtils.format_infos_with_tabulate(select_df))

    def show_conversation(self, conversation_id: str):
        # STEP 2: select `conversation_id`, show conversation
        # 1. collect the conversation infos
        self.selected_conversation_id = conversation_id
        self.conv_cfg = Config.from_dict(self.db.query_config_by_conversation_id(conversation_id))
        self.conv_df = self.db.query_messages_by_conversation_id(conversation_id).to_dataframe()
        self.data_manager.refresh_config(self.conv_cfg)
        # 2. show the conversation
        _selected_columns = ['role', 'content', 'utterance_id']
        df_selected = self.conv_df[_selected_columns].set_index('utterance_id')
        print(LogUtils.format_infos_with_tabulate(df_selected))
        # 3. show the related user profile
        with open(self.data_manager.DIR_data_workflow / f"user_profile/{self.conv_cfg.workflow_id}.json", 'r') as f:
            user_profiles = json.load(f)
            selected_up = user_profiles[self.conv_cfg.user_profile_id]
            print(LogUtils.format_infos_basic(selected_up))
            

    def show_utterance(self, utterance_id: int):
        # STEP3: select `utterance_id`, show utterance
        selected_row = self.conv_df[self.conv_df['utterance_id'] == utterance_id].iloc[0].to_dict()
        print(LogUtils.format_infos_with_pprint(selected_row))
        
    def select_cmd(self) -> CmdType:
        print(LogUtils.format_str_with_color("> Available commands: " + CmdType.get_cmd_infos(), 'gray'))
        prompt = f"Select your command: "
        cmd_idx = LogUtils.format_user_input(prompt)
        cmd = CmdType.from_index(int(cmd_idx))
        return cmd
    
    def main(self):
        info_str = "=== USAGE ===\n" + CmdType.get_cmd_detailed_infos()
        print(info_str)
        while True:
            cmd = self.select_cmd()
            if cmd == CmdType.EXP:
                candidate_exp_versions = self.db.get_all_run_exp_versions()
                print(LogUtils.format_str_with_color("> Candidate exp versions: " + ", ".join(candidate_exp_versions), 'gray'))
                exp_version = LogUtils.format_user_input("Enter exp_version: ")
                self.query_run_experiments(exp_version)
            elif cmd == CmdType.CONV:
                candidate_conversation_ids = self.run_exps_df.index
                print(LogUtils.format_str_with_color("> Candidate conversation ids: " + ", ".join(candidate_conversation_ids), 'gray'))
                conversation_id = LogUtils.format_user_input("Enter conversation_id to view details: ")
                self.show_conversation(conversation_id)
            elif cmd == CmdType.UTTER:
                candidate_utterance_ids = self.conv_df['utterance_id'].to_list()
                candidate_utterance_ids.sort()
                candidate_utterance_ids = [str(i) for i in candidate_utterance_ids]
                print(LogUtils.format_str_with_color("> Candidate utterance ids: " + ", ".join(candidate_utterance_ids), 'gray'))
                utterance_id = LogUtils.format_user_input("Enter utterance_id to view details: ")
                utterance_id = int(utterance_id)
                self.show_utterance(utterance_id)
            elif cmd == CmdType.EXIT:
                break
