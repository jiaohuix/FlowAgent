""" updated @240906 
"""
import jinja2
import yaml, copy, os
from dataclasses import dataclass, asdict, field

@dataclass
class Config:
    workflow_dataset: str = "STAR"
    workflow_type: str = "text"     # text, code, flowchart
    workflow_id: str = "000"
    exp_version: str = "default"
    exp_mode: str = "session"       # turn, session
    exp_save_config: bool = False
    
    user_mode: str = "llm_profile"  # llm_oow, manual, llm_profile
    user_llm_name: str = "gpt-4o"
    user_template_fn: str = None    # "flowagent/user_llm.jinja"
    # user_profile: bool = True # controlled by exp_mode
    user_profile_id: int = 0
    user_retry_limit: int = 3
    user_oow_ratio: float = 0.1
    
    bot_mode: str = "react_bot"
    bot_template_fn: str = None     # "flowagent/bot_flowbench.jinja"
    bot_llm_name: str = "gpt-4o"
    bot_action_limit: int = 5
    bot_retry_limit: int = 3
    pdl_check_dependency: bool = True
    pdl_check_api_dup_calls: bool = True
    pdl_check_api_dup_calls_threshold: int = 2
    
    api_mode: str = "llm"
    api_template_fn: str = None     # "flowagent/api_llm.jinja"
    api_llm_name: str = "gpt-4o"

    conversation_turn_limit: int = 20
    log_utterence_time: bool = True
    log_to_db: bool = True

    db_uri: str = 'mongodb://localhost:27017/'
    db_name: str = "pdl"
    db_message_collection_name: str = "messages"
    db_meta_collection_name: str = "config"
    
    simulate_num_persona: int = -1
    simulate_max_workers: int = 10
    simulate_force_rerun: bool = False
    
    judge_max_workers: int = 10
    judge_model_name: str = "gpt-4o"
    judge_conversation_id: str = None   # the conversation to be judged
    # judge_passrate_threshold: int = 3
    judge_log_to: str = "wandb"
    judge_force_rejudge: bool = False
    judge_retry_limit: int = 3

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_yaml(cls, yaml_file: str):
        with open(yaml_file, 'r') as file:
            # replace ${} with os.environ, with jinja2
            context = file.read()
            content = jinja2.Template(context).render(os.environ)
            data = yaml.safe_load(content)
        obj = cls(**data)
        return obj
    
    def to_yaml(self, yaml_file: str):
        with open(yaml_file, 'w') as file:
            yaml.dump(asdict(self), file, sort_keys=False)
    
    @classmethod
    def from_dict(cls, dic: dict):
        # ignore unknown fields
        obj = cls(**{ k:v for k,v in dic.items() if k in cls.__dataclass_fields__ })
        return obj
    
    def copy(self):
        return copy.deepcopy(self)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(f"Key '{key}' not found in Config")

if __name__ == '__main__':
    config_dict = {
        "workflow_dataset": "xxx",
        "workflow_type": "xxx",
        "workflow_id": "000",
        "xxx": "xxx"
    }
    cfg = Config.from_dict(config_dict)
    print(cfg)