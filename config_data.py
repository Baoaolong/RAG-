from pathlib import Path

# 以本文件所在目录为基准，避免工作目录变化（本地 / 容器 / 服务器）时找不到向量库
APP_DIR = Path(__file__).resolve().parent

md5_path = str(APP_DIR / 'md5.txt')


collection_name = 'rag'
persist_directory = str(APP_DIR / 'chroma_db')



chunk_size=300
chunk_overlap=50
separators=['\n\n','\n','.','!','?','。','！','？','，','']
max_split_char_number=1000

similarity_threshold=3

embedding_model_name='text-embedding-v4'
chat_model_name='qwen3.7-max'


session_config={
        'configurable':{
            'session_id':'user_001',
        }
    }
