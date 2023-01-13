import csv

from dotenv import load_dotenv
from sqlite3 import Error

import db_operations as db


load_dotenv()


def insert_data_from_csv(cursor, table_name, csv_file):
    with open(csv_file, "r") as f:
        csv_data = csv.reader(f)
        print(next(csv_data))
        for row in csv_data:
            print(row)
            values = str(row[:5]).strip("[]")
            # insert data into the table
            cursor.execute(f"INSERT INTO {table_name} (thought, class, urgency, status, eta) VALUES ({values})")
            print("Data inserted successfully")


def create_table_from_csv(connection, table_name, csv_file):
    # create a table in the database and insert data from csv file
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ("
                       f"thought VARCHAR(255) NOT NULL, "
                       f"class VARCHAR(255) NOT NULL, "
                        f"urgency VARCHAR(255), "
                        f"status VARCHAR(255), "
                        f"eta VARCHAR(255))")
        insert_data_from_csv(cursor, table_name, csv_file)
        connection.commit()
    except Error as e:
        print(e)


if __name__ == '__main__':
    with db.get_connection() as connection:
        create_table_from_csv(connection, "thoughts", "data/my_showcase_data.csv")
