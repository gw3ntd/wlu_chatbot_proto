import argparse

from ucr_chatbot.db.models import *
from sqlalchemy import inspect

inspector = inspect(engine)

def parse():
  parser = argparse.ArgumentParser()
  parser.add_argument("action")
  parser.add_argument("--force", action="store_true")

  args = parser.parse_args()
  print(args)
  if args.action == "initialize":
    initialize(args.force)
  elif args.action == 'mock':
    print("Mock data added to database.")

def initialize(force_init: bool):
  if not inspector.has_table("Users"):
    base.metadata.create_all(engine)
    print("Database initialized.")
  elif inspector.has_table("Users") and force_init:
    base.metadata.drop_all(engine)
    base.metadata.create_all(engine)
    print("Database cleared and initialized.")
  elif inspector.has_table("Users") and not force_init:
    print("Database already initialized.")
  

if __name__ == "__main__":
  parse()