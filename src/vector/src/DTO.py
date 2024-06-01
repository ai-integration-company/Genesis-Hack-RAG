from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class Userbd(BaseModel):
    document_id: UUID
    start: int
    end: int
    vector: List[float]


class Vector(BaseModel):
    vector: List[float]


class KNN(Vector):
    k: int
