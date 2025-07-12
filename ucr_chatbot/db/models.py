from sqlalchemy import (
    create_engine,
    String,
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    Boolean
)
from sqlalchemy.orm import declarative_base, mapped_column, relationship, Session
import enum
from pgvector.sqlalchemy import Vector  # type: ignore
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from sqlalchemy.exc import IntegrityError

from tabulate import tabulate

load_dotenv()


password = os.getenv("DB_PASSWORD")

engine = create_engine(
    f"postgresql+psycopg://postgres:{password}@127.0.0.1:5432/testing_tutor"
)

base = declarative_base()


class MessageType(enum.Enum):
    """Manditory choices for Message type"""

    ASSISTANT_MESSAGES = "AssistantMessage"
    STUDENT_MESSAGES = "StudentMessage"
    BOT_MESSAGES = "BotMessage"


class Users(base):
    """Represents a User and their profile information"""

    __tablename__ = "Users"
    email = Column(String, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)

    conversations = relationship("Conversations", back_populates="user", uselist=True)
    messages = relationship("Messages", back_populates="user", uselist=True)
    participates = relationship("ParticipatesIn", back_populates="user")


class ParticipatesIn(base):
    """Represents the enrollment between users and courses"""

    __tablename__ = "ParticipatesIn"
    email = Column(String, ForeignKey("Users.email"), primary_key=True)
    course_id = Column(Integer, ForeignKey("Courses.id"), primary_key=True)
    role = Column(String, nullable=False)

    user = relationship("Users", back_populates="participates")
    course = relationship("Courses", back_populates="participates")


class Conversations(base):
    """Represents the conversations a user can initiate"""

    __tablename__ = "Conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    initiated_by = Column(String, ForeignKey("Users.email"), nullable=False)
    course_id = Column(Integer, ForeignKey("Courses.id"), nullable=False)

    course = relationship("Courses", back_populates="conversations")
    messages = relationship("Messages", back_populates="conversation", uselist=True)
    user = relationship("Users", back_populates="conversations")


class Courses(base):
    """Represents a course"""

    __tablename__ = "Courses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    conversations = relationship("Conversations", back_populates="course", uselist=True)
    documents = relationship("Documents", back_populates="course", uselist=True)
    participates = relationship("ParticipatesIn", back_populates="course")


class Documents(base):
    """Represents a stored file to be references with queries"""

    __tablename__ = "Documents"
    file_path = Column(String, primary_key=True)
    course_id = Column(Integer, ForeignKey("Courses.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    course = relationship("Courses", back_populates="documents")
    segments = relationship("Segments", back_populates="document", uselist=True)


class Segments(base):
    """Represents a section of a document to be embedded"""

    __tablename__ = "Segments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String)
    document_id = Column(String, ForeignKey("Documents.file_path"), nullable=False)

    document = relationship("Documents", back_populates="segments")
    embeddings = relationship("Embeddings", back_populates="segment", uselist=True)


class Messages(base):
    """Represents a specific message between a user and LLM"""

    __tablename__ = "Messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    body = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    type = Column(Enum(MessageType))
    conversation_id = Column(Integer, ForeignKey("Conversations.id"), nullable=False)
    written_by = Column(String, ForeignKey("Users.email"), nullable=False)

    conversation = relationship("Conversations", back_populates="messages")
    user = relationship("Users", back_populates="messages")


class Embeddings(base):
    """Represents the embedding of a segment"""

    __tablename__ = "Embeddings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vector = mapped_column(Vector)
    segment_id = Column(Integer, ForeignKey("Segments.id"), nullable=False)

    segment = relationship("Segments", back_populates="embeddings")


class References(base):
    """Represents the relationship between a message and referenced segments"""

    __tablename__ = "References"
    message = Column(Integer, ForeignKey("Messages.id"), primary_key=True)
    segment = Column(Integer, ForeignKey("Segments.id"), primary_key=True)


base.metadata.drop_all(engine)
base.metadata.create_all(engine)


def add_new_user(email: str, first_name: str, last_name: str):
    """Adds new user entry to Users table with the given parameters."""
    with Session(engine) as session:
        try:
            new_user = Users(email=email, first_name=first_name, last_name=last_name)

            session.add_all([new_user])
            session.commit()
            print("New user added successfully.\n")
        except IntegrityError:
            session.rollback()
            print("Error adding new user.\n")


def add_new_course(id: int, name: str):
    """Adds new course to the Courses table with the given parameters."""
    with Session(engine) as session:
        try:
            new_course = Courses(
                id=id,
                name=name,
            )

            session.add(new_course)
            session.commit()
            print("New course added successfully.\n")
        except IntegrityError:
            session.rollback()
            print("Error adding new course.\n")


def add_new_document(file_path: str, course_id: int):
    """Adds new document to the Documents table with the given parameters."""
    with Session(engine) as session:
        try:
            new_document = Documents(
                file_path=file_path,
                course_id=course_id,
            )
            session.add(new_document)
            session.commit()
            print("Document added successfully.\n")
        except IntegrityError:
            session.rollback()
            print("Error adding document. Course id must exist.\n")

def set_document_inactive(file_path: str):
    with Session(engine) as session:
        document = session.query(Documents).filter_by(file_path=file_path).first()
        document.is_active = False
        session.commit()


def print_users():
    """prints all users and their information"""
    with Session(engine) as session:
        all_entries = session.query(Users).all()
        rows: list[typing.Tuple[Column[str], Column[str], Column[str]]] = []

        for row in all_entries:
            rows.append((row.email, row.first_name, row.last_name))
        print(tabulate(rows, headers="keys", tablefmt="psql"))


import typing


def print_participation():
    """prints all relationships between users and courses"""
    with Session(engine) as session:
        all_entries = session.query(ParticipatesIn).all()
        rows: list[typing.Tuple[Column[str], Column[int], Column[str]]] = []

        for row in all_entries:
            rows.append((row.email, row.course_id, row.role))
        print(tabulate(rows, headers="keys", tablefmt="psql"))
