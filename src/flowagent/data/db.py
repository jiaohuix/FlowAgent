""" updated @240906

"""
from typing import List
import pymongo, pymongo.results
from .base_data import Message, Conversation, Role

class DBManager:
    def __init__(
        self, uri='mongodb://localhost:27017/', db_name='message_database', 
        collection_name='messages', meta_collection_name='config', eval_collection_name='evaluations',
        **kwargs
    ) -> None:
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.collection_meta = self.db[meta_collection_name]
        self.collection_eval = self.db[eval_collection_name]

    def insert_message(self, message: Message) -> pymongo.results.InsertOneResult:
        message_dict = message.to_dict()
        res = self.collection.insert_one(message_dict)
        # print(f"  <db> Inserted message: {message.content}")

    def insert_conversation(self, conversation: Conversation) -> pymongo.results.InsertManyResult:
        msg_list = conversation.to_list()
        res = self.collection.insert_many(msg_list)
        return res

    def query_messages_by_conversation_id(self, conversation_id: str) -> Conversation:
        query = {"conversation_id": conversation_id}
        results = self.collection.find(query)
        results = [res for res in results]
        if len(results)==0:
            return Conversation()
        messages = [Message(**{**res, "role": Role.get_by_rolename(res["role"])}) for res in results]
        return Conversation.from_messages(messages)
    
    def insert_config(self, infos: dict) -> pymongo.results.InsertOneResult:
        """ record one experiment """
        res = self.collection_meta.insert_one(infos)
        return res
    
    def query_config_by_conversation_id(self, conversation_id: str) -> dict:
        query = {"conversation_id": conversation_id}
        res = self.collection_meta.find_one(query)
        return res
    
    def get_most_recent_unique_conversation_ids(
        self, query: dict = {}, limit: int = 0
    ) -> List[str]:
        """ query collection_meta, sort by conversation_id """
        sort_order = [('conversation_id', -1)]
        results = self.collection_meta.find(query).sort(sort_order).limit(limit)
        return [res["conversation_id"] for res in results]
    
    def query_run_experiments(self, query: dict = {}, limit: int = 0) -> List[dict]:
        sort_order = [('conversation_id', -1)]
        results = self.collection_meta.find(query).sort(sort_order).limit(limit)
        return [res for res in results]
    
    def delete_run_experiments(self, query: dict = {}) -> pymongo.results.DeleteResult:
        res = self.collection_meta.delete_many(query)
        return res
    
    def get_all_run_exp_versions(self) -> List[str]:
        results = self.collection_meta.distinct("exp_version")
        return results

    def query_evaluations(self, query: dict = {}, limit: int = 0) -> List[dict]:
        results = self.collection_eval.find(query).limit(limit)
        return [res for res in results]
    
    def insert_evaluation(self, eval_result: dict) -> pymongo.results.InsertOneResult:
        res = self.collection_eval.insert_one(eval_result)
        return res
    
    def delete_evaluations(self, query: dict = {}) -> pymongo.results.DeleteResult:
        res = self.collection_eval.delete_many(query)
        return res


if __name__ == "__main__":
    db_manager = DBManager(db_name="test_db", collection_name="messages")

    message = Message(role=Role.USER, content="Hello", prompt="prompt", llm_response="response", conversation_id="conv1", utterance_id=1)
    db_manager.insert_message(message)

    conversation = Conversation()
    conversation.msgs.append(message)
    conversation.msgs.append(Message(role=Role.SYSTEM, content="Hi there!", prompt="prompt", llm_response="response", conversation_id="conv1", utterance_id=2))
    db_manager.insert_conversation(conversation)

    messages = db_manager.query_messages_by_conversation_id("conv1")
    for msg in messages:
        print(msg.to_str())