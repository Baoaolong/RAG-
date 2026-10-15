import os
import uuid
import streamlit as st
from dotenv import load_dotenv

# 1. 本地开发时读取 .env
load_dotenv()

# 2. 云端（Hugging Face / 服务器）没有 .env，密钥来自环境变量或 Streamlit Secrets
if not os.getenv("DASHSCOPE_API_KEY"):
    try:
        os.environ["DASHSCOPE_API_KEY"] = (
            st.secrets["DASHSCOPE_API_KEY"]
        )
    except Exception:
        pass
if not os.getenv("DASHSCOPE_API_KEY"):
    st.error("尚未配置 DASHSCOPE_API_KEY，请检查密钥设置。")
    st.stop()


import config_data as config
import streamlit as st
# 3. 必须在上面完成之后再导入模型
from rag import RagService
import time

st.title('智能客服')

st.divider()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

session_config = {
    "configurable": {
        "session_id": st.session_state["session_id"]
    }
}

if 'message' not in st.session_state:
    st.session_state['message']=[{'role':'assistant','content':'你好，有什么可以帮助你?'}]

if 'rag' not in st.session_state:
    st.session_state['rag']=RagService()


for message in st.session_state['message']:
    st.chat_message(message['role']).write(message['content'])


prompt=st.chat_input()


if prompt:

    st.chat_message('user').write(prompt)
    st.session_state['message'].append({'role':'user','content':prompt})


    ai_res_list=[]

    with st.spinner('AI思考中....'):
        res_steam=st.session_state['rag'].chain.stream({'input':prompt},session_config)


        def capture(generator,cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                yield chunk

        st.chat_message('assistant').write_stream(capture(res_steam,ai_res_list))
        st.session_state['message'].append({'role':'assistant','content':''.join(ai_res_list)})