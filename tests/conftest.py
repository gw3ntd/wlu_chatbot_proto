import sys
from pathlib import Path, PurePath
from dataclasses import dataclass

import pytest
from flask import Flask
from sqlalchemy.orm import Session
from sqlalchemy import inspect

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from wlu_chatbot import create_app
from wlu_chatbot.db.models import get_engine, base, User, ParticipatesIn, Course
from wlu_chatbot.api.file_storage import get_storage_service
from wlu_chatbot.config import LLMMode, FileStorageMode


TEST_APP_CONFIG = {
        "TESTING": True,
        "FILE_STORAGE_MODE": FileStorageMode.LOCAL,
        "FILE_STORAGE_PATH": "test_storage",
        "REQUIRE_OAUTH": False,
        "LLM_MODE": LLMMode.TESTING
    }

@pytest.fixture(scope="session", autouse=True)
def check_empty_db():
    """
    Checks if the database is empty before running any tests.
    """

    with create_app(TEST_APP_CONFIG).app_context():

        engine = get_engine()
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        if table_names:
            pytest.exit(
                f"Test database is not empty. The following tables were found: {', '.join(table_names)}. "
                "Please drop the tables before running tests."
            )

@pytest.fixture(scope="function")
def app():
    app = create_app(TEST_APP_CONFIG)
    app.template_folder = str(Path(__file__).resolve().parent.parent / 'wlu_chatbot' / 'templates')

    with app.app_context():
        base.metadata.create_all(get_engine())
        yield app
        base.metadata.drop_all(get_engine())
        get_storage_service().recursive_delete(PurePath(""))

@pytest.fixture
def client(app: Flask):
    return app.test_client()

@pytest.fixture
def storage_service(app: Flask):
    """
    A fixture to directly access the configured StorageService instance.
    """
    yield get_storage_service()


@pytest.fixture
def db(app: Flask):
    connection = get_engine().connect()
    yield connection
    connection.close()


@dataclass
class MockCourse:
    course_id: int
    instructor_email: str
    student_email: str

@pytest.fixture(scope="function")
def mock_course(app: Flask) -> MockCourse:
    mock_course: MockCourse
    with Session(get_engine()) as session:
        mock_course = MockCourse(
            course_id=1,
            instructor_email="instructor@westliberty.edu",
            student_email="student@westliberty.edu",
        )
        session.add(Course(id = 1, name="CS009A"))
        session.add(User(email="instructor@westliberty.edu", password_hash=""))
        session.add(User(email="student@westliberty.edu",  password_hash=""))
        session.add(ParticipatesIn(email="instructor@westliberty.edu", course_id=1, role="instructor"))
        session.add(ParticipatesIn(email="student@westliberty.edu", course_id=1, role="student"))
        session.commit()
    return mock_course

@pytest.fixture(scope="function")
def mock_course2(app: Flask) -> MockCourse:
    mock_course: MockCourse
    with Session(get_engine()) as session:
        mock_course = MockCourse(
            course_id=2,
            instructor_email="instructor2@westliberty.edu",
            student_email="student2@westliberty.edu",
        )
        session.add(Course(id = 2, name="CS009A"))
        session.add(User(email="instructor2@westliberty.edu", password_hash=""))
        session.add(User(email="student2@westliberty.edu",  password_hash=""))
        session.add(ParticipatesIn(email="instructor2@westliberty.edu", course_id=2, role="instructor"))
        session.add(ParticipatesIn(email="student2@westliberty.edu", course_id=2, role="student"))
        session.commit()
    return mock_course