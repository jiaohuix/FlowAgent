""" Main entrypoint for evaluation! run simulations, judge, and analyze
updated @240926

- [ ] add stat of #error_output (for parse)
- [x] turn-level evaluation
- [x] update analyzer: more metrics
"""

import os, json, tqdm, itertools, pickle, collections, traceback, datetime, argparse
from typing import List, Dict, Optional, Tuple, Union, Callable
import pandas as pd
import concurrent.futures

from ..data import Config, DataManager, DBManager, LogUtils, Workflow
from .analyzer import Analyzer
from ..controller import FlowagentController
from .judger import Judger
from .eval_utils import EvalUtils


def task_simulate(cfg: Config) -> None:
    """ One simulation task
    """
    controller = FlowagentController(cfg)
    controller.start_conversation(verbose=False)
    
def task_simulate_teacher_forcing(cfg: Config) -> None:
    """ One simulation task | turn-level
    """
    controller = FlowagentController(cfg)
    controller.start_conversation_teacher_forcing(verbose=False)


def task_judge(cfg: Config) -> None:
    """ One evaluation task
    return: True if pass
    """
    judger = Judger(cfg)
    judger.start_judge(verbose=False, mode="session")

def task_judge_turn_level(cfg: Config) -> None:
    """ One evaluation task
    return: True if pass
    """
    judger = Judger(cfg)
    judger.start_judge(verbose=False, mode="turn")


class Evaluator: # rename -> Exp?
    """ abstraction of whole evaluation process
    USAGE:
        evaluator = Evaluator(cfg)
        evaluator.main()
    """
    cfg: Config = None
    data_namager: DataManager = None
    db: DBManager = None
    
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.data_namager = DataManager(cfg)
        self.db = DBManager(cfg.db_uri, cfg.db_name, cfg.db_message_collection_name)
        
    def main(self):
        """ 
        0. set configs. log the configs by `exp_version`
        1. run simulations, use `XXXController(cfg).start_conversation()` to start a single exp with specific config
            output to db with `exp_version` (clean if exist)
        2. run evaluations/judges (query db to find run exps)
        3. analyze the evaluation results
        """
        self.process_configs()
        
        if self.cfg.exp_mode == "session":
            self.print_header_info(step_name="STEP 1: Simulating", infos={k:v for k,v in self.cfg.to_dict().items() if k.startswith("simulate") or k.startswith("exp")})
            self.run_simulations(f_task=task_simulate)
            self.print_header_info(step_name="STEP 2: Evaluating", infos={k:v for k,v in self.cfg.to_dict().items() if k.startswith("judge")})
            self.run_evaluations(f_task=task_judge)
            self.print_header_info(step_name="STEP 3: Analyzing")
            self.analyze()
        elif self.cfg.exp_mode == "turn":
            self.print_header_info(step_name="STEP 1: Simulating", infos={k:v for k,v in self.cfg.to_dict().items() if k.startswith("simulate") or k.startswith("exp")})
            self.run_simulations(f_task=task_simulate_teacher_forcing)
            self.print_header_info(step_name="STEP 2: Evaluating", infos={k:v for k,v in self.cfg.to_dict().items() if k.startswith("judge")})
            self.run_evaluations(f_task=task_judge_turn_level)
            self.print_header_info(step_name="STEP 3: Analyzing")
            self.analyze()
        else:
            raise NotImplementedError(f"Unknown exp_mode: {self.cfg.exp_mode}")
    
    def process_configs(self):
        """ Log the config. If existed, reload it! """
        cfn_fn = self.data_namager.DIR_config / f"exps/{self.cfg.exp_version}.yaml"
        os.makedirs(cfn_fn.parent, exist_ok=True)
        if os.path.exists(cfn_fn):
            print(f"EXP {self.cfg.exp_version} config existed! Loading from {cfn_fn}")
            self.cfg = Config.from_yaml(cfn_fn)     # NOTE: reload the config!
        else:
            if self.cfg.exp_save_config: # save the config
                self.cfg.to_yaml(cfn_fn)
                print(f"EXP {self.cfg.exp_version} config saved to {cfn_fn}")

    @staticmethod
    def print_header_info(step_name: str, infos: Union[None, Dict, pd.DataFrame]=None):
        """ Formatted header info """
        step_name = f" {step_name.strip()} "
        s_print = step_name.center(150, "=") + "\n"
        if infos is not None:
            s_print += LogUtils.format_infos_with_tabulate(infos)
        print(s_print)

    def run_simulations(self, f_task: Callable):
        """ 
        1. get all the simulation configs
        2. run simulations in parallel
        """
        def f_exec(cfg, f_task=f_task):
            # 1. check if run (query db) -- DONE in `XXXController.start_conversation`
            # 2. run with retry (3 times) NOTE: can be a decorator? @retry_wrapper
            for retry_ in range(3):
                try:
                    return f_task(cfg)
                except Exception as e:
                    print(f"Task failed for {cfg}: {e}")
                    traceback.print_exc()
            else:
                print(f"ERROR!!! Task failed after 3 retrys for {cfg}")
                return None

        tasks = EvalUtils.get_configs_all_workflows(self.cfg, simulate_num_persona=self.cfg.simulate_num_persona)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.cfg.simulate_max_workers) as executor:
            futures = []
            for cfg in tasks:
                future = executor.submit(f_exec, cfg, f_task=f_task)
                futures.append(future)
            print(f"Running {len(futures)} tasks...")
            for future in tqdm.tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Executing tasks"):
                future.result()


    def run_evaluations(self, f_task: Callable):
        """ evaluation process:
        1. get the experiments to be evaluated
        2. run evaluations in parallel
        """
        def f_exec(cfg, f_task=f_task):
            for retry_ in range(3):
                try:
                    return f_task(cfg)
                except Exception as e:
                    print(f"Task failed for {cfg}: {e}")
                    traceback.print_exc()
            else:
                print(f"ERROR!!! Task failed after 3 retrys for {cfg}")
                return None
        
        tasks = EvalUtils.get_evaluation_configs(self.cfg, db=self.db)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.cfg.judge_max_workers) as executor:
            futures = []
            for cfg in tasks:
                future = executor.submit(f_exec, cfg, f_task=f_task)
                futures.append(future)
            print(f"Executing {len(futures)} judge tasks...")
            # num_errors = 0
            for future in tqdm.tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Executing tasks"):
                future.result() 
            #     if r: num_errors += 1
            # print(f"# of errors: {num_errors}")
        # if num_errors > 0:
        #     raise Exception(f"# of errors when evaluation: {num_errors}")

    def analyze(self):
        """ analysis process: -> to `Analyzer`
        """
        analyzer = Analyzer(self.cfg)
        analyzer.analyze()
