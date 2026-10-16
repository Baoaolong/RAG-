import os
import streamlit as st

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if not st.session_state["admin_logged_in"]:
    st.title("知识库管理登录")

    password = st.text_input(
        "请输入管理员密码",
        type="password"
    )

    if st.button("登录"):
        correct_password = os.getenv("ADMIN_PASSWORD")
        if not correct_password:
            try:
                correct_password = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                correct_password = None

        if correct_password and password == correct_password:
            st.session_state["admin_logged_in"] = True
            st.rerun()
        elif not correct_password:
            st.error("请先配置 ADMIN_PASSWORD")
        else:
            st.error("密码错误")

    st.stop()

from knowledge_base import KnowledgeBaseService

st.title('知识库更新')


uploader_file=st.file_uploader(
    '请上传文件',
    type=['txt'],
    accept_multiple_files=False,
)

if 'counter' not in st.session_state:
    st.session_state['counter']=0
if 'service' not in st.session_state:
    st.session_state['service']=KnowledgeBaseService()



if uploader_file is not None:
    file_name=uploader_file.name
    file_type=uploader_file.type
    file_size=uploader_file.size/1024


    st.subheader(f'文件名:{file_name}')
    st.write(f'格式:{file_type} | 大小:{file_size:.2f}KB')


    text=uploader_file.getvalue().decode('utf-8')
    st.write(text)

    st.session_state['counter']+=1


    with st.spinner('载入知识库中...'):
        result=st.session_state['service'].upload_by_str(text,file_name)
        st.write(result)