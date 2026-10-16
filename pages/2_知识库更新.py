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
        import hashlib

        env_pw = os.getenv("ADMIN_PASSWORD")
        try:
            sec_pw = st.secrets["ADMIN_PASSWORD"]
        except Exception as exc:
            sec_pw = f"<不可用: {type(exc).__name__}>"
        try:
            sec_any = sorted(list(st.secrets.keys()))
        except Exception:
            sec_any = []

        # 临时诊断：只显示长度与哈希，不显示明文。排查完删掉这一段。
        lines = []
        for label, val in (("环境变量", env_pw), ("st.secrets", sec_pw)):
            if isinstance(val, str) and not val.startswith("<"):
                lines.append(
                    f"{label}: 长度 {len(val)} sha256_12 "
                    f"{hashlib.sha256(val.encode('utf-8')).hexdigest()[:12]}"
                )
            else:
                lines.append(f"{label}: {val}")
        lines.append(f"st.secrets 里的键: {sec_any}")
        lines.append(f"输入值: 长度 {len(password)} sha256_12 "
                     f"{hashlib.sha256(password.encode('utf-8')).hexdigest()[:12]}")
        st.code("\n".join(lines), language="text")

        correct_password = env_pw or (sec_pw if isinstance(sec_pw, str) else None)

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