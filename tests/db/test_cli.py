import sys
import shlex
import pytest
from pathlib import Path
from sqlalchemy import insert, select, delete, inspect
from sqlalchemy.engine import Connection


from ucr_chatbot.db.models import *
from ucr_chatbot.db.cli import *
from helper_functions import clear_db



def test_main(capsys):
  """Tests that arguments are parsed corrrectly in main"""
  base.metadata.drop_all(engine)
  main(shlex.split('initialize'))
  output = capsys.readouterr().out.rstrip()
  assert "Database initialized." in output

def test_initialize():
  """Tests that dataabase is initialized correctly"""
  base.metadata.drop_all(engine)
  initialize(False)
  inspector = inspect(engine)
  assert inspector.has_table("Users") == True

def test_initialize_force():
  """Tests that database is initialized correctly with --force"""
  base.metadata.drop_all(engine)
  initialize(False)
  initialize(True)
  inspector = inspect(engine)
  assert inspector.has_table("Users") == True

def test_mock(db: Connection):
  """Tests that mock data is added correctly to database"""
  initialize(True)
  mock()
  s = select(Courses).where(Courses.id==1)
  result = db.execute(s)

  answer = None
  for row in result:
    answer = row
  assert answer.name == 'CS010C'

  s = select(Users).where(Users.email=='test001@ucr.edu')
  result = db.execute(s)

  answer = None
  for row in result:
    answer = row
  assert answer.email == 'test001@ucr.edu'
