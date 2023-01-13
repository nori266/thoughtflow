from dotenv import load_dotenv
from sqlite3 import connect, Error


def get_connection():
    load_dotenv()
    # connect to sqlite3 database
    try:
        connection = connect("thoughtflow.db", check_same_thread=False)
        print("Connection to SQLite DB successful")
        return connection
    except Error as e:
        print(f"The error '{e}' occurred")
        return None


def add_thought(connection, thought, class_, urgency, eta):
    # using sqlite3 connect add a thought to the database
    try:
        create_table_query = f"""
        INSERT INTO thoughts (thought, class, urgency, eta)
        VALUES (%s, %s, %s, %s)
        """
        cursor = connection.cursor()
        cursor.execute(create_table_query, (thought, class_, urgency, eta))
        connection.commit()
    except Error as e:
        print(e)


def get_random_note(connection):
    # using sqlite3 connect add a thought to the database
    try:
        create_table_query = f"""
        SELECT * FROM thoughts ORDER BY RANDOM() LIMIT 1
        """
        cursor = connection.cursor()
        cursor.execute(create_table_query)
        return cursor.fetchone()
    except Error as e:
        print(e)


def update_status(connection, thought, status):
    # update the status of a thought
    try:
        query = f"""
        UPDATE thoughts
        SET status = %s
        WHERE thought = %s
        """
        cursor = connection.cursor()
        cursor.execute(query, (status, thought))
        connection.commit()
    except Error as e:
        print(e)
