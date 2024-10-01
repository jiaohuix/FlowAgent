from ..data import Config, Workflow, DataManager, DBManager
from typing import List, Dict, Optional, Tuple, Union, Callable


class EvalUtils:
    @staticmethod
    def _get_configs_per_workflow(cfg:Config, simulate_num_persona:int=None):
        """ collect simulation for a specific workflow
        """
        # 1. get all user ids
        num_user_profile = Workflow(cfg).num_user_profile
        if simulate_num_persona is not None and simulate_num_persona > 0:
            num_user_profile = min(num_user_profile, simulate_num_persona)
        # 2. get all the configs
        tasks = []
        for uid in range(num_user_profile):
            cfg_new = cfg.copy()
            cfg_new.user_profile_id = uid
            tasks.append((cfg_new))
        return tasks
    
    @staticmethod
    def get_configs_all_workflows(cfg:Config, simulate_num_persona:int=None, workflow_ids: List[str]=None):
        """ collect simulation for all workflows
        """
        # 1. get all workflow_ids
        if workflow_ids is None:
            num_workflow = DataManager(cfg).num_workflows
            workflow_ids = [f"{i:03d}" for i in range(num_workflow)]
        # 2. get all the configs
        tasks = []
        for workflow_id in workflow_ids:
            cfg_new = cfg.copy()
            cfg_new.workflow_id = workflow_id
            tasks.extend(EvalUtils._get_configs_per_workflow(cfg_new, simulate_num_persona=simulate_num_persona))
        return tasks
    
    @staticmethod
    def get_evaluation_configs(cfg:Config, db:DBManager=None):
        """filter the experiments by `exp_version`
        """
        if db is None: db = DBManager(cfg.db_uri, cfg.db_name, cfg.db_message_collection_name)
        
        # 1. find all run experiments
        run_exps = db.query_run_experiments({ "exp_version": cfg.exp_version }, limit=0)
        
        # 2. get all evaluation configs
        tasks = []
        for exp in run_exps:
            # 2.1 restore the exp config
            cfg_exp = Config.from_dict(
                db.query_config_by_conversation_id(exp["conversation_id"])
            )
            # 2.2 check if the configs of run exps match the input config. partly done by the "reloading" mechanism?
            keys_to_check = ["exp_version", "workflow_dataset", "workflow_type"]
            assert all([cfg_exp[k] == cfg[k] for k in keys_to_check]), f"Config mismatch: {cfg_exp} vs {cfg}"
            # 2.3 ensure the judge config slots: `judge_conversation_id, judge_model_name`
            cfg_exp.judge_model_name = cfg.judge_model_name
            cfg_exp.judge_conversation_id = exp["conversation_id"]
            tasks.append(cfg_exp)
        return tasks