from sqlalchemy import Column, String, ForeignKey, ARRAY, FLOAT, INTEGER, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship, mapped_column, Mapped
from uuid import uuid4
from typing import List
from pgvector.sqlalchemy import Vector

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from uuid import UUID, uuid4


from config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


class Document(Base):
    __tablename__ = "document"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey('document.id'), nullable=False)
    start: Mapped[INTEGER] = mapped_column(INTEGER, nullable=False)
    end: Mapped[INTEGER] = mapped_column(INTEGER, nullable=False)
    vector: Mapped[FLOAT] = mapped_column(Vector(2), nullable=False)

    document = relationship("Document")
