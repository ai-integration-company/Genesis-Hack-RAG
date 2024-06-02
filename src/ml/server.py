import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Response, File, UploadFile

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma

from langchain.text_splitter import RecursiveCharacterTextSplitter
from yandex_chain import YandexEmbeddings
from yandex_chain import YandexLLM

from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

import shutil
from tempfile import NamedTemporaryFile
from langchain_community.document_loaders import PyMuPDFLoader

from models import TextRequest
from utlis import get_text_chunks, MyLoader, is_scans

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
        chunks = get_text_chunks(text.text, text_splitter)
        langchain_chroma.add_texts(chunks)
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load_pdf")
def load_pdf(file: UploadFile = File(...)):

    try:
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
            # Copy the uploaded file content to the temp file
            with open(tmp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        if is_scans(tmp_path):
            loader = MyLoader(tmp_path, extract_images=True)
        else:
            loader = PyMuPDFLoader(tmp_path)

        documents = loader.load()
        text = "\n".join([doc.page_content for doc in documents])
        chunks = get_text_chunks(text, text_splitter)
        langchain_chroma.add_texts(chunks)
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/question")
def question(text: TextRequest):
    try:
        template = """Answer the question in short based only on the following context:
        {context}

        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)

        chain = (
                {"context": langchain_chroma.as_retriever(), "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
        )

        return {"answer": chain.invoke(text.text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






