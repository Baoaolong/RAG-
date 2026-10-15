import os
import json
from typing import Sequence

from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory


def get_history(session_id):
    # 基于本文件位置，容器/服务器上工作目录变化也能写对地方
    history_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history')
    return FileChatMessageHistory(session_id, history_root)


class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id, storage_path):
        super().__init__()
        self.session_id = session_id
        self.storage_path = storage_path

        self.file_path = os.path.join(self.storage_path, self.session_id)

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def _write_messages(self, messages):
        """把完整消息列表落盘；写入前先建目录，避免首个会话文件写不进去。"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        new_messages = [message_to_dict(message) for message in messages]
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(new_messages, f, ensure_ascii=False)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        # langchain-core 1.x 的新入口：一次性追加多条消息
        all_messages = list(self.messages)
        all_messages.extend(messages)
        self._write_messages(all_messages)

    def add_message(self, message: BaseMessage) -> None:
        # 保留单条写入接口；不要再调用 super()，
        # 否则基类会因为「本类没有实现 add_messages」而抛 NotImplementedError
        self.add_messages([message])

    @property
    def messages(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
        except FileNotFoundError:
            return []

        return messages_from_dict(messages_data)

    def clear(self):
        self._write_messages([])
        return super().clear()