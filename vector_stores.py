from langchain_chroma import Chroma
import config_data as config


class VectorStoreService(object):
    def __init__(self,embedding):
        self.embedding=embedding

        self.vector_store=Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory,
        )



    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={'k':config.similarity_threshold})


if __name__=='__main__':
    from langchain_community.embeddings import DashScopeEmbeddings

    retriever=VectorStoreService(DashScopeEmbeddings(model=config.embedding_model_name)).get_retriever()

    # res=retriever.invoke('我是男的，我的体重180斤，尺码推荐')
    while True:
        question=input('你想问的问题：').strip()
        if question.lower()=='q':
            break
        res=retriever.invoke(question)
        for i,doc in enumerate(res,start=1):
            print(f'\n相关资料{i}:')
            print(doc.page_content)
            print('-'*40)