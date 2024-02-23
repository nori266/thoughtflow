from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import func


Base = declarative_base()


class Thought(Base):
    __tablename__ = 'thought'
    id = Column(Integer, primary_key=True, autoincrement=True)
    note_text = Column(String(512))  # TODO: change to Text
    label = Column(String(512))
    urgency = Column(String(16))
    status = Column(String(16))
    eta = Column(Float(2), default=0.5)
    date_created = Column(DateTime, default=func.now())  # TODO test this
    date_completed = Column(DateTime)
    message_id = Column(Integer)

    def __repr__(self):
        thought_col_len = 40
        if len(self.note_text) > thought_col_len:
            thought = self.note_text[:thought_col_len]
        else:
            pad_len = thought_col_len - len(self.note_text)
            thought = self.note_text + " " * pad_len

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


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    show_category = Column(String(512))
    semantic_category = Column(String(512))

    def __repr__(self):
        return f"<Category(show_category={self.show_category})>"
