import abc
from typing import Tuple
from ..data import PDL, Conversation, Role, Message, Config, BotOutput
from .pdl_utils import PDLNode, PDLGraph


class BaseChecker:
    """ abstraction class for action checkers 
    USAGE:
        checker = XXXChecker(cfg, conv)
        res = checker.check(bot_output)
    """
    cfg: Config = None
    conv: Conversation = None
    
    def __init__(self, cfg: Config, conv:Conversation, *args, **kwargs) -> None:
        self.cfg = cfg
        self.conv = conv        # the conversation! update it when necessary!

    def check(self, bot_output: BotOutput) -> bool:
        # 1. check validation
        res, msg_content = self._check_with_message(bot_output)
        # 2. if not validated, log the error info!
        if not res:
            msg = Message(
                Role.SYSTEM, msg_content, prompt="", llm_response="",
                conversation_id=self.conv.conversation_id, utterance_id=self.conv.current_utterance_id
            )
            self.conv.add_message(msg)
        return res

    @abc.abstractmethod
    def _check_with_message(self, bot_output: BotOutput) -> Tuple[bool, str]:
        raise NotImplementedError


class PDLDependencyChecker(BaseChecker):
    pdl: PDL = None
    graph: PDLGraph = None
    curr_node = None
    
    def __init__(self, cfg:Config, conv:Conversation, pdl:PDL) -> None:
        super().__init__(cfg, conv)
        self.pdl = pdl
        self.graph = self._build_graph(pdl)
    
    def _build_graph(self, pdl:PDL):
        if (pdl.apis is None) or (not pdl.apis):  # if pdl.apis is None
            pdl.apis = []
        apis = pdl.apis
        g = PDLGraph()
        for api in apis:
            node = PDLNode(name=api["name"], preconditions=api.get("precondition", None), version=pdl.version)
            g.add_node(node)
        g.check_preconditions()
        return g

    def _check_with_message(self, bot_output: BotOutput) -> Tuple[bool, str]:
        next_node = bot_output.action
        # 1. match the node
        if next_node not in self.graph.name2node:
            return False, f"ERROR! Node {next_node} not found!"
        node = self.graph.name2node[next_node]
        # 2. check preconditions
        if node.precondition:
            for p in node.precondition:
                if not self.graph.name2node[p].is_activated:
                    msg = f"Precondition check failed! {p} not activated for {next_node}!"
                    return False, msg
        # 3. success! set it as activated
        node.is_activated = True
        msg = f"Check success! {next_node} activated!"
        return True, msg


class APIDuplicatedChecker(BaseChecker):
    """ to avoid duplicated API calls! """

    def _check_with_message(self, bot_output: BotOutput) -> Tuple[bool, str]:
        app_calling_info = self.conv.get_last_message().content
        duplicate_cnt = 0
        for check_idx in range(len(self.conv)-1, -1, -1):
            previous_msg = self.conv.get_message_by_idx(check_idx)
            if previous_msg.role != Role.BOT: continue
            if previous_msg.content != app_calling_info: break
            duplicate_cnt += 1
            if duplicate_cnt >= self.cfg.pdl_check_api_dup_calls_threshold:
                msg = "Too many duplicated API call! try another action instead."
                return False, msg
        msg = "Check success!"
        return True, msg
    
