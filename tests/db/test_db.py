import sys
import os
from sqlalchemy import insert, select, delete
from datetime import datetime, timezone

from sqlalchemy.engine import Connection


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ucr_chatbot.db.models import *

def test_add_new_course(db: Connection):
    """tests the add_new_course wrapper function"""
    add_new_course(id = 100, name = 'CS100')
    s = select(Courses).where(Courses.id == 100 , Courses.name=='CS100')
    result = db.execute(s)

    answer = None
    for row in result:
        answer = row
    assert answer is not None
    assert answer == (100,'CS100',)

def test_add_course_integrity(capsys):
    """tests the add_new_course function exception occurs when error"""
    add_new_course(id = 100, name = 'CS100')
    captured = capsys.readouterr()
    assert "Error adding new course.\n\n" in captured.out
    



def test_add_new_user(db: Connection):
    """tests the add_new_user wrapper function"""
    add_new_user("test@ucr.edu", "John", "Doe")
    s = select(Users).where(Users.email=='test@ucr.edu', Users.first_name=='John', Users.last_name=='Doe')
    result = db.execute(s)

    answer = None
    for row in result:
        answer = row
    assert answer is not None
    assert answer == ('test@ucr.edu', 'John', 'Doe')


def test_add_user_integrity(capsys):
    """tests the add_new_user function exception occurs when error"""
    add_new_user("test@ucr.edu", "John", "Doe")
    captured = capsys.readouterr()
    assert "Error adding new user." in captured.out

def test_print_users(capsys):
    """tests the print_users wrapper function"""
    print_users()
    captured = capsys.readouterr()
    print(repr(captured.out)) 
    assert captured.out == '+--------------+------+-----+\n| 0            | 1    | 2   |\n|--------------+------+-----|\n| test@ucr.edu | John | Doe |\n+--------------+------+-----+\n'



def test_insert_participates(db: Connection):
    """tests if the relationship between a user and a course can be added and selected out of db"""


    stmt = insert(ParticipatesIn).values(email = 'test@ucr.edu', course_id = 100, role='Student')
    db.execute(stmt)
    db.commit()


    s = select(ParticipatesIn).where(ParticipatesIn.email=='test@ucr.edu', ParticipatesIn.course_id==100, ParticipatesIn.role == 'Student')
    result = db.execute(s)

    answer = None
    for row in result:
        answer = row
    assert answer is not None
    assert answer == ('test@ucr.edu', 100, 'Student')

def test_print_participation(capsys):
    """tests the print_participation wrapper function"""
    print_participation()
    captured = capsys.readouterr()
    print(repr(captured.out))  
    assert captured.out == "+--------------+-----+---------+\n| 0            |   1 | 2       |\n|--------------+-----+---------|\n| test@ucr.edu | 100 | Student |\n+--------------+-----+---------+\n"



def test_insert_conversations(db: Connection): 
    """tests if a conversation can be inserted and selected out of db"""


    stmt = insert(Conversations).values(id =100, initiated_by = 'test@ucr.edu', course_id = 100)
    db.execute(stmt)
    db.commit()


    s = select(Conversations).where(Conversations.id ==100, Conversations.initiated_by == 'test@ucr.edu', Conversations.course_id == 100)
    result = db.execute(s)

    answer = None
    for row in result:
        answer = row
    assert answer is not None
    assert answer == (100, 'test@ucr.edu',100)

def test_insert_messages(db: Connection): 
    """tests if a message can be inserted and selected out of db"""
    
    curr_time = datetime.now(timezone.utc)
    stmt = insert(Messages).values(id = 100, body = "testing", timestamp = curr_time, type=MessageType.STUDENT_MESSAGES, conversation_id = 100, written_by = 'test@ucr.edu')
    db.execute(stmt)
    db.commit()


    s = select(Messages).where(Messages.id == 100,Messages.body == "testing", Messages.type==MessageType.STUDENT_MESSAGES, Messages.conversation_id == 100, Messages.written_by == 'test@ucr.edu')
    result = db.execute(s)

    answer = None
    for row in result:
        answer = row
    assert answer is not None
    assert answer[0] ==(100)

def test_add_new_document(db: Connection):
    """tests the add_new_documents wrapper function"""
    add_new_document(file_path="slide_1.pdf", course_id=100)
    s = select(Documents).where(Documents.file_path=="slide_1.pdf", Documents.course_id==100)
    result = db.execute(s)

    answer = None
    for row in result:
        answer = row
    assert answer is not None
    assert answer == ("slide_1.pdf", 100)

def test_add_document_integrity(capsys):
    """tests the add_new_document function exception occurs when error"""
    add_new_document(file_path="slide_1.pdf", course_id=100)
    captured = capsys.readouterr()
    assert "Error adding document. Course id must exist.\n\n" in captured.out

def test_insert_segments(db: Connection): 
    """tests if a segment can be inserted and selected out of db"""
    stmt = insert(Segments).values(id =100, text = "hello", document_id="slide_1.pdf")
    db.execute(stmt)
    db.commit()


    s = select(Segments).where(Segments.id==100, Segments.text=="hello", Segments.document_id=="slide_1.pdf")
    result = db.execute(s)

    answer = None
    for row in result:
        answer = row
    assert answer is not None
    assert answer ==(100,"hello", "slide_1.pdf")

def test_insert_embeddings(db: Connection): 
    """tests if an embedding can be inserted and selected out of db"""
    emb = [0,0,0,0.,0,0,0,0,0,0]
    stmt = insert(Embeddings).values(id =100, vector=emb, segment_id=100)
    db.execute(stmt)
    db.commit()


    s = select(Embeddings).where(Embeddings.id ==100)
    result = db.execute(s)

    answer = None
    for row in result:
        answer = row
    assert answer is not None
    assert answer[0] ==(100)

def test_insert_reference(db: Connection): 
    """tests if a reference between a message and segment can be inserted and selected out of db"""
    stmt = insert(References).values(message =100, segment=100)
    db.execute(stmt)
    db.commit()


    s = select(References).where(References.message==100, References.segment==100)
    result = db.execute(s)

    answer = None
    for row in result:
        answer = row
    assert answer is not None
    assert answer == (100,100)

def test_delete_reference(db: Connection): 
    """tests if a reference between a message and segment can be deleted out of db"""
    stmt = delete(References).where(References.message==100, References.segment==100)
    db.execute(stmt)
    db.commit()

    s = select(References).where(References.message==100, References.segment==100)
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0

def test_delete_embeddings(db: Connection): 
    """tests if an embedding can be deleted from db"""
    stmt = delete(Embeddings).where(Embeddings.id ==100, Embeddings.vector==[0,0,0,0,0,0,0,0,0,0], Embeddings.segment_id==100)
    db.execute(stmt)
    db.commit()

    s = select(Embeddings).where(Embeddings.id ==100)
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0

def test_delete_segments(db: Connection):
    """tests if a segment can be deleted from db"""
    stmt = delete(Segments).where(Segments.id==100, Segments.text=="hello", Segments.document_id=="slide_1.pdf")
    db.execute(stmt)
    db.commit()

    s = select(Segments).where(Segments.id==100, Segments.text=="hello", Segments.document_id=="slide_1.pdf")
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0


def test_delete_documents(db: Connection):
    """tests if a document can be deleted from db"""
    stmt = delete(Documents).where(Documents.file_path=="slide_1.pdf", Documents.course_id==100)
    db.execute(stmt)
    db.commit()

    s = select(Documents).where(Documents.file_path=="slide_1.pdf", Documents.course_id==100)
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0



def test_delete_messages(db: Connection):
    """tests if a message can be deleted from db"""
    stmt = delete(Messages).where(Messages.id == 100,Messages.body == "testing", Messages.type==MessageType.STUDENT_MESSAGES, Messages.conversation_id == 100, Messages.written_by == 'test@ucr.edu')
    db.execute(stmt)
    db.commit()

    s = select(Messages).where(Messages.id == 100,Messages.body == "testing", Messages.type==MessageType.STUDENT_MESSAGES, Messages.conversation_id == 100, Messages.written_by == 'test@ucr.edu')
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0

def test_delete_conversations(db: Connection):
    """tests if a conversation can be deleted from db"""
    stmt = delete(Conversations).where(Conversations.id ==100, Conversations.initiated_by == 'test@ucr.edu', Conversations.course_id == 100)
    db.execute(stmt)
    db.commit()

    s = select(Conversations).where(Conversations.id ==100, Conversations.initiated_by == 'test@ucr.edu', Conversations.course_id == 100)
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0


def test_delete_participates(db: Connection):
    """tests if a user course relationship can be deleted from db"""
    stmt = delete(ParticipatesIn).where(ParticipatesIn.email=='test@ucr.edu', ParticipatesIn.course_id == 100)
    db.execute(stmt)
    db.commit()

    s = select(ParticipatesIn).where(ParticipatesIn.email=='test@ucr.edu', ParticipatesIn.course_id == 100)
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0


def test_delete_course(db: Connection):
    """tests if a course can be deleted from db"""
    stmt = delete(Courses).where(Courses.id==100)
    db.execute(stmt)
    db.commit()

    s = select(Courses).where(Courses.id==100)
    result = db.execute(s)
    result = list(result)
   
    
    assert len(result)==0

def test_delete_user(db: Connection): 
    """tests if a user can be deleted from db"""
    stmt = delete(Users).where(Users.email=='test@ucr.edu', Users.first_name=='John', Users.last_name=='Doe')
    db.execute(stmt)
    db.commit()

    s = select(Users).where(Users.email=='test@ucr.edu', Users.first_name=='John', Users.last_name=='Doe')
    result = db.execute(s)
    result = list(result)
   
    assert len(result)==0






