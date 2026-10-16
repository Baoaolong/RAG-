from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.runnables import RunnablePassthrough,RunnableWithMessageHistory,RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from file_history_store import get_history
import os


DEBUG_PROMPT = os.getenv('RAG_DEBUG_PROMPT') == '1'


def print_prompt(prompt):
    if not DEBUG_PROMPT:
        return prompt

    print('=='*20)
    print(prompt.to_string())
    print('=='*20)

    return prompt



class RagService(object):
    def __init__(self):
        self.vector_service=VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name)

        )

        self.prompt_template=ChatPromptTemplate.from_messages(
            [
                ('system','你是网店的智能客服小助手，语气自然、亲切、简洁，'
                 '主要根据参考资料回答用户问题。参考资料：{context}'),
                ('system','回答规则：\n'
                 '1. 若参考资料里有相关内容，严格依据它回答，不要编造。\n'
                 '2. 若参考资料为“无相关参考资料”或内容与问题无关：\n'
                 '   - 用户只是打招呼、道谢、再见、闲聊时，自然友好地回应即可，不要拒绝。\n'
                 '   - 用户问的是知识库没收录的事实（尺码、库存、物流、售后政策等），'
                 '坦率说明资料里没有，建议联系人工客服，绝不编造。\n'
                 '3. 与衣物洗护、尺码、搭配完全无关的请求（写作文、写代码等），礼貌说明帮不上并回到业务范围。\n'
                 '4. 不要提及“参考资料”“知识库”“文档”这类字眼，用自己的话回答。'),
                 ('system','以下是我提供用户的对话历史记录: '),
                 MessagesPlaceholder('history'),
                 ('user','请回答用户提问:{input}')

            ]
        )



        self.chat_model=ChatTongyi(model=config.chat_model_name)

        self.chain=self.get_chain()

    def get_chain(self):
        retriever=self.vector_service.get_retriever()

        def format_document(docs):
            if not docs:
                return '无相关参考资料'

            formatted_str=""
            for doc in docs:
                formatted_str+=f'文档片段:{doc.page_content}\n文档原数据:{doc.metadata}\n\n'
            return formatted_str
        def temp1(value):
            # 当前用户的问题
            current_question = value['input']
            # 获取聊天历史
            history = value.get('history', [])
            # 只使用最近4条历史消息，避免上下文太长
            recent_history = history[-4:]
            history_text = '\n'.join(f"{'用户' if msg.type == 'human' else '助手'}：{msg.content}" for msg in recent_history if isinstance(msg.content, str)
    )
            # 如果是第一次提问，直接检索当前问题
            if not history_text:
                return current_question
            return (f"最近的对话历史：\n{history_text}\n" f"当前问题：{current_question}"
    )
            
        def temp2(value):
            # print('--------',value)
            new_value={}
            new_value['input']=value['input']['input']
            new_value['context']=value['context']
            new_value['history']=value['input']['history']
            return new_value

        chain=(
            {
                'input':RunnablePassthrough(),
                'context':RunnableLambda(temp1) | retriever| format_document
                
            } | RunnableLambda(temp2) | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )

        conversation_chain=RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key='input',
            history_messages_key='history',

        )
        return conversation_chain
        # return chain


if __name__=='__main__':

    session_config={
        'configurable':{
            'session_id':'user_001',
        }
    }

    res=RagService().chain.invoke({'input':'体重140斤'},session_config)
    print(res)