""" Metrics updated @240919
from AgentRE
"""

import re
from typing import List, Set, Tuple, Union


class MetricBase:
    def __init__(self):
        raise NotImplementedError()
    
    def update(self, y_truth, y_pred):
        raise NotImplementedError()
    
    def get_metric(self):
        raise NotImplementedError()
    
    def get_last(self):
        raise NotImplementedError()


class MetricAcc(MetricBase):
    def __init__(self):
        self.scores = []
    
    def update(self, y_truth: str, y_pred: str):
        if y_truth == y_pred:
            self.scores.append(1)
        else:
            self.scores.append(0)
    
    def get_metric(self):
        if len(self.scores) == 0:
            return 0
        else:
            return sum(self.scores) / len(self.scores)
    
    def get_last(self):
        return self.scores[-1]


class MetricF1(MetricBase):
    def __init__(self):
        self.sum_TP = 0
        self.sum_FN = 0
        self.sum_FP = 0
        self.last_TP = None
        self.last_FN = None
        self.last_FP = None
    
    def update(self, y_truth: Union[list, set], y_pred: Union[list, set]):
        # TP: 在truth中存在，且在pred中存在
        # FN: 在truth中存在，但在pred中不存在
        # FP: 在truth中不存在，但在pred中存在
        assert isinstance(y_truth, (list, set)), "y_truth must be a list or set"
        assert isinstance(y_pred, (list, set)), "y_pred must be a list or set"
        y_truth, y_pred = set(y_truth), set(y_pred)
        
        self.last_TP = len(y_truth & y_pred)
        self.last_FN = len(y_truth - y_pred)
        self.last_FP = len(y_pred - y_truth)
        self.sum_TP += self.last_TP
        self.sum_FN += self.last_FN
        self.sum_FP += self.last_FP
    
    def get_metric(self):
        # TP + FN 可能为0
        # TP + FP 可能为0
        TP = self.sum_TP
        FN = self.sum_FN
        FP = self.sum_FP
        if TP + FN == 0:
            recall = 0
        else:
            recall = TP / (TP + FN)
        if TP + FP == 0:
            precision = 0
        else:
            precision = TP / (TP + FP)
        if recall + precision == 0:
            f1 = 0
        else:
            f1 = 2 * recall * precision / (recall + precision)
        self.recall = recall
        self.precision = precision
        return f1
    
    def get_detail(self):
        if not hasattr(self, 'recall'):
            f1 = self.get_metric()
        return f1, self.recall, self.precision
    
    def get_last(self):
        return self.last_TP, self.last_FN, self.last_FP


if __name__ == '__main__':
    metric = MetricF1()
    metric.update({1, 2, 3}, {2, 3, 4})
    f1, recall, precision = metric.get_detail()
    print(f"f1: {f1:.4f}, recall: {recall:.4f}, precision: {precision:.4f}")
    
    metric = MetricAcc()
    metric.update('1', '1')
    acc = metric.get_metric()
    print(f"acc: {acc:.4f}")
