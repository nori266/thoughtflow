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
        query = f"""
            INSERT INTO thoughts (thought, class, urgency, status, eta)
            VALUES ('{thought}', '{class_}', '{urgency}', 'open', '{eta}')
        """
        cursor = connection.cursor()
        cursor.execute(query)
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


def show_last_5(connection):
    # show the last 5 thoughts
    try:
        query = f"""
        SELECT * FROM thoughts ORDER BY id DESC LIMIT 5
        """
        cursor = connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(e)


if __name__ == '__main__':
    with get_connection() as connection:
        print(show_last_5(connection))
