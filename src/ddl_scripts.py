import argparse
import logging
import os

from dotenv import load_dotenv
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Integer
from tqdm import tqdm

from db_entities import Thought, Category


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

    def create_table_from_model(self, model_class):
        try:
            model_class.__table__.create(bind=self.session.bind, checkfirst=True)
            self.session.commit()
            logger.info(f"Table '{model_class.__tablename__}' created successfully.")
        except SQLAlchemyError as e:
            logger.error(f"Error creating table '{model_class.__tablename__}': {e}")
            raise

    def drop_table(self, table: Base):
        table.__table__.drop(self.session.bind)

    def add_thoughts_from_csv(self, csv_file):
        try:
            df = pd.read_csv(csv_file, na_values='none')
            # replace Nan with None
            df = df.where(pd.notnull(df), None)
            df['eta'].fillna(0.5, inplace=True)
            df = df.fillna(np.nan).astype(object).replace({np.nan: None})
            for _, row in tqdm(df.iterrows(), total=len(df)):
                thought = Thought(
                    note_text=row['note_text'],
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

    def add_categories_from_csv(self, csv_file):
        try:
            df = pd.read_csv(csv_file, na_values='none')
            # replace Nan with None
            df = df.where(pd.notnull(df), None)
            df = df.fillna(np.nan).astype(object).replace({np.nan: None})
            for _, row in tqdm(df.iterrows(), total=len(df)):
                category = Category(
                    show_category=row['show_category'],
                    semantic_category=row['semantic_category']
                )
                self.session.add(category)
            self.session.commit()
        except Exception as e:
            logger.error(e)

    def add_column(self, table: Base, column: str, column_type):
        self.session.execute(f"ALTER TABLE {table.__tablename__} ADD COLUMN {column} {column_type().compile(self.session.bind.dialect)}")
        self.session.commit()

    def rename_column(self, table, old_column_name, new_column_name):
        try:
            rename_command = f"""
                ALTER TABLE {table.__tablename__} 
                RENAME COLUMN {old_column_name} TO {new_column_name};
            """
            self.session.execute(rename_command)
            self.session.commit()
            logger.info(f"Column '{old_column_name}' renamed to '{new_column_name}' in '{table.__tablename__}'.")
        except SQLAlchemyError as e:
            logger.error(f"Error renaming column: {e}")
            raise

    def map_labels(self):
        df = pd.read_csv('data/category_paths.csv')
        mapping_dict = pd.Series(df.show_category.values, index=df.semantic_category).to_dict()
        for thought in self.session.query(Thought).all():
            if thought.label in mapping_dict:
                thought.label = mapping_dict[thought.label]

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
    inspector = Inspector.from_engine(db_ddl.session.bind)
    # TODO add a check to see if the csv file exists
    # TODO backup the database before dropping the tables
    tables_before = inspector.get_table_names()
    logger.info(f"Tables before drop: {tables_before}")

    db_ddl.drop_all_tables()

    # Checking tables after drop
    tables_after_drop = inspector.get_table_names()
    logger.info(f"Tables after drop: {tables_after_drop}")
    db_ddl.create_all_tables()
    db_ddl.add_thoughts_from_csv(csv_file)


if __name__ == '__main__':
    # TODO create a function for this:
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
    db_ddl.create_table_from_model(Category)
    db_ddl.add_categories_from_csv('data/category_paths.csv')
