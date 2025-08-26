import shlex
from sqlalchemy import select, inspect
from sqlalchemy.engine import Connection
import pytest

from flask import Flask

from ucr_chatbot.db.models import base, get_engine, Users, Courses
from ucr_chatbot.db.cli import main, initialize, mock


def test_main(capsys, app):
  """Tests that arguments are parsed corrrectly in main"""
  base.metadata.drop_all(get_engine())
  main(shlex.split('initialize'))
  output = capsys.readouterr().out.rstrip()
  assert "Database initialized." in output

def test_initialize(app):
  """Tests that dataabase is initialized correctly"""
  base.metadata.drop_all(get_engine())
  initialize(False)
  inspector = inspect(get_engine())
  assert inspector.has_table("Users") == True

def test_initialize_force(app):
  """Tests that database is initialized correctly with --force"""
  base.metadata.drop_all(get_engine())
  initialize(False)
  initialize(True)
  inspector = inspect(get_engine())
  assert inspector.has_table("Users") == True

def test_mock(db: Connection, app):
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
