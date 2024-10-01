""" updated @240919
collect the evaluation results from DB, generate a report to WanDB
- [ ] summary exp settings
"""

import collections, wandb
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from ..data import Config, DBManager, LogUtils
from .metric import MetricF1


class Analyzer:
    """ abstraction of evaluation results analysis 
    USAGE:
        analyzer = Analyzer(cfg)
        analyzer.analyze()
    """
    cfg: Config = None
    db: DBManager = None
    
    df: pd.DataFrame = None     # df of evaluation results
    stat_dict: dict = None      # collect key matrices
    
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.db = DBManager(cfg.db_uri, cfg.db_name, cfg.db_message_collection_name)
    
        self._collect_exp_results()
        self.stat_dict = dict()
        if self.cfg.judge_log_to == "wandb":
            wandb.init(project="pdl", name=cfg.exp_version)
    
    def _collect_exp_results(self):
        query_res = self.db.query_evaluations({ "exp_version": self.cfg.exp_version })
        if len(query_res) == 0:
            print(f"  <analyze> No evaluation results found for {self.cfg.exp_version}!!!")
            return 
        df = pd.DataFrame(query_res)
        # check that workflow_dataset & workflow_type are all the same!
        assert df["workflow_dataset"].nunique() == 1 and df["workflow_type"].nunique() == 1, \
            f"workflow_dataset & workflow_type are not the same in {self.cfg.exp_version}"
        self.df = df
    
    def analyze(self) -> dict:
        if self.df is None: return None
        if self.cfg.exp_mode == "session":
            self.stat_judge_session()
            self.stat_judge_session_stat()
            self.stat_num_turns()
        elif self.cfg.exp_mode == "turn":
            self.stat_judge_turn()
            self.stat_judge_turn_stat()
            self.stat_num_turns()
        
        print(LogUtils.format_infos_with_tabulate(self.stat_dict, color="blue"))
        # log to W&B
        if self.cfg.judge_log_to == "wandb":
            for k, v in self.stat_dict.items():
                wandb.summary[k] = v
        return self.stat_dict

    def stat_judge_session(self):
        """ 
        input key: judge_session_result
        metric: Success Rate, Task Progress.  
        """
        df = self.df
        df['if_pass'] = df['judge_session_result'].apply(lambda x: x['Result'].strip() == 'yes')
        df['goals_total'] = df['judge_session_result'].apply(lambda x: int(x['Total number of goals']))
        df['goals_accomplished'] = df['judge_session_result'].apply(lambda x: int(x['Number of accomplished goals']))
        df['task_progress'] = df['goals_accomplished'] / df['goals_total']
        metrics = dict(
            success_rate=df['if_pass'].mean(),
            task_progress=df['task_progress'].mean()
        )
        self.stat_dict |= metrics
        return metrics

    def stat_judge_session_stat(self):
        """ 
        input key: judge_session_stat
        metric: API Precision, Recall, F1
        """
        metric = MetricF1()
        for session_stat in self.df['judge_session_stat']:
            metric.update(y_truth=session_stat['apis_gt'], y_pred=session_stat['apis_pred'])
        f1, recall, precision = metric.get_detail()
        metrics = dict(
            f1=f1, recall=recall, precision=precision
        )
        self.stat_dict |= metrics
        return metrics
        
    def stat_judge_turn(self):
        """ turn-level | overall metric & selected metric
        input key: judge_turn_result
        metric: Response Score
        """
        scores = []         # mean{ mean_score_of_a_session } 
        passes = []         # mean{ pass of turns } 
        oow_scores = []
        oow_passes = []
        for jr_session in self.df["judge_turn_result"]:
            score, oow_score = [], []
            succ, oow_succ = [], []
            for jr in jr_session:
                # jr: {Score, utterance_id, type}
                s = int(jr["Score"])
                score.append(s)
                succ.append(int(s >= 9))
                if jr['type']: 
                    oow_score.append(s)
                    oow_succ.append(int(s >= 9))
            scores.append(np.mean(score))
            passes += succ
            oow_scores.append(np.mean(oow_score))
            oow_passes += oow_succ
        metrics = dict(
            mean_score=np.mean(scores),
            passrate=np.mean(passes),
            oow_mean_score=np.mean(oow_scores),
            oow_passrate=np.mean(oow_passes)
        )
        self.stat_dict |= metrics
        return metrics
    
    def stat_judge_turn_stat(self):
        """ 
        input key: judge_turn_stat
        metric: API Precision, Recall, F1 / Parameter Precision, Recall, F1
        """
        api_metric = MetricF1()
        params_metric = MetricF1()
        for jr in self.df["judge_turn_stat"]:
            for api_gt, api_pred in zip(jr["apis_gt"], jr["apis_pred"]):
                api_gt_names, api_pred_names = set(), set()
                params_gt, params_pred = set(), set()
                if api_gt: 
                    api_gt_names.add(api_gt[0])
                    params_gt = set([str(i) for i in api_gt[1].values()])
                if api_pred: 
                    api_pred_names.add(api_pred[0])
                    params_pred = set([str(i) for i in api_pred[1].values()])
                api_metric.update(y_truth=api_gt_names, y_pred=api_pred_names)
                params_metric.update(y_truth=params_gt, y_pred=params_pred)
        f1, recall, precision = api_metric.get_detail()
        para_f1, para_recall, para_precision = params_metric.get_detail()
        metrics = dict(
            f1=f1, recall=recall, precision=precision,
            para_f1=para_f1, para_recall=para_recall, para_precision=para_precision
        )
        self.stat_dict |= metrics
        return metrics

    def stat_num_turns(self):
        avg_conv_turns = self.df["num_turns"].mean()
        self.stat_dict["avg_num_turns"] = avg_conv_turns
        
        vc_num_turns = self.df["num_turns"].value_counts().sort_index().reset_index()
        plt.figure(figsize=(10, 6))
        # plt.bar(vc_num_turns['num_turns'].values, vc_num_turns['count'].values, color='blue')
        sns.barplot(x='num_turns', y='count', data=vc_num_turns, palette='Blues_d', hue='num_turns', legend=False)
        plt.title('Number of turns Distribution')
        plt.xlabel('Number of turns')
        plt.ylabel('Count')
        if self.cfg.judge_log_to == "wandb":
            wandb.log({"dist_num_turns": wandb.Image(plt)})
        return vc_num_turns
    
    def stat_scores_overall(self):
        self.stat_dict["mean_score"] = self.df["overall_score"].mean()
        # stat_dict["passrate"] = sum(self.df["overall_score"] >= th) / len(self.df)
        
        df_scores = self.df['overall_score'].value_counts().sort_index().reset_index()

        data = []
        for score, count in df_scores.values:
            data.append([score, count, 'GPT'])
        df_scores_dist = pd.DataFrame(data, columns=['Score', 'Count', 'Source'])
        plt.figure(figsize=(10, 6))
        sns.barplot(x='Score', y='Count', hue='Source', data=df_scores_dist)
        plt.title('Comparison of Scores between GPT and Human')
        plt.xticks(rotation=0)
        plt.tight_layout()
        if self.cfg.judge_log_to == "wandb":
            wandb.log({"dist_scores_overall": wandb.Image(plt)})
        return df_scores
