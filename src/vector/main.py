import logging
import os
import shutil
from uuid import uuid4
from fastapi import FastAPI, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID, uuid4
from sqlalchemy.sql import func

from src.database import get_async_session, engine, Base, Document, User
from src.DTO import Userbd, Vector, KNN

app = FastAPI()

logger = logging.getLogger(__name__)


@app.post("/files")
async def upload_file(
        content: str,
        session: AsyncSession = Depends(get_async_session)):

    file_id = uuid4()

    document = Document(id=file_id, content=content)
    session.add(document)
    await session.commit()

    return JSONResponse(status_code=200, content={"document_id": str(document.id)})


@app.post("/vectors")
async def upload_vector(
        new_user: Userbd,
        session: AsyncSession = Depends(get_async_session)):

    user = User(document_id=new_user.document_id, vector=new_user.vector, start=new_user.start, end=new_user.end)
    session.add(user)
    await session.commit()

    return JSONResponse(status_code=200, content={"document_id": str(user.document_id), "user_id": str(user.id)})


@app.get("/files/{document_id}")
async def get_document(document_id: UUID, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Document).filter_by(id=document_id))
    document = result.scalars().first()
    if document:
        return JSONResponse(status_code=200, content={"document_id": str(document.id), "content": document.content})
    return JSONResponse(status_code=404, content={"message": "Document not found"})


@app.post("/nearest_files/")
async def nearest_files(
        vectord: Vector,
        session: AsyncSession = Depends(get_async_session)):
    results = await session.execute(
        select(
            User.document_id,
            func.sum(User.vector.cosine_distance(vectord.vector)).label('cosine_sum'),
        )
        .group_by(User.document_id)
        .order_by('cosine_sum'),
    )
    nearest_file = results.first()

    logger.info(nearest_file)

    if nearest_file is not None:
        nearest_file_dict = {
            "document_id": str(nearest_file.document_id)
        }
        return JSONResponse(content=nearest_file_dict)
    else:
        return JSONResponse(content={}, status_code=404)


@app.post("/vectors/knn")
async def knn(
        vectork: KNN,
        session: AsyncSession = Depends(get_async_session)):
    results = await session.execute(
        select(User)
        .order_by(User.vector.l2_distance(vectork.vector))
        .limit(vectork.k),
    )
    nearest_neighbors = results.scalars().all()

    if nearest_neighbors:
        nearest_neighbors_list = [
            {
                "document_id": str(neighbor.document_id),
                "start": neighbor.start,
                "end": neighbor.end,
            }
            for neighbor in nearest_neighbors
        ]
        logger.info(f"Returning nearest neighbors: {nearest_neighbors_list}")
        return JSONResponse(content=nearest_neighbors_list)
