import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Response

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma

from langchain.text_splitter import RecursiveCharacterTextSplitter
from yandex_chain import YandexEmbeddings
from yandex_chain import YandexLLM

from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, List, Any


from models import TextRequest
from utlis import get_text_chunks, extract_metadata, split_chunks_and_metadata


load_dotenv()
API_KEY = os.environ.get("API_KEY")
FOLDER_ID = os.environ.get("FOLDER_ID")


app = FastAPI()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

embeddings = YandexEmbeddings(
    folder_id=FOLDER_ID, api_key=API_KEY,
)

client = chromadb.HttpClient(host="chroma", port=8000, settings=Settings(allow_reset=True))
collection = client.get_or_create_collection("data")
langchain_chroma = Chroma(
    client=client,
    collection_name="data",
    embedding_function=embeddings,
)
llm = YandexLLM(folder_id=FOLDER_ID, api_key=API_KEY)
llm.temperature = 0


@app.get("/ping")
def ping() -> str:
    return "pong"


@app.post("/load_text")
def load_text(text: TextRequest):
    try:
        chunks, metadatas = split_chunks_and_metadata(get_text_chunks(text.text, text_splitter))

        langchain_chroma.add_texts(texts=chunks, metadatas=metadatas)
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/question")
def question(text: TextRequest):

    metadata = extract_metadata(text.text)

    name_list = [metadata["name"]] if metadata["name"] else []
    date_list = [metadata["date"]] if metadata["date"] else []
    company_list = [metadata["company"]] if metadata["company"] else []

    name_filter = {"name": {"$in": name_list}} if name_list else []
    date_filter = {"date": {"$in": date_list}} if date_list else []
    company_filter = {"company": {"$in": company_list}} if company_list else []

    filters = [f for f in [name_filter, date_filter, company_filter] if f]

    if len(filters) > 1:
        combined_filter = {"$or": filters}
    elif len(filters) == 1:
        combined_filter = filters[0]
    else:
        combined_filter = None

    template = """Answer the question in short based only on the following context:
        {context}

        Question: {question}
        """
    prompt = ChatPromptTemplate.from_template(template)

    if combined_filter:
        chain = ({"context": langchain_chroma.as_retriever(search_kwargs={'k': 5, 'filter': combined_filter}),
                  "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    else:
        chain = ({"context": langchain_chroma.as_retriever(),
                  "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())

    return {"answer": chain.invoke(text.text)}
