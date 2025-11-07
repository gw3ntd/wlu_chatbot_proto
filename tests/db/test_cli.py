import shlex
from sqlalchemy import select, inspect
from sqlalchemy.orm import Session
from sqlalchemy.engine import Connection

from flask import Flask

from wlu_chatbot.db.models import base, get_engine, User, Course, ParticipatesIn
from wlu_chatbot.db.cli import main, initialize, mock


def test_main(capsys, app: Flask):
  """Tests that arguments are parsed corrrectly in main"""
  base.metadata.drop_all(get_engine())
  main(shlex.split('initialize'))
  output = capsys.readouterr().out.rstrip()
  assert "Database initialized." in output

def test_initialize(app: Flask):
  """Tests that dataabase is initialized correctly"""
  base.metadata.drop_all(get_engine())
  initialize(False)
  inspector = inspect(get_engine())
  assert inspector.has_table("users") == True

def test_initialize_force(app: Flask):
  """Tests that database is initialized correctly with --force"""
  base.metadata.drop_all(get_engine())
  initialize(False)
  initialize(True)
  inspector = inspect(get_engine())
  assert inspector.has_table("users") == True

def test_mock(db: Connection, app: Flask):
  """Tests that mock data is added correctly to database"""
  initialize(True)
  mock(False)
  s = select(Course).where(Course.id==1)
  result = db.execute(s)

  answer = None
  for row in result:
    answer = row
  assert answer.name == 'CS010C'

  s = select(User).where(User.email=='test001@westliberty.edu')
  result = db.execute(s)

  answer = None
  for row in result:
    answer = row
  assert answer.email == 'test001@westliberty.edu'


def test_create_user(app: Flask):
  main(shlex.split("create user test001@westliberty.edu test"))
  with Session(get_engine()) as sess:
    users = sess.query(User).all()
    assert len(users) == 1
    assert users[0].email == "test001@westliberty.edu"

def test_create_course(app: Flask):
  main(shlex.split("create course \"Calculus 2\""))
  with Session(get_engine()) as sess:
    courses = sess.query(Course).all()
    assert len(courses) == 1
    assert courses[0].name == "Calculus 2"

def test_create_participates_in(app: Flask):
  with Session(get_engine()) as sess:
    user = User(email="test009@westliberty.edu")
    user.set_password("test")
    course = Course(name="Calculus 3")
    sess.add(user)
    sess.add(course)
    sess.commit()
    course_id = course.id

  main(shlex.split(f"create participates_in test009@westliberty.edu {course_id} assistant"))
  with Session(get_engine()) as sess:
    part_ins = sess.query(ParticipatesIn).where().all()
    assert len(part_ins) == 1
    assert part_ins[0].course_id == course_id
    assert part_ins[0].email == "test009@westliberty.edu"