import sys
import os
from sqlalchemy import insert, select, delete
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ucr_chatbot.db.models import *

def test_insert_course(db): #tests insertion into Courses table
    stmt = insert(Courses).values(id = 100, name = 'CS100')
    db.execute(stmt)
    db.commit()


    s = select(Courses).where(Courses.id == 100 , Courses.name=='CS100')
    result = db.execute(s)

    for row in result:
        answer = row
    
    assert answer == (100,'CS100',)





def test_insert_user(db): #tests insertion into User table
    stmt = insert(Users).values(email = 'test@ucr.edu', first_name = 'John', last_name = 'Doe')
    db.execute(stmt)
    db.commit()


    s = select(Users).where(Users.email=='test@ucr.edu', Users.first_name=='John', Users.last_name=='Doe')
    result = db.execute(s)
    print("enters")
    print(type(result))
    for row in result:
        answer = row
    
    assert answer == ('test@ucr.edu', 'John', 'Doe')

def test_insert_participates(db): #tests insertion into User table
    print("Running test_insert_participates")

    stmt = insert(ParticipatesIn).values(email = 'test@ucr.edu', course_id = 100, role='Student')
    db.execute(stmt)
    db.commit()


    s = select(ParticipatesIn).where(ParticipatesIn.email=='test@ucr.edu', ParticipatesIn.course_id==100, ParticipatesIn.role == 'Student')
    result = db.execute(s)
    print("enters")
    print(type(result))
    for row in result:
        answer = row
    
    assert answer == ('test@ucr.edu', 100, 'Student')

def test_insert_conversations(db): #tests insertion into User table


    stmt = insert(Conversations).values(id =100, initiated_by = 'test@ucr.edu', course_id = 100)
    db.execute(stmt)
    db.commit()


    s = select(Conversations).where(Conversations.id ==100, Conversations.initiated_by == 'test@ucr.edu', Conversations.course_id == 100)
    result = db.execute(s)
    print("enters")
    print(type(result))
    for row in result:
        answer = row
    
    assert answer == (100, 'test@ucr.edu',100)

def test_insert_messages(db): #tests insertion into User table
    curr_time = datetime.now(timezone.utc).replace(tzinfo=None)
    stmt = insert(Messages).values(id = 100, body = "testing", timestamp = curr_time, type="StudentMessages", conversation_id = 100, written_by = 'test@ucr.edu')
    db.execute(stmt)
    db.commit()


    s = select(Messages).where(Messages.id == 100,Messages.body == "testing", Messages.type=="StudentMessages", Messages.conversation_id == 100, Messages.written_by == 'test@ucr.edu')
    result = db.execute(s)
    print("enters")
    print(type(result))
    for row in result:
        answer = row
    
    assert answer ==(100, 'testing', curr_time, 'StudentMessages', 100, 'test@ucr.edu')

def test_insert_documents(db): #tests insertion into User table
    stmt = insert(Documents).values(file_path="slide_1.pdf", course_id=100)
    db.execute(stmt)
    db.commit()


    s = select(Documents).where(Documents.file_path=="slide_1.pdf", Documents.course_id==100)
    result = db.execute(s)
    print("enters")
    print(type(result))
    for row in result:
        answer = row
    
    assert answer ==("slide_1.pdf", 100)

def test_insert_segments(db): #tests insertion into User table
    stmt = insert(Segments).values(id =100, text = "hello", document="slide_1.pdf")
    db.execute(stmt)
    db.commit()


    s = select(Segments).where(Segments.id==100, Segments.text=="hello", Segments.document=="slide_1.pdf")
    result = db.execute(s)
    print("enters")
    print(type(result))
    for row in result:
        answer = row
    
    assert answer ==(100,"hello", "slide_1.pdf")

def test_insert_embeddings(db): #tests insertion into User table
    emb = ([0.,0.,0.,0.,0.,0.,0.,0.,0.,0.])
    stmt = insert(Embeddings).values(id =100, vector=emb, segment_id=100)
    db.execute(stmt)
    db.commit()


    s = select(Embeddings).where(Embeddings.id ==100, Embeddings.vector==emb, Embeddings.segment_id==100)
    result = db.execute(s)
    print("enters")
    print(type(result))
    for row in result:
        answer = row
    
    assert answer ==(100,emb, 100)

def test_delete_embeddings(db): #tests deleting from User table
    stmt = delete(Embeddings).where(Embeddings.id ==100, Embeddings.vector==[0,0,0,0,0,0,0,0,0,0], Embeddings.segment_id==100)
    db.execute(stmt)
    db.commit()

    s = select(Segments).where(Embeddings.id ==100, Embeddings.vector==[0,0,0,0,0,0,0,0,0,0], Embeddings.segment_id==100)
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0

def test_delete_segments(db): #tests deleting from User table
    stmt = delete(Segments).where(Segments.id==100, Segments.text=="hello", Segments.document=="slide_1.pdf")
    db.execute(stmt)
    db.commit()

    s = select(Segments).where(Segments.id==100, Segments.text=="hello", Segments.document=="slide_1.pdf")
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0


def test_delete_documents(db): #tests deleting from User table
    stmt = delete(Documents).where(Documents.file_path=="slide_1.pdf", Documents.course_id==100)
    db.execute(stmt)
    db.commit()

    s = select(Documents).where(Documents.file_path=="slide_1.pdf", Documents.course_id==100)
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0



def test_delete_messages(db): #tests deleting from User table
    stmt = delete(Messages).where(Messages.id == 100,Messages.body == "testing", Messages.type=="StudentMessages", Messages.conversation_id == 100, Messages.written_by == 'test@ucr.edu')
    db.execute(stmt)
    db.commit()

    s = select(Messages).where(Messages.id == 100,Messages.body == "testing", Messages.type=="StudentMessages", Messages.conversation_id == 100, Messages.written_by == 'test@ucr.edu')
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0

def test_delete_conversations(db): #tests deleting from User table
    stmt = delete(Conversations).where(Conversations.id ==100, Conversations.initiated_by == 'test@ucr.edu', Conversations.course_id == 100)
    db.execute(stmt)
    db.commit()

    s = select(Conversations).where(Conversations.id ==100, Conversations.initiated_by == 'test@ucr.edu', Conversations.course_id == 100)
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0


def test_delete_participates(db): #tests deleting from User table
    stmt = delete(ParticipatesIn).where(ParticipatesIn.email=='test@ucr.edu', ParticipatesIn.course_id == 100)
    db.execute(stmt)
    db.commit()

    s = select(ParticipatesIn).where(ParticipatesIn.email=='test@ucr.edu', ParticipatesIn.course_id == 100)
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0


def test_delete_course(db): #tests deleting from Courses table
    stmt = delete(Courses).where(Courses.id==100)
    db.execute(stmt)
    db.commit()

    s = select(Courses).where(Courses.id==100)
    result = db.execute(s)
    result = list(result)
   
    
    assert len(result)==0

def test_delete_user(db): #tests deleting from User tabl
    stmt = delete(Users).where(Users.email=='test@ucr.edu', Users.first_name=='John', Users.last_name=='Doe')
    db.execute(stmt)
    db.commit()

    s = select(Users).where(Users.email=='test@ucr.edu', Users.first_name=='John', Users.last_name=='Doe')
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0




