"""魔搭创空间（ModelScope Studio）Streamlit 类型的入口文件。

平台要求 Streamlit 应用以 `app.py` 作为入口，才能真正跑起来。
这里只做一件事：定位到项目根目录，然后执行真正的主页面 app_qa.py，
避免把 70 多行页面代码复制成两份、日后改一处忘一处。
"""
import runpy
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

# 让 app_qa / rag / config_data 等同级模块都能被导入，
# 无论平台把代码放在哪个工作目录
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

runpy.run_path(str(APP_DIR / "app_qa.py"), run_name="__main__")
