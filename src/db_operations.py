import os
from tqdm import tqdm

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func

load_dotenv()


Base = declarative_base()


class Thought(Base):
    __tablename__ = 'thought'
    id = Column(Integer, primary_key=True, autoincrement=True)
    thought = Column(String(512))
    label = Column(String(32))
    urgency = Column(String(16))
    status = Column(String(16))
    eta = Column(Float(2), default=0.5)
    date_created = Column(DateTime)
    date_completed = Column(DateTime)

    def __repr__(self):
        # return f"<Thought(thought={self.thought}, label={self.label}, urgency={self.urgency}, status={self.status}, " \
        #        f"eta={self.eta}, date_created={self.date_created}, date_completed={self.date_completed})>"
        thought_col_len = 40
        if len(self.thought) > thought_col_len:
            thought = self.thought[:thought_col_len]
        else:
            pad_len = thought_col_len - len(self.thought)
            thought = self.thought + " " * pad_len

        # TODO padding for all columns
        return f"{thought}\t{self.label}\t\t\t{self.urgency}\t{self.status}\t{self.eta}\t{self.date_created}\t" \
               f"{self.date_completed}"


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64))
    password = Column(String(64))
    email = Column(String(64))
    is_admin = Column(Boolean)

    def __repr__(self):
        return f"<User(username={self.username}, password={self.password}, email={self.email}, " \
               f"is_admin={self.is_admin})>"


class DB_DDL:
    def __init__(self, session):
        self.session = session

    def create_all_tables(self):
        Base.metadata.create_all(self.session.bind)

    def drop_all_tables(self):
        Base.metadata.drop_all(self.session.bind)

    def create_table(self, table: Base):
        table.__table__.create(self.session.bind)

    def drop_table(self, table: Base):
        table.__table__.drop(self.session.bind)


class DB_DML:
    def __init__(self, session):
        self.session = session

    def add_thought(self, thought, label, urgency, status, eta, date_created, date_completed=None):
        try:
            thought = Thought(
                thought=thought,
                label=label,
                urgency=urgency,
                status=status,
                eta=eta,
                date_created=date_created,
                date_completed=date_completed
            )
            self.session.add(thought)
            self.session.commit()
        except Exception as e:
            print(e)

    def get_random_note(self):
        try:
            thought = self.session.query(Thought).filter(Thought.status == 'todo').order_by(func.random()).first()
            return thought
        except Exception as e:
            print(e)

    def update_thought_status(self, thought, status):
        try:
            self.session.query(Thought).filter(Thought.thought == thought).update({Thought.status: status})
            self.session.commit()
        except Exception as e:
            print(e)

    def add_thoughts_from_csv(self, csv_file):
        try:
            df = pd.read_csv(csv_file, na_values='none')
            # replace Nan with None
            df = df.where(pd.notnull(df), None)
            df['eta'].fillna(0.5, inplace=True)
            for _, row in tqdm(df.iterrows(), total=len(df)):
                self.add_thought(
                    row['thought'],
                    row['label'],
                    row['urgency'],
                    row['status'],
                    row['eta'],
                    row['date_created'],
                    row['date_completed']
                )
        except Exception as e:
            print(e)

    def show_last_5(self):
        try:
            thoughts = self.session.query(Thought).order_by(Thought.id.desc()).limit(10).all()
            return thoughts
        except Exception as e:
            print(e)

    def add_user(self, username, password, email, is_admin):
        try:
            user = User(username=username, password=password, email=email, is_admin=is_admin)
            self.session.add(user)
            self.session.commit()
        except Exception as e:
            print(e)

    def get_user(self, username):
        try:
            user = self.session.query(User).filter(User.username == username).first()
            return user
        except Exception as e:
            print(e)


def get_session():
    url = os.getenv("DB_URL")
    engine = create_engine(
        url,
        connect_args=dict(host=os.getenv("DB_HOST"), port=3306)
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


if __name__ == '__main__':
    # TODO to unit test
    my_session = get_session()
    db_ddl = DB_DDL(my_session)
    db_dml = DB_DML(my_session)
    db_ddl.drop_all_tables()
    db_ddl.create_all_tables()
    db_dml.add_thoughts_from_csv('data/all_thoughts_date_filled.csv')
    last_5 = db_dml.show_last_5()
    for note in last_5:
        print(note)
