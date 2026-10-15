import os,json

from typing import Sequence
from langchain_core.messages import message_to_dict,messages_from_dict,BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory

def get_history(session_id):
    return FileChatMessageHistory(session_id,'./chat_history')


class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self,session_id,storage_path):
        super().__init__()
        self.session_id=session_id
        self.storage_path=storage_path

        self.file_path=os.path.join(self.storage_path,self.session_id)

        os.makedirs(os.path.dirname(self.file_path),exist_ok=True)


    def add_message(self, message):
        
        all_messages=list(self.messages)
        all_messages.append(message)



        new_messages=[message_to_dict(message) for message in all_messages]
        with open(self.file_path,'w',encoding='utf-8') as f:
            json.dump(new_messages,f)
        
        return super().add_message(message)


    @property
    def messages(self):
        try:
            with open(self.file_path,'r',encoding='utf-8') as f:
                messages_data=json.load(f)

        except FileNotFoundError:
            return []

        return messages_from_dict(messages_data)


    def clear(self):

        with open(self.file_path,'w',encoding='utf-8') as f:
            json.dump([],f)
        return super().clear()