from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuthorizedUserBase(BaseModel):
    user_id: str
    description: Optional[str] = None


class AuthorizedUserCreate(AuthorizedUserBase):
    pass


class AuthorizedUserRead(AuthorizedUserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime