from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.models import Base

T = TypeVar("T", bound=Base)

class AsyncBaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[T]:
        """Fetch a single record by primary key."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Fetch all records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: dict) -> T:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: T, obj_in: dict) -> T:
        """Update an existing record with a dictionary of changes."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def remove(self, id: Any) -> Optional[T]:
        """Delete a record by primary key."""
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.commit()
        return obj

class UserRepository(AsyncBaseRepository):
    async def get_by_email(self, email: str):
        stmt = select(self.model).where(self.model.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

class PatientRepository(AsyncBaseRepository):
    async def get_by_ahp_id(self, ahp_id: str):
        stmt = select(self.model).where(self.model.ahp_id == ahp_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int):
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
