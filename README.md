---
title: 智能客服 RAG
emoji: 🧵
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 智能客服 RAG（基于通义千问的知识库问答）

一个可上线的小型 RAG 客服应用：上传自家业务文档 → 向量化入库 → 用户提问时检索资料并带着对话历史作答。

## 功能

- **对话问答**：基于知识库资料回答，支持多轮追问（会带上最近 4 条对话历史）
- **知识库更新**（需管理员密码）：上传 `.txt` 文档，自动切分、向量化并写入 Chroma
- **向量检索**：DashScope `text-embedding-v4` + Chroma，检索 Top-3 片段作为参考资料
- **会话级隔离**：每个浏览器会话有独立的 `session_id`，聊天历史按会话落盘

## 目录结构

| 路径 | 作用 |
| --- | --- |
| `app_qa.py` | 主页面：对话问答 |
| `pages/2_知识库更新.py` | 知识库管理页（密码保护） |
| `rag.py` | 检索 + 提示词 + 模型的链（RagService） |
| `knowledge_base.py` / `vector_stores.py` | 文档切分入库 / 向量库封装 |
| `file_history_store.py` | 按会话把聊天历史存成 JSON |
| `config_data.py` | 模型名、切分参数、top-k 等配置 |
| `chroma_db/` | 已建好的向量库（随仓库提供，无需重新embedding） |
| `data/` | 原始知识文档 |

## 部署到 Hugging Face Spaces（本仓库已配好）

1. 打开 https://huggingface.co/new-space ，填名字，**SDK 选 Docker**，硬件选免费的 CPU basic，创建。
2. 把本仓库代码推到这个 Space（或直接在 Space 的 Files 页面上传）。
3. 进入 **Settings → Variables and secrets**，添加两个 **Secret**：
   - `DASHSCOPE_API_KEY`：阿里云百炼控制台申请的密钥（`sk-` 开头）
   - `ADMIN_PASSWORD`：知识库管理页的登录密码，自己定
4. 等构建完成（首次约 3~6 分钟），页面出现即部署成功。

> ⚠️ 免费版 Space 在无访问时会休眠，下一次访问需要几十秒唤醒，属正常现象。

## 本地运行

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    mac/linux: source .venv/bin/activate
pip install -r requirements.txt

# 本地用 .env（已被 .gitignore 忽略），或直接设环境变量
echo "DASHSCOPE_API_KEY=sk-你的密钥" > .env
echo "ADMIN_PASSWORD=你的密码" >> .env

streamlit run app_qa.py
```

浏览器打开 http://localhost:7860 （端口由 `.streamlit/config.toml` 指定，与云端一致）。

## 配置项（`config_data.py`）

| 配置 | 当前值 | 说明 |
| --- | --- | --- |
| `chat_model_name` | `qwen3.7-max` | 对话模型 |
| `embedding_model_name` | `text-embedding-v4` | 向量模型，**换了要重建向量库** |
| `chunk_size` / `chunk_overlap` | 300 / 50 | 文档切分粒度 |
| `similarity_threshold` | 3 | 检索返回片段数 |

## 调试

设 `RAG_DEBUG_PROMPT=1` 可打印送入模型的完整提示词（默认关闭，避免日志泄露用户数据）。

## 注意

- 向量库已随仓库提交，**不要重复上传同一份文档**，重复 embedding 会消耗额度且产生重复片段。
- 容器文件系统在重建后会重置，因此**运行期内新增的知识文档与聊天历史不会永久保留**。需要持久化请改用国内云服务器并挂载数据盘，或接入外部数据库。
