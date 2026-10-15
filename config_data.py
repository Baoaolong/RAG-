md5_path='./md5.txt'



collection_name='rag'
persist_directory='./chroma_db'



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
