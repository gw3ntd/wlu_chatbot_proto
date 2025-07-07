from sqlalchemy import create_engine, String, Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, mapped_column,  relationship
from datetime import datetime

from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
password = ""
engine = create_engine(f"postgresql+psycopg://postgres:{password}@127.0.0.1:5432/testing_tutor")


base = declarative_base()
class Users(base):
    __tablename__ = "Users"
    email = Column(String,primary_key=True)
    first_name = Column(String)
    last_name = Column(String)

    # conversations = relationship('Conversations', back_populates='Users', uselist=True)
    # messages = relationship('Messages', back_populates='Users', uselist=True)

class ParticipatesIn(base):
    __tablename__ = "ParticipatesIn"
    email = Column(String, ForeignKey("Users.email"), primary_key=True)
    course_id = Column(Integer, ForeignKey("Courses.id"), primary_key=True)
    role = Column(String, nullable = False)

class Conversations(base):
    __tablename__ = "Conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    initiated_by = Column(String, ForeignKey("Users.email"), nullable=False)
    course_id = Column(Integer, ForeignKey("Courses.id"), nullable=False)

    # course = relationship('Courses', back_populates='Conversations')
    # messages = relationship('Messages', back_populates='Conversations', uselist = True)
    # user = relationship('Users', back_populates='Conversations')

class Courses(base):
    __tablename__ = "Courses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    # conversations = relationship('Conversations', back_populates='Courses',uselist=True)
    # documents = relationship('Documents', back_populates='Courses', uselist=True)
class Documents(base):
    __tablename__ = "Documents"
    file_path = Column(String, primary_key=True)
    course_id = Column(Integer, ForeignKey("Courses.id"), nullable=False)

    # course = relationship('Course', back_populates='Documents')

class Segments(base):
    __tablename__ = "Segments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String)
    document = Column(String, ForeignKey("Documents.file_path"), nullable=False)

class Messages(base):
    __tablename__ = "Messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    body = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String) #must be of 3 types num types
    conversation_id = Column(Integer, ForeignKey("Conversations.id"), nullable=False)
    written_by = Column(String, ForeignKey("Users.email"), nullable = False)

    # conversation = relationship('Conversation', back_populates='Messages')
    # user = relationship('Users', back_populates='Messages')

class Embeddings(base):
    __tablename__ = "Embeddings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vector = mapped_column(Vector(10)) #10 just for initial testing
    segment_id = Column(Integer, ForeignKey("Segments.id"), nullable=False)

class References(base):
    __tablename__ = "References"
    message = Column(Integer, ForeignKey("Messages.id"), primary_key=True)
    segment = Column(Integer, ForeignKey("Segments.id"), primary_key=True)


base.metadata.drop_all(engine)
base.metadata.create_all(engine)


#dont cascade  leave as normal
#create script that takes in emails, create dummy password, put into db