import argparse
import logging
import os

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Integer
from tqdm import tqdm

from db_entities import Thought


load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.DEBUG)

Base = declarative_base()


class DB_DDL:
    def __init__(self):
        self.session = self.get_session()

    def create_all_tables(self):
        Base.metadata.create_all(self.session.bind)

    def drop_all_tables(self):
        Base.metadata.drop_all(self.session.bind)

    def create_table(self, table: Base):
        table.__table__.create(self.session.bind)

    def drop_table(self, table: Base):
        table.__table__.drop(self.session.bind)

    def add_thoughts_from_csv(self, csv_file):
        try:
            df = pd.read_csv(csv_file, na_values='none')
            # replace Nan with None
            df = df.where(pd.notnull(df), None)
            df['eta'].fillna(0.5, inplace=True)
            for _, row in tqdm(df.iterrows(), total=len(df)):
                thought = Thought(
                    thought=row['thought'],
                    label=row['label'],
                    urgency=row['urgency'],
                    status=row['status'],
                    eta=row['eta'],
                    date_created=row['date_created'],
                    date_completed=row['date_completed']
                )
                self.session.add(thought)
            self.session.commit()
        except Exception as e:
            logger.error(e)

    def add_column(self, table: Base, column: str, column_type):
        self.session.execute(f"ALTER TABLE {table.__tablename__} ADD COLUMN {column} {column_type().compile(self.session.bind.dialect)}")
        self.session.commit()


    @staticmethod
    def get_session():
        # TODO move to utils so that it can be reused in db_action_handler
        url = os.getenv("DB_URL")
        engine = create_engine(
            url,
            connect_args=dict(host=os.getenv("DB_HOST"), port=3306)
        )
        Session = sessionmaker(bind=engine)
        return Session()


def reload_data(csv_file):
    """
    Reloads data from csv file to the database. Removes all the data from the database and replaces it with the data
    from the csv file.
    :param csv_file:
    :return:
    """
    db_ddl = DB_DDL()
    # TODO add a check to see if the csv file exists
    # TODO backup the database before dropping the tables
    db_ddl.drop_all_tables()
    db_ddl.create_all_tables()
    db_ddl.add_thoughts_from_csv(csv_file)


if __name__ == '__main__':
    # ask the user if they want to reload the data from the csv file
    # reload = input("Do you want to reload the data from the csv file? "
    #                "This will remove all current data in the database! (yes/no): ")
    # args = argparse.ArgumentParser()
    # args.add_argument('--csv', type=str)
    # parsed_args = args.parse_args()
    # if reload == 'yes':
    #     reload_data(parsed_args.csv)
    # elif reload == 'no':
    #     print("Data not reloaded.")
    # else:
    #     print("Invalid input. Please type 'yes' or 'no'.")

    db_ddl = DB_DDL()
    db_ddl.add_column(Thought, 'message_id', Integer)
