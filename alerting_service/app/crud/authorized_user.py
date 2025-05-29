from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import AuthorizedUser
from app.schemas.authorized_user import AuthorizedUserCreate
from typing import List, Optional


class CRUDAuthorizedUser:
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[AuthorizedUser]:
        result = await db.execute(select(AuthorizedUser).filter(AuthorizedUser.user_id == user_id))
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: AuthorizedUserCreate) -> AuthorizedUser:
        db_obj = AuthorizedUser(
            user_id=obj_in.user_id,
            description=obj_in.description
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_all(self, db: AsyncSession) -> List[AuthorizedUser]:
        result = await db.execute(select(AuthorizedUser))
        return result.scalars().all()

    async def is_user_authorized(self, db: AsyncSession, *, user_id: str) -> bool:
        user = await self.get_by_user_id(db, user_id=user_id)
        return user is not None


authorized_user = CRUDAuthorizedUser() 