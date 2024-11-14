import sqlite3
from sqlite3 import Error

class DBManager:
    def __init__(self, logger, db_file: str) -> None:
        self.logger = logger;
        self.db_file = db_file
        self.connection = None
        self.cursor = None

    def connect(self) -> None:
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
        except Error as e:
            self.logger.error(f"error while connecting to dabase {e}")
    
    def close(self) -> None:
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=()) -> None:
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except Error as e:
            self.logger.error(f"error while perform query {query}: {e}")
    
    def fetch_all(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return rows
        except Error as e:
            self.logger.error(f"error while fetching rows {query}, {e}")
            return []
    
    def getTasks(self, query, params = ()):
        self.connect()
        tasks = self.fetch_all(query=query, params=params)
        self.close()
        return tasks
    
    def insert_task(self, data) -> None:
        self.connect()
        query = f"insert into tasks (operation, language, title, file, destinationPath) values (?, ?, ?, ?, ?)"
        self.execute_query(query=query, params=data)
        self.close()
    
    def update_task_status(self, taskId) -> None:
        self.connect()
        query = f"update tasks set process = ? where id = ?"
        self.execute_query(query=query, params=(1, taskId))
        self.close()

    def delete_task(self, taskId) -> None:
        self.connect()
        query = f"delete from tasks where id = ?"
        self.execute_query(query=query, params=(taskId,))
        self.close()