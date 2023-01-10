import csv
from getpass import getpass
from os import environ

from dotenv import load_dotenv
from mysql.connector import connect, Error


load_dotenv()


def create_database(connection):
    create_db_query = "CREATE DATABASE IF NOT EXISTS thoughtflow"
    with connection.cursor() as cursor:
        cursor.execute(create_db_query)


def insert_data_from_csv(connection, table_name, csv_file):
    with open(csv_file, "r") as f:
        csv_data = csv.reader(f)
        print(next(csv_data))

        with connection.cursor() as cursor:
            print("Inserting data...")
            for row in csv_data:
                print(row)
                # insert data into the table
                cursor.execute(f"INSERT INTO {table_name} (thought, class, urgency, status, eta, date_created) "
                               f"VALUES (%s, %s, %s, %s, %s, %s)", row[:-1])
        connection.commit()


def create_table_from_csv(connection, table_name, csv_file):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        thought TEXT,
        class VARCHAR(255),
        urgency VARCHAR(255),
        status VARCHAR(255),
        eta FLOAT,
        date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
        date_completed DATETIME DEFAULT NULL
    )
    """
    with connection.cursor() as cursor:
        cursor.execute(create_table_query)
    insert_data_from_csv(connection, table_name, csv_file)


if __name__ == '__main__':
    user = environ.get('DB_USER')
    password = environ.get('DB_PASSWORD')
    try:
        with connect(
            host="localhost",
            user=user,
            password=password,
            database="thoughtflow",
        ) as db_connection:
            create_table_from_csv(db_connection, "thoughts", "data/thoughts_with_all_fields.csv")
    except Error as e:
        print(e)
