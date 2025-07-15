from sqlalchemy import (
    create_engine,
    String,
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    Boolean,
)
from sqlalchemy.orm import declarative_base, mapped_column, relationship, Session
import enum
from pgvector.sqlalchemy import Vector  # type: ignore
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from sqlalchemy.exc import SQLAlchemyError

from typing import Sequence

load_dotenv()

upload_folder: str = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads")


password = os.getenv("DB_PASSWORD")

engine = create_engine(
    f"postgresql+psycopg2://postgres:{password}@127.0.0.1:5432/testing_tutor"
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


# base.metadata.drop_all(engine)
base.metadata.create_all(engine)


def add_new_user(email: str, first_name: str, last_name: str):
    """Adds new user entry to Users table with the given parameters.
    :param email: new user's email address
    :param first_name: new user's first name
    :param last_name: new user's last_name
    """
    with Session(engine) as session:
        try:
            new_user = Users(email=email, first_name=first_name, last_name=last_name)

            session.add_all([new_user])
            session.commit()
        except SQLAlchemyError:
            session.rollback()


def add_new_course(name: str):
    """Adds new course to the Courses table with the given parameters and creates a new upload folder for it.
    :param id: id for course to be added
    :param name: name of course to be added
    """
    with Session(engine) as session:
        try:
            new_course = Courses(name=name)

            session.add(new_course)
            session.commit()

            create_upload_folder(getattr(new_course, "id"))
        except SQLAlchemyError:
            session.rollback()


def add_new_document(file_path: str, course_id: int):
    """Adds new document to the Documents table with the given parameters.
    :param file_path: path pointing to where new document is stored.
    :param course_id: id for course document was uploaded to.
    """
    with Session(engine) as session:
        try:
            new_document = Documents(
                file_path=file_path,
                course_id=course_id,
            )
            session.add(new_document)
            session.commit()
            print("Document added.")
        except SQLAlchemyError:
            session.rollback()
            print("Document not added.")


def set_document_inactive(file_path: str):
    """Sets the is_active column of a document entry to false.
    :param file_path: The file path of the document to be set inactive.
    """
    with Session(engine) as session:
        document = session.query(Documents).filter_by(file_path=file_path).first()
        if document:
            document.is_active = False  # type: ignore
            session.commit()


def get_active_documents() -> list[str]:
    """Returns list of the file paths for all active documents in the database.
    :return: list of the file paths for all active documents:
    """
    with Session(engine) as session:
        active_documents = session.query(Documents).filter_by(is_active=True)
        file_paths: list[str] = []

        for doc in active_documents:
            file_paths.append(getattr(doc, "file_path"))

        return file_paths


def store_segment(segment_text: str, file_path: str) -> int:
    """Creates new Segments instance and stores it into Segments table.
    :param segment_text: The segment text to be added.
    :param file_path: The file path of the document the segment was parsed from.
    :return: An int representing the segment ID.
    """
    with Session(engine) as session:
        # document = session.query(Documents).filter_by(file_path=file_path).first()
        new_segment = Segments(
            text=segment_text,
            document_id=file_path,
        )
        session.add(new_segment)
        session.flush()
        segment_id = int(getattr(new_segment, "id"))
        session.commit()

        return segment_id


def store_embedding(embedding: Sequence[float], segment_id: int):
    """Creates new Embeddings instance and stores it into Embeddings table.
    :param embedding: List of floats representing the vector embedding.
    :param segment_id: ID for the segment the vector embedding represents.
    """
    with Session(engine) as session:
        # segment = session.query(Segments).filter_by(id=segment_id).first()
        try:
            new_embedding = Embeddings(
                vector=embedding,
                segment_id=segment_id,
            )
            session.add(new_embedding)
            session.commit()
        except SQLAlchemyError:
            session.rollback()


def create_upload_folder(course_id: int):
    """Creates a folder named after the course id within the uploads folder.
    :param course_id: name of the folder to be created
    """
    if not os.path.isdir(upload_folder):
        os.makedirs(upload_folder)

    os.makedirs(os.path.join(upload_folder, str(course_id)))
