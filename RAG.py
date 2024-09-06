from langchain.prompts import ChatPromptTemplate
import os
from langchain_core.output_parsers import StrOutputParser
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from operator import itemgetter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()
api=os.environ.get("PINECONE_API_KEY")
index_name=os.environ.get("INDEX_NAME")
PINECONE_API_KEY = Pinecone(api_key=api)
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
embeddings =OpenAIEmbeddings(model="text-embedding-3-small")
def _combine_documents(
    docs ,document_separator="\n\n"):
        doc_strings = [doc.page_content for doc in docs]
        return document_separator.join(doc_strings)

def ai_consultant(history,input_query):
    try:
        docsearch = PineconeVectorStore.from_existing_index(embedding=embeddings, index_name=index_name)
        num_chunks=7
        retriever=docsearch.as_retriever(search_type='similarity', search_kwargs={"k": num_chunks})
        template = """You are an AI consultant specializing in guiding users about studying and living in Finland. Utilize the information from the provided context, user history, and your own knowledge to deliver clear, friendly, and concise responses.
        Context: {context}
        History: {history}
        Please provide a helpful and engaging answer.
        Question: {question}
        Guidelines:
        1. **Analyze the user question thoroughly and respond specifically to queries related to studying or living in Finland. If the question is unrelated, respond by stating that you are only able to provide information about Finland and studying there.**
        2. **Acknowledge greetings, but do not provide detailed responses or information in these cases.**
        3. **Summarize the essential steps or information that the user needs.**
        4. **Provide relevant links or resources from the Study in Finland website.**
        5. **Encourage users to ask further questions or explore additional resources.**
        6. **Do not go out of the context provided**
        7. **If the question is out of the context tha simply say sorry I found nothing about ask me another question.**
        """
        prompt = ChatPromptTemplate.from_template(template)
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
    
def analyze_letter_of_motivation(program_name,program_description,lom):
    try:
        template = """You are an expert in Letter of Motivation {lom} for Bachelor's, Masters, and Phd programs
        evaluation for admissions in Finland Universities for both applied sciences universities and research based universities.
        Your task is analayze it first after that rate this document out of 10 and and also gives at least 3 suggestions to improve the letter of motivation.
        Instructions:
        **1. Analyze for grammer mistakes, sentence structuring, vocabulary.**
        **2. Check program relevancy by matching letter of motivation with {program_name}, {program_description}**
        **3. Check for any kind of acheivements relevent to {program_name}**
        **4. Check for any research experiance or work experiance relevant to {program_name}**
        **5. Check for the user motivational statements why they want to study in respective field {program_name}**
        **6. Response should not be greater than 5 lines**
        Note : 
        **After analyzing the above instructuction rate the letter out of 10 deduct rating based on above instructions**
        """
        context_fetcher=itemgetter("lom")
        setup_and_retrieval={"lom": context_fetcher,"program_name":itemgetter("program_name"),"program_description":itemgetter("program_description")}
        model = ChatOpenAI(model="gpt-4o-mini",api_key=OPENAI_API_KEY)
        prompt = ChatPromptTemplate.from_template(template)
        output_parser = StrOutputParser()
        chain = setup_and_retrieval | prompt | model | output_parser
        res = chain.invoke({"lom": lom,"program_name":program_name,"program_description":program_description})
        return res
    except Exception as e:
        raise e
    
def transcript_evaluation(program_name,program_description,transcript_of_records):
    try:
        template = """You are an expert in Transcript {transcript_of_records} for Bachelor's, Masters, and Phd programs
        evaluation for admissions in Finland Universities for both applied sciences universities and research based universities.
        Your task is analayze it first after than give some 3 peaceful advice basis on the record and also tells him with this transcript of records how many percent of
        chances are that you get admission in Finland.
        Instructions:
        **1. Analyze the grades of each subject or course**
        **2. Check program relevancy by matching Transcript with {program_name}, {program_description}**
        **3. Check for any kind of poor grades in those subjects relevent to {program_name}**
        **5. Check for if the transcript has irrelevant information than just said the provided information is irrelevant**
        **6. Response should not be greater than 5 lines**
        Note : 
        **After analyzing the above instructions tells te user how many percent of chances are there that you will get admission in Finland Universities.**
        """
        context_fetcher=itemgetter("transcript_of_records")
        setup_and_retrieval={"transcript_of_records": context_fetcher,"program_name":itemgetter("program_name"),"program_description":itemgetter("program_description")}
        model = ChatOpenAI(model="gpt-4o-mini",api_key=OPENAI_API_KEY)
        prompt = ChatPromptTemplate.from_template(template)
        output_parser = StrOutputParser()
        chain = setup_and_retrieval | prompt | model | output_parser
        res = chain.invoke({"transcript_of_records": transcript_of_records,"program_name":program_name,"program_description":program_description})
        return res
    except Exception as e:
        raise e
    
def resume_evaluation(program_name,program_description,resume):
    try:
        template = """You are an expert in resume or cv {resume} for Bachelor's, Masters, and Phd programs
        evaluation for admissions in Finland Universities for both applied sciences universities and research based universities.
        Your task is analayze it first after than give some 3 peaceful advice basis on the record and also rate the resume out of 10
        Instructions:
        **1. Analyze marks, CGPA or Grades if provided in resume**
        **2. Check program relevancy by matching reume with {program_name}, {program_description}**
        **3. Check for if the resume has irrelevant information than just said the provided information is irrelevant**
        **4. Response should not be greater than 5 lines**
        Note : 
        **After analyzing the above instructions rate the resume out of 10 and also tells the user how many chances are there that you will get admission in this {program_name} in Finland University .**
        """
        context_fetcher=itemgetter("resume")
        setup_and_retrieval={"resume": context_fetcher,"program_name":itemgetter("program_name"),"program_description":itemgetter("program_description")}
        model = ChatOpenAI(model="gpt-4o-mini",api_key=OPENAI_API_KEY)
        prompt = ChatPromptTemplate.from_template(template)
        output_parser = StrOutputParser()
        chain = setup_and_retrieval | prompt | model | output_parser
        res = chain.invoke({"resume": resume,"program_name":program_name,"program_description":program_description})
        return res
    except Exception as e:
        raise e
    
def history_summerizer(history):
    try:
        template = """You are an expert chat history summerizer. Your task is to summerize the chat history {history}.
        Instructions:
        **Summerize the chat history in 3 lines maximum do not exceed than 2 lines.**
        **Anlyze the User Question and AI answer properly**
        """
        model = ChatOpenAI(model="gpt-4o-mini",api_key=OPENAI_API_KEY)
        prompt = ChatPromptTemplate.from_template(template)
        output_parser = StrOutputParser()
        chain = prompt | model | output_parser
        res = chain.invoke({"history": history})
        return res
    except Exception as e:
        raise e