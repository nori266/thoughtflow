import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func

from db_entities import Thought, User


load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.DEBUG)


class DBActionHandler:
    def __init__(self):
        self.session = self.get_session()

    def add_thought(self, thought):
        try:
            # TODO try except to decorator? or use context manager? what is context manager?
            self.session.add(thought)
            self.session.commit()
        except Exception as e:
            logger.error(e)

    def get_random_note(self) -> Thought:
        try:
            # return a random note which status is not "done"
            thought = self.session.query(Thought).filter(Thought.status != "done").order_by(func.random()).first()
            return thought
        except Exception as e:
            logger.error(e)

    def update_note_status(self, thought: Thought, status):
        try:
            if status != thought.status:
                thought.status = status
                # TODO: add logic to handle date_completed if the status is "done"
                # TODO: write some log to track the status change (maybe don't even store any dates in the Thought table)
                self.session.commit()
        except Exception as e:
            logger.error(e)


    def show_last_n(self, n=10):
        try:
            thoughts = self.session.query(Thought).order_by(Thought.id.desc()).limit(n).all()
            return thoughts
        except Exception as e:
            logger.error(e)

    def add_user(self, username, password, email, is_admin):
        try:
            user = User(username=username, password=password, email=email, is_admin=is_admin)
            self.session.add(user)
            self.session.commit()
        except Exception as e:
            logger.error(e)

    def get_user(self, username):
        try:
            user = self.session.query(User).filter(User.username == username).first()
            return user
        except Exception as e:
            logger.error(e)

    @staticmethod
    def get_session():
        url = os.getenv("DB_URL")
        engine = create_engine(
            url,
            connect_args=dict(host=os.getenv("DB_HOST"), port=3306)
        )
        Session = sessionmaker(bind=engine)
        return Session()
