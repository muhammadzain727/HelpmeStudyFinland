from langchain.prompts import ChatPromptTemplate
import os
from langchain_core.output_parsers import StrOutputParser
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from operator import itemgetter
from langchain_openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
api=os.environ.get("PINECONE_API_KEY")
PINECONE_API_KEY = Pinecone(api_key=api)
embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def _combine_documents(
    docs ,document_separator="\n\n"):
        doc_strings = [doc.page_content for doc in docs]
        return document_separator.join(doc_strings)
def qa_ret(history,index_name,input_query):
    try:
        docsearch = PineconeVectorStore.from_existing_index(embedding=embeddings, index_name=index_name)
        # input_query="The first three parts laid the foundation for this concept of tiny, daily actions?"
        num_chunks=2
        retriever=docsearch.as_retriever(search_type='similarity', search_kwargs={'namespace': 'test-space'})

        OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")
        template = """You are AI assistant that assisant user by providing answer to the question of user by extracting information from provided context and history:
        {context} and {history} if you do not find any relevant information from context or history for given question just say ask me another quuestion. you are ai assistant.
        Answer should not be greater than 3 lines.
        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)
        # setup_and_retrieval = RunnableParallel(
        #         {"context": retriever, "question": RunnablePassthrough()}
        #         )
        query_fetcher=itemgetter("question")
        setup_and_retrieval={"context": query_fetcher|retriever|_combine_documents, "question": query_fetcher,"history":itemgetter("history")}
            # Load QA Chain
        model = OpenAI(api_key=OPENAI_API_KEY,model_name="gpt-4o-mini")
        output_parser= StrOutputParser()
        rag_chain = (
        setup_and_retrieval
        | prompt
        | model
        | output_parser
        )
        response=rag_chain.invoke({"history":history,"question":input_query})
        return response
    except Exception as e:
        raise Exception(f"llm response failed: {str(e)}")