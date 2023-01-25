from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()


Base = declarative_base()


class Thoughts(Base):
    __tablename__ = 'thoughts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    thought = Column(String(255))
    label = Column(String(32))
    urgency = Column(String(16))
    status = Column(String(16))
    eta = Column(Float(2))
    date_created = Column(DateTime)
    data_completed = Column(DateTime)

    def __repr__(self):
        return f"<Thoughts(thought={self.thought}, label={self.label}, urgency={self.urgency}, status={self.status}, " \
               f"eta={self.eta}, date_created={self.date_created}, data_completed={self.data_completed})>"


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64))
    password = Column(String(64))
    email = Column(String(64))
    is_admin = Column(Boolean)

    def __repr__(self):
        return f"<Users(username={self.username}, password={self.password}, email={self.email}, " \
               f"is_admin={self.is_admin})>"


def get_connection():
    url = os.getenv("DB_URL")
    engine = create_engine(
        url,
        connect_args=dict(host=os.getenv("DB_HOST"), port=3306)
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def create_table(connection):
    Base.metadata.create_all(connection.bind)


def drop_table(connection):
    Base.metadata.drop_all(connection.bind)


def add_thought(connection, thought, label, urgency, eta):
    # using sqlalchemy connect add a thought to the database
    try:
        query = f"""
            INSERT INTO thoughts (thought, label, urgency, status, eta)
            VALUES ('{thought}', '{label}', '{urgency}', 'open', '{eta}')
        """
        result = connection.execute(query)
        return result
    except Exception as e:
        print(e)


def get_random_note(connection):
    # using sqlalchemy connect add a thought to the database
    try:
        create_table_query = f"""
        SELECT * FROM thoughts ORDER BY RAND() LIMIT 1
        """
        result = connection.execute(create_table_query)
        return result.fetchone()
    except Exception as e:
        print(e)


def update_status(connection, thought, status):
    # update the status of a thought
    try:
        connection.query(Thoughts).filter(Thoughts.thought == thought).update({Thoughts.status: status})
        connection.commit()
    except Exception as e:
        print(e)


def show_last_5(connection):
    try:
        query = f"""
        SELECT * FROM thoughts ORDER BY id DESC LIMIT 5
        """
        result = connection.execute(query)
        return result.fetchall()
    except Exception as e:
        print(e)


def add_user(connection, username, password, email, is_admin):

    try:
        query = f"""
        INSERT INTO users (username, password, email, is_admin)
        VALUES ('{username}', '{password
        }', '{email}', '{is_admin}')
        """
        result = connection.execute(query)
        return result
    except Exception as e:
        print(e)


def get_user(connection, username):
    try:
        query = f"""
        SELECT * FROM users
        WHERE username = '{username}'
        """
        result = connection.execute(query)
        return result.fetchone()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    connection = get_connection()
    # drop_table(connection)
    create_table(connection)
    add_thought(connection, 'test', 'test', 'test', 1)
    # print(get_random_note(connection))
    update_status(connection, 'test', 'updated')
    print(show_last_5(connection))
    # add_user(connection
    # get_user(connection, 'test')
