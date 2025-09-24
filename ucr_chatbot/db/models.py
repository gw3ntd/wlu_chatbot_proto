from sqlalchemy import (
    Engine,
    create_engine,
    String,
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    UniqueConstraint,
)

from sqlalchemy.orm import declarative_base, mapped_column, relationship, Session
import enum
from pgvector.sqlalchemy import Vector  # type: ignore
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from typing import cast
import secrets
import string
from pathlib import PurePath


from flask_login import UserMixin  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash
from flask import g
import markdown


from ucr_chatbot.config import app_config


def get_engine() -> Engine:
    """Gets the database engine instance. Must be called from within a request context."""
    if g.get("_db_engine") is None:
        g._db_engine = create_engine(
            f"""postgresql+psycopg2://{app_config.DB_USER}:{app_config.DB_PASSWORD}@{app_config.DB_URL}/{app_config.DB_NAME}"""
        )
    return g._db_engine


base = declarative_base()


class MessageType(str, enum.Enum):
    """Manditory choices for Message type"""

    ASSISTANT_MESSAGE = "ASSISTANT_MESSAGE"
    STUDENT_MESSAGE = "STUDENT_MESSAGE"
    BOT_MESSAGE = "BOT_MESSAGE"


class User(base, UserMixin):
    """Represents a User and their profile information"""

    __tablename__ = "users"
    email = Column(String, primary_key=True)
    password_hash = Column(String(255), nullable=False)

    conversations = relationship("Conversation", back_populates="user", uselist=True)
    messages = relationship("Message", back_populates="user", uselist=True)
    participates_in = relationship("ParticipatesIn", back_populates="user")

    def set_password(self, password: str):
        """Takes a plain text password and uses generate_password_hash
        to create a hashed version of the password. Then it stores the
        hashed password in the password_hash attribute of the user
        instance.
        :param password: plain text password
        :type password: str

        """
        print("User added -> email: " + self.email + " password: " + password)
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Takes a plain text password and uses check_password_hash
        to compare the plain version with the stored hashed
        password. It returns True if the password matches the hash.
        :param password: plain text password
        :type password: str
        :return: True if the password matches the hash,
        False if otherwise
        :rtype: bool
        """
        return check_password_hash(
            cast(str, self.password_hash), generate_password_hash(password)
        )

    def get_id(self) -> str:
        """Return the ID used for Flask-Login session tracking."""
        return str(self.email)  # Flask-Login uses this to store user ID in session


class ParticipatesIn(base):
    """Represents the enrollment between users and courses"""

    __tablename__ = "participates_in"
    email = Column(String, ForeignKey("users.email"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)
    role = Column(String, nullable=False)

    user = relationship("User", back_populates="participates_in")
    course = relationship("Course", back_populates="participates_in")


class ConversationState(str, enum.Enum):
    CHATBOT = "CHATBOT"
    REDIRECTED = "REDIRECTED"
    RESOLVED = "RESOLVED"


class Conversation(base):
    """Represents the conversations a user can initiate"""

    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    initiated_by = Column(String, ForeignKey("users.email"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    state: ConversationState = Column(
        Enum(ConversationState),
        nullable=False,
        default=ConversationState.CHATBOT,  # type: ignore
    )
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)

    course = relationship("Course", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", uselist=True)
    user = relationship("User", back_populates="conversations")


class Course(base):
    """Represents a course"""

    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    conversations = relationship("Conversation", back_populates="course", uselist=True)
    documents = relationship("Document", back_populates="course", uselist=True)
    participates_in = relationship("ParticipatesIn", back_populates="course")
    consent_forms = relationship("ConsentForm", back_populates="course", uselist=True)


class ConsentForm(base):
    """Represents a consent form to be filled out before accessing the AI Tutor."""

    __tablename__ = "consent_forms"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    body = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    course = relationship("Course", back_populates="consent_forms")
    consents = relationship(
        "Consent",
        backref="consent_form",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def body_as_html(self):
        """Returns the HTML version of this consent forms body."""
        return markdown.markdown(str(self.body))


class Consent(base):
    """Represents a user's consenting to a form"""

    __tablename__ = "consents"
    consent_form_id = Column(
        Integer, ForeignKey("consent_forms.id", ondelete="CASCADE"), primary_key=True
    )
    user_email = Column(String, ForeignKey("users.email"), primary_key=True)


class Document(base):
    """Represents a stored file to be references with queries"""

    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_hash = Column(String(64), nullable=False)
    file_extension = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("file_hash", "course_id", name="_customer_location_uc"),
    )
    course = relationship("Course", back_populates="documents")
    segments = relationship(
        "Segment", back_populates="document", uselist=True, cascade="all, delete-orphan"
    )

    @property
    def full_file_path(self) -> PurePath:
        """The location at which this document is stored."""
        return PurePath(str(self.course_id), f"{self.file_hash}")

    @property
    def name_with_extension(self) -> str:
        """The name of this file with its file extension"""
        return f"{self.name}.{self.file_extension}"


class Segment(base):
    """Represents a section of a document to be embedded"""

    __tablename__ = "segments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String)
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )

    document = relationship("Document", back_populates="segments")
    embeddings = relationship(
        "Embedding",
        back_populates="segment",
        uselist=True,
        cascade="all, delete-orphan",
    )


class Message(base):
    """Represents a specific message between a user and LLM"""

    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    body = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    type = Column(Enum(MessageType))
    conversation_id = Column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    written_by = Column(String, ForeignKey("users.email"), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")


class Limit(base):
    """Represents the per-user limit for LLM access"""

    __tablename__ = "limits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    maximum_number_of_uses = Column(Integer)
    time_span_seconds = Column(Integer)


class Embedding(base):
    """Represents the embedding of a segment"""

    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vector = mapped_column(Vector)
    segment_id = Column(
        Integer, ForeignKey("segments.id", ondelete="CASCADE"), nullable=False
    )

    segment = relationship("Segment", back_populates="embeddings")


class Reference(base):
    """Represents the relationship between a message and referenced segments"""

    __tablename__ = "references"
    message_id = Column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True
    )
    segment_id = Column(
        Integer, ForeignKey("segments.id", ondelete="CASCADE"), primary_key=True
    )


def add_new_user(email: str):
    """Adds new user entry to users table with the given parameters.
    Must be called within a request context.
    :param email: new user's email address
    """
    with Session(get_engine()) as session:
        try:
            alphabet = string.ascii_letters + string.digits
            password = "".join(secrets.choice(alphabet) for _ in range(10))
            new_user = User(
                email=email,
                password_hash="",
            )
            new_user.set_password(password)

            session.add(new_user)
            session.commit()
        except SQLAlchemyError:
            session.rollback()


def add_user_to_course(email: str, course_id: int, role: str):
    """Adds a user to the specified course.
    Must be called within a request context.

    :param email: The email for the user to be added.
    :param course_id: The course the user will be added to.
    :param role: The role of the user in the course."""
    with Session(get_engine()) as session:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            add_new_user(email)

        participation_status = (
            session.query(ParticipatesIn)
            .filter(
                ParticipatesIn.email == email,
                ParticipatesIn.course_id == course_id,
                ParticipatesIn.role == role,
            )
            .first()
        )
        if not participation_status:
            new_participation = ParticipatesIn(
                email=email, course_id=course_id, role=role
            )
            session.add(new_participation)
            session.commit()
            print("User added to course.")


def add_new_course(name: str):
    """Adds new course to the Course table with the given parameters and creates a new upload folder for it.
    Must be called within a request context.

    :param id: id for course to be added
    :param name: name of course to be added
    """
    with Session(get_engine()) as session:
        try:
            new_course = Course(name=name)

            session.add(new_course)
            session.commit()

        except SQLAlchemyError:
            session.rollback()
