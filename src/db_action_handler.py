from datetime import datetime, timedelta
import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func

from db_entities import Thought, User
from plot_maker import PlotMaker


load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)


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

    def get_note_by_message_id(self, message_id: int) -> Thought:
        try:
            thought = self.session.query(Thought).filter(Thought.message_id == message_id).first()
            return thought
        except Exception as e:
            logger.error(e)

    def get_random_note(self) -> Thought:
        try:
            # return a random note which status is not "done"
            thought = self.session.query(Thought).filter(Thought.status != "done").order_by(func.random()).first()
            return thought
        except Exception as e:
            logger.error(e)

    def update_note_status(self, message_id: int, status: Optional[str]) -> Thought:
        try:
            thought = self.session.query(Thought).filter(Thought.message_id == message_id).first()
            if status is not None and status != thought.status:
                thought.status = status
                # TODO: add logic to handle date_completed if the status is "done"
                # TODO: write some log to track the status change (maybe don't even store any dates in the Thought table)
                self.session.commit()
            return thought
        except Exception as e:
            logger.error("Error updating note status", e)

    def update_note_category(self, message_id: Optional[int], category: str) -> Thought:
        # Assumes that the new category comes from telegram and message_id is not None
        try:
            thought = self.session.query(Thought).filter(Thought.message_id == message_id).first()
            if category != thought.label:
                thought.label = category
                self.session.commit()
            return thought
        except Exception as e:
            logger.error(e)

    def update_note_urgency(self, message_id: Optional[int], urgency: str):
        if message_id is None:
            return
        try:
            thought = self.session.query(Thought).filter(Thought.message_id == message_id).first()
            if urgency != thought.urgency:
                thought.urgency = urgency
                self.session.commit()
        except Exception as e:
            logger.error(e)

    def update_note_eta(self, message_id: Optional[int], eta: str):
        if message_id is None:
            return
        try:
            thought = self.session.query(Thought).filter(Thought.message_id == message_id).first()
            if eta != thought.eta:
                thought.eta = eta
                self.session.commit()
        except Exception as e:
            logger.error(e)

    def show_last_n(self, n=10):
        try:
            thoughts = self.session.query(Thought).order_by(Thought.id.desc()).limit(n).all()
            return thoughts
        except Exception as e:
            logger.error(e)

    def get_recent_notes(self, time_frame=10):
        # get recent notes (last time_frame days) with the status "Open"
        try:
            start_date = datetime.now() - timedelta(days=time_frame)
            thoughts = self.session.query(Thought).filter(Thought.date_created > start_date).filter(
                Thought.status == "open").all()
            return thoughts
        except Exception as e:
            logger.error(e)

    def get_all_notes(self) -> List:
        query = self.session.query(Thought)
        record_count = query.count()

        if record_count > 1000:
            query = query.order_by(Thought.id.desc()).limit(1000)

        return query.all()

    def send_plots(self):
        # TODO take two dates as arguments
        try:
            # get thoughts with date_created not older than a month
            thoughts = self.session.execute(
                "SELECT * FROM thought WHERE date_created > DATE_SUB(NOW(), INTERVAL 2 MONTH)"
            ).fetchall()
            filename = PlotMaker.get_plots(thoughts)
            return filename
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

    def get_all_categories(self):
        try:
            categories = self.session.query(Thought.label).distinct().all()
            return [str(category[0]) for category in categories]
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


if __name__ == "__main__":
    action_handler = DBActionHandler()
    plot_file = action_handler.send_plots()
    print(plot_file)
