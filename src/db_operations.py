from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import func
from dotenv import load_dotenv
import os

load_dotenv()


Base = declarative_base()


class Thought(Base):
    __tablename__ = 'thought'
    id = Column(Integer, primary_key=True, autoincrement=True)
    thought = Column(String(255))
    label = Column(String(32))
    urgency = Column(String(16))
    status = Column(String(16))
    eta = Column(Float(2))
    date_created = Column(DateTime)
    data_completed = Column(DateTime)

    def __repr__(self):
        # TODO pretty print (with columns)
        return f"<Thought(thought={self.thought}, label={self.label}, urgency={self.urgency}, status={self.status}, " \
               f"eta={self.eta}, date_created={self.date_created}, data_completed={self.data_completed})>"


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

    def add_thought(self, thought, label, urgency, eta):
        try:
            thought = Thought(thought=thought, label=label, urgency=urgency, eta=eta)
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

    def show_last_5(self):
        try:
            thoughts = self.session.query(Thought).order_by(Thought.id.desc()).limit(5).all()
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
    db_dml.add_thought('test', 'test', 'test', 1)
    db_dml.add_thought('test2', 'test2', 'test2', 1)
    db_dml.update_thought_status('test', 'done')
    last_5 = db_dml.show_last_5()
    for thought in last_5:
        print(thought)
