import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Response, File, UploadFile

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma

from langchain.text_splitter import RecursiveCharacterTextSplitter
from yandex_chain import YandexEmbeddings
from yandex_chain import YandexLLM

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

import shutil
from tempfile import NamedTemporaryFile

from langchain_community.document_loaders import PyMuPDFLoader

from models import TextRequest
from utlis import get_text_chunks, MyLoader, is_scans, extract_metadata, split_chunks_and_metadata

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

history = ChatMessageHistory()


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


@app.post("/load_pdf")
def load_pdf(file: UploadFile = File(...)):

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
    chunks, metadatas = split_chunks_and_metadata(get_text_chunks(text, text_splitter))
    langchain_chroma.add_texts(texts=chunks, metadatas=metadatas)
    return Response(status_code=200)


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

    search_kwargs = {"k": 5}

    if len(filters) > 1:
        search_kwargs["filter"] = {"$or": filters}
    elif len(filters) == 1:
        search_kwargs["filter"] = filters[0]

    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is."""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, langchain_chroma.as_retriever(search_kwargs=search_kwargs), contextualize_q_prompt,
    )

    template = """Answer the question in short based only on the following context:
        {context}

        Question: {input}
        """
    qa_prompt = ChatPromptTemplate.from_template(template)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        lambda _: history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    return {
        "answer": conversational_rag_chain.invoke(
            {"input": text.text}, config={"configurable": {"session_id": "42"}}
        )["answer"]
    }


@app.get("/clear_history")
def clear_history():
    global history
    try:
        history = ChatMessageHistory()
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
