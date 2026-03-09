from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from app.models.models import Base

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[T]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: dict) -> T:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: T, obj_in: dict) -> T:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, id: int) -> T:
        obj = self.db.query(self.model).get(id)
        self.db.delete(obj)
        self.db.commit()
        return obj

class UserRepository(BaseRepository):
    def get_by_email(self, email: str):
        return self.db.query(self.model).filter(self.model.email == email).first()

class PatientRepository(BaseRepository):
    def get_by_ahp_id(self, ahp_id: str):
        return self.db.query(self.model).filter(self.model.ahp_id == ahp_id).first()

    def get_by_user_id(self, user_id: int):
        return self.db.query(self.model).filter(self.model.user_id == user_id).first()
