from os import environ

from dotenv import load_dotenv
from mysql.connector import connect, Error


load_dotenv()
user = environ.get('DB_USER')
password = environ.get('DB_PASSWORD')


def add_thought(thought, class_, urgency, eta):
    try:
        with connect(
            host="localhost",
            user=user,
            password=password,
            database="thoughtflow",
        ) as db_connection:
            create_table_query = f"""
            INSERT INTO thoughts (thought, class, urgency, eta)
            VALUES (%s, %s, %s, %s)
            """
            with db_connection.cursor() as cursor:
                cursor.execute(create_table_query, (thought, class_, urgency, eta))
            db_connection.commit()
    except Error as e:
        print(e)


def get_random_note():
    try:
        with connect(
            host="localhost",
            user=user,
            password=password,
            database="thoughtflow",
        ) as db_connection:
            create_table_query = f"""
            SELECT thought, class, urgency, eta FROM thoughts
            WHERE status = 'open'
            ORDER BY RAND()
            LIMIT 1
            """
            with db_connection.cursor() as cursor:
                cursor.execute(create_table_query)
                return cursor.fetchone()
    except Error as e:
        print(e)


def update_status(thought, status):
    try:
        with connect(
            host="localhost",
            user=user,
            password=password,
            database="thoughtflow",
        ) as db_connection:
            create_table_query = f"""
            UPDATE thoughts SET status = %s WHERE thought = %s
            """
            with db_connection.cursor() as cursor:
                cursor.execute(create_table_query, (status, thought))
            db_connection.commit()
    except Error as e:
        print(e)
