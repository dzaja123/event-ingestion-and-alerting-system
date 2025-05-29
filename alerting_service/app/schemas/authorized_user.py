from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AuthorizedUserBase(BaseModel):
    user_id: str
    description: Optional[str] = None


class AuthorizedUserCreate(AuthorizedUserBase):
    pass


class AuthorizedUserRead(AuthorizedUserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True 