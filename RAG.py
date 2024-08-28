from langchain.prompts import ChatPromptTemplate
import os
from langchain_core.output_parsers import StrOutputParser
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from operator import itemgetter
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()
api=os.getenv("PINECONE_API_KEY")
index_name=os.getenv("INDEX_NAME")
PINECONE_API_KEY = Pinecone(api_key=api)
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")

# embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-en-v1.5")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
def _combine_documents(
    docs ,document_separator="\n\n"):
        doc_strings = [doc.page_content for doc in docs]
        return document_separator.join(doc_strings)
def qa_ret(history,input_query):
    try:
        docsearch = PineconeVectorStore.from_existing_index(embedding=embeddings, index_name=index_name)
        # input_query="The first three parts laid the foundation for this concept of tiny, daily actions?"
        num_chunks=3
        retriever=docsearch.as_retriever(search_type='similarity', search_kwargs={"k": num_chunks})
        template = """You are an AI consultant specializing in guiding users about studying and living in Finland. Utilize the information from the provided context, user history, and your own knowledge to deliver clear, friendly, and concise responses.
        Context: {context}
        History: {history}
        Please provide a helpful and engaging answer.
        Question: {question}
        Guidelines:
        1. Analyze the user question thoroughly and respond specifically to queries related to studying or living in Finland. If the question is unrelated, respond by stating that you are only able to provide information about Finland and studying there.
        2. Acknowledge greetings, but do not provide detailed responses or information in these cases.
        3. Summarize the essential steps or information that the user needs.
        4. Provide relevant links or resources from the Study in Finland website.
        5. Encourage users to ask further questions or explore additional resources.
        Example Response:
        "Hello! To study in Finland, start by selecting a degree program that aligns with your interests. Visit the 'Admissions' section on the Study in Finland website to find detailed information about entry requirements and deadlines. If you have more questions, feel free to ask or explore the website for further guidance!"
        Now, please answer the question below.
        """

        prompt = ChatPromptTemplate.from_template(template)
        # setup_and_retrieval = RunnableParallel(
        #         {"context": retriever,"question": RunnablePassthrough()}
        #         )
        query_fetcher=itemgetter("question")
        setup_and_retrieval={"context": query_fetcher|retriever|_combine_documents, "question": query_fetcher,"history":itemgetter("history")}
            # Load QA Chain
        model = ChatOpenAI(api_key=OPENAI_API_KEY,model_name="gpt-4o-mini")
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
    
# You are an expert in document analysis, tasked with analyzing Letters of Recommendation and letters of motivation. Provide a rating and suggestions for improvement.


def analyze_document(doc_file):
        try:
                template = """You are an expert in ((Letter of Motivation)) and ((Letter of recommendation))
                analysis for admissions in Finish Universities for any kind of universities and programms.
                your task is analayze it first after that rate this document out of 10 and and also gives 3 short
                suggestions what you observe
                instructions:
                1.Make heading of ""Ranking""
                2.Make heading of ""suggestions"" and uder it create 3 points 
                """
                model = ChatOpenAI(model="gpt-4o-mini",api_key=OPENAI_API_KEY)
                prompt = ChatPromptTemplate.from_template(template)
                output_parser = StrOutputParser()
                chain = prompt | model | output_parser
                res = chain.invoke({"doc_file": doc_file})
                return res
        except Exception as e:
                raise e