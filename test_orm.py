from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass


from sqlalchemy.orm import Mapped
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import String, Integer
from typing import Optional, List
class Student(Base):
    __tablename__ ="students"
    sid: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    gpa: Mapped[float]
    best_friend: Mapped[Optional["Student"]] = mapped_column(Integer, ForeignKey("students.sid"))
    good_friends: Mapped[List["Student"]] = relationship("student")
    def __repr__(self):
        return f"Student(sid={self.sid!r}, name={self.name!r})"
    

from sqlalchemy import create_engine
engine = create_engine(
    "postgresql+psycopg2://localhost:5432/postgres",

)
Base.metadata.create_all(engine, checkfirst=True)


from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, insert, select


with Session(engine) as session:
    result = session.scalars(select(Student).order_by(Student.sid))
    print(result.all()[-1].best_friend)