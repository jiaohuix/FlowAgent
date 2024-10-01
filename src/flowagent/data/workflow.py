""" updated @240906
WorkflowType: text, code, flowchart, pdl
    with different subdirs and suffixes!
"""
import yaml, json, os
from dataclasses import dataclass, asdict, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Dict, Optional, Union
from .user_profile import UserProfile, OOWIntention
from .config import Config
from .pdl import PDL
from .base_data import ConversationWithIntention, Conversation


@dataclass
class DataManager:
    cfg: Config = None
    
    DIR_root = Path(__file__).resolve().parent.parent.parent.parent
    DIR_src_base = (DIR_root / "src")
    
    DIR_config = DIR_root / "src/flowagent/configs"
    
    DIR_data_root = DIR_root / "dataset"
    
    DIR_data_workflow = None               # subdir for specific dataset
    FN_data_workflow_infos = None
    
    data_version: str = None
    workflow_infos: dict = field(default_factory=dict)
    
    def __init__(self, cfg:Config) -> None:
        self.cfg = cfg
        self._build_workflow_infos(cfg.workflow_dataset)
        
    def _build_workflow_infos(self, workflow_dataset: str):
        self.DIR_data_workflow = self.DIR_data_root / workflow_dataset
        self.FN_data_workflow_infos = self.DIR_data_workflow / "task_infos.json"
        infos: dict = json.load(open(self.FN_data_workflow_infos, 'r'))
        self.data_version = infos['version']
        self.workflow_infos = infos['task_infos']
    
    def refresh_config(self, cfg: Config) -> None:
        self.cfg = cfg
        self._build_workflow_infos(cfg.workflow_dataset)

    @staticmethod
    def normalize_config_name(config_name:str):
        config_fn = DataManager.DIR_config / config_name
        return config_fn

    @property
    def num_workflows(self):
        return len(self.workflow_infos)
    
    def get_workflow_dataset_names(self):
        # return folder name in self.DIR_data_root
        all_entries = os.listdir(self.DIR_data_root)
        names = [entry for entry in all_entries if os.path.isdir(os.path.join(self.DIR_data_root, entry))]
        return names


class WorkflowType(Enum):
    TEXT = ("TEXT", "format for natural language", ".txt", 'text')
    CODE = ("CODE", "format of code", ".py", 'code')
    FLOWCHART = ("FLOWCHART", "format of flowchart", ".md", 'flowchart')
    PDL = ("PDL", "format of PDL", ".yaml", 'pdl')

    def __init__(self, workflow_type, description, suffix, subdir):
        self.workflow_type: str = workflow_type
        self.description: str = description
        self.suffix: str = suffix
        self.subdir: str = subdir
    
    @property
    def types(self):
        types_upper = list(map(lambda x: x.value[0], WorkflowType))
        types_lower = list(map(lambda x: x.value[0].lower(), WorkflowType))
        return types_upper + types_lower

    def __str__(self):
        return self.workflow_type


class WorkflowTypeStr(str, Enum):
    TEXT = "text"
    CODE = "code"
    FLOWCHART = "flowchart"
    PDL = "pdl"


@dataclass
class Workflow:  # rename -> Data
    type: WorkflowType = None
    id: str = None              # 000
    name: str = None
    task_description: str = None
    task_detailed_description: str = None
    
    workflow: str = None
    toolbox: List[Dict] = field(default_factory=list)   # apis
    pdl: PDL = None         # only for PDL
    
    user_profiles: List[UserProfile] = None
    reference_conversations: List[ConversationWithIntention] = None
    user_oow_intentions: List[OOWIntention] = None
    
    cfg: Config = None
    data_manager: DataManager = None
    

    def __init__(self, cfg:Config, data_manager:DataManager=None) -> None:
        self.cfg = cfg
        if data_manager is None: data_manager = DataManager(cfg)
        self.data_manager = data_manager
        
        self.type = WorkflowType[self.cfg.workflow_type.upper()]
        # 1. load basic info
        self.id = self.cfg.workflow_id
        assert self.id in data_manager.workflow_infos, f"[ERROR] {self.id} not found in {data_manager.workflow_infos.keys()}"
        infos = data_manager.workflow_infos[self.id]
        self.name = infos['name']
        self.task_description = infos['task_description']
        self.task_detailed_description = infos['task_detailed_description']
        # 2. load the workflow & toolbox
        with open(data_manager.DIR_data_workflow / f"tools/{self.id}.yaml", 'r') as f:
            self.toolbox = yaml.safe_load(f)
        with open(data_manager.DIR_data_workflow / f"{self.type.subdir}/{self.id}{self.type.suffix}", 'r') as f:
            self.workflow = f.read().strip()
        if self.type == WorkflowType.PDL:   # sepcial for PDL
            self.pdl = PDL.load_from_file(data_manager.DIR_data_workflow / f"pdl/{self.id}.yaml")
            self.workflow = self.pdl.to_str_wo_api() # self.pdl.procedure
        # 3. load the user infos
        if (self.cfg.exp_mode=="session"): # load_user_profiles:
            with open(data_manager.DIR_data_workflow / f"user_profile/{self.id}.json", 'r') as f:
                user_profiles = json.load(f)
            self.user_profiles = [UserProfile.load_from_dict(profile) for profile in user_profiles]
            # if user in OOW mode! 
            if "oow" in self.cfg.user_mode.lower():
                with open(data_manager.DIR_data_root / f"meta/oow.yaml", 'r') as f:
                    data = yaml.safe_load(f)
                self.user_oow_intentions = [OOWIntention.from_dict(d) for d in data]
        if (self.cfg.exp_mode=="turn"): # load_reference_conversation: 
            with open(data_manager.DIR_data_workflow / f"user_profile_w_conversation/{self.id}.json", 'r') as f:
                data = json.load(f)
            self.reference_conversations = []
            for d in data:
                self.reference_conversations.append(
                    ConversationWithIntention(
                        d["user_intention"], Conversation.load_from_json(d["conversation"])
                    )
                )

    @property
    def num_user_profile(self):
        if self.user_profiles is not None: return len(self.user_profiles)
        if self.reference_conversations is not None: return len(self.reference_conversations)
        raise NotImplementedError
    
    def to_str(self):
        # return f"ID: {self.type}-{self.id}\nName: {self.name}\nTask: {self.task_description}\nWorkflow: {self.workflow}"
        info_dict = {
            "ID": f"{self.type}-{self.id}",
            "Name": self.name,
            "Task": self.task_description,
            "Workflow": self.task_detailed_description # just use natural language-format workflow? 
        }
        return "".join([f"{k}: {v}\n" for k, v in info_dict.items()])

