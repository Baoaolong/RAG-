import os
from pathlib import Path

# ---- 关键：在 import langchain 之前先把 .env 里的 DASHSCOPE_API_KEY 注入 os.environ ----
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / '.env', override=False)

import config_data as config
import hashlib
import datetime
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma


def check_md5(md5_str):
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        # 原来写成了 open(...).readline()，只会读第一行并且按“字符”遍历
        with open(config.md5_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() == md5_str:
                    return True
            return False


def save_md5(md5_str):
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')


def get_string_md5(input_str, encoding='utf-8'):
    str_bytes = input_str.encode(encoding=encoding)

    md5_obj = hashlib.md5()
    md5_obj.update(str_bytes)
    md5_hex = md5_obj.hexdigest()

    return md5_hex


class KnowledgeBaseService(object):

    def __init__(self):
        os.makedirs(config.persist_directory, exist_ok=True)

        self.chroma = Chroma(
            collection_name=config.collection_name,
            embedding_function=DashScopeEmbeddings(model='text-embedding-v4'),
            persist_directory=config.persist_directory,
        )

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,   # 原来拼成 chunk_over_lap，会 TypeError
            separators=config.separators,
            length_function=len,
        )

    def upload_by_str(self, data, filename):
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            return '[跳过]内容已经存在知识库中'

        # if len(data) > config.max_split_char_number:
        #     knowledge_chunks: list[str] = self.spliter.split_text(data)
        # else:
        #     knowledge_chunks = [data]
        knowledge_chunks = self.spliter.split_text(data)

        metadata = {
            'source': filename,
            # 原来写的是 datetime.now()，会 AttributeError
            'create_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'operator': '小薯',
        }
        self.chroma.add_texts(
            knowledge_chunks,
            metadatas=[metadata for _ in knowledge_chunks],
        )

        save_md5(md5_hex)

        return '[成功]内容已经成功载入向量库'


if __name__ == '__main__':
    service = KnowledgeBaseService()
    # r = service.upload_by_str('周杰伦', 'testfile')
    # print(r)

    # file_path = Path(r'D:\vsCode\python\RAG项目练习\data\尺码推荐.txt')

    # with open(file_path, 'r', encoding='utf-8') as f:
    #     text = f.read()

    # result = service.upload_by_str(text, '尺码推荐.txt')
    # print(result)

    # print(service.chroma.get(include=['documents', 'metadatas']))
    # file_path = Path(
    #     r'D:\vsCode\python\RAG项目练习\data\尺码推荐.txt'
    # )
    # text = file_path.read_text(encoding='utf-8')

    # # 1. 计算这份文档的 MD5
    # md5_hex = get_string_md5(text)

    # # 2. 删除数据库中旧的、来源为尺码推荐.txt的文档
    # service.chroma.delete(
    #     where={'source': '尺码推荐.txt'}
    # )

    # # 3. 从 md5.txt 中移除这份文档的去重记录
    # md5_file = Path(config.md5_path)

    # if md5_file.exists():
    #     lines = md5_file.read_text(encoding='utf-8').splitlines()
    #     remaining_lines = [
    #         line for line in lines
    #         if line.strip() != md5_hex
    #     ]
    #     md5_file.write_text(
    #         ''.join(line + '\n' for line in remaining_lines),
    #         encoding='utf-8'
    #     )

    # # 4. 按新的分块规则重新导入
    # chunks = service.spliter.split_text(text)
    # print('预计文本块数量：', len(chunks))

    # result = service.upload_by_str(text, '尺码推荐.txt')
    # print('导入状态：', result)

    # # 5. 只查看这份文档重新导入后的结果
    # data = service.chroma.get(
    #     where={'source': '尺码推荐.txt'},
    #     include=['documents', 'metadatas']
    # )

    # print('实际文本块数量：', len(data['documents']))

    # for i, doc in enumerate(data['documents'], start=1):
    #     print(f'\n第 {i} 块，长度：{len(doc)}')
    #     print(doc)


    # 1. 找到存放 TXT 文档的文件夹
    data_dir=Path(__file__).resolve().parent/'data'
    # 2. 写出这次想导入的两个文件名
    file_names=[
        '洗涤养护.txt',
        '颜色选择.txt',
        '尺码推荐.txt',
    ]
    for file_name in file_names:
        file_path=data_dir/file_name

        if not file_path.is_file():
            print(f'[失败]找不到文件:{file_path}')
            continue
        text=file_path.read_text(encoding='utf-8')

        if not text.strip():
            print(f'[跳过]文件内容为空:{file_name}')
            continue
        result=service.upload_by_str(text,file_name)
        print(file_name,result)
