import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Response

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.gigachat import GigaChatEmbeddings

from utlis import get_text_chunks

load_dotenv()
API_TOKEN = os.environ.get("API_TOKEN")

app = FastAPI()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

embeddings = GigaChatEmbeddings(
    credentials=API_TOKEN, verify_ssl_certs=False
)

client = chromadb.HttpClient(host="chroma", port=8000, settings=Settings(allow_reset=True))
collection = client.get_or_create_collection("data")
langchain_chroma = Chroma(
    client=client,
    collection_name="data",
    embedding_function=embeddings,
)


@app.get("/")
def ping() -> str:
    return "pong"


@app.post("/load_text")
def load_text(text: str):
    try:
        chunks = get_text_chunks(text, text_splitter)
        langchain_chroma.add_texts(chunks)
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")




