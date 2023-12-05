from datetime import datetime
from Config import ADMIN_USERNAME, ADMIN_PASSWORD

class Database:
    def __init__(self, conn):
        self.conn = conn

    def create_table(self, table_name, fields):
        fields_str = ', '.join(f'{name} {type}' for name, type in fields.items())
        self.exec_query(f"CREATE TABLE IF NOT EXISTS {table_name} ({fields_str})")

    def insert_row(self, table_name, data):
        placeholders = ', '.join('?' * len(data))
        fields = ', '.join(data.keys())
        cursor = self.conn.cursor()
        cursor.execute(f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})", tuple(data.values()))
        self.conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    def update_row(self, table_name, data, where = None, values=tuple()):
        set_clause = ', '.join(f'{k} = ?' for k in data.keys())
        query = f"UPDATE {table_name} SET {set_clause}"
        if where is not None:
            query += f" WHERE {where}"
        self.exec_query(query, tuple(data.values()) + values)

    def get_row(self, table_name, where = None, order_by = None, values=tuple()):
        query = f"SELECT * FROM {table_name}"
        if where is not None:
            query += f" WHERE {where} "
        if order_by is not None:
            query += f" ORDER BY {order_by} "
        query += " LIMIT 1"
        return self.get_row_query(query, values)

    def get_rows(self, table_name, where = None, values=tuple(), order_by = " id DESC ", limit = None):
        query = f"SELECT * FROM {table_name}"
        if where is not None:
            query += f" WHERE {where} "
        if order_by is not None:
            query += f" ORDER BY {order_by} "
        if limit is not None:
            query += f" LIMIT {limit} "
        return self.get_rows_query(query, values)

    def delete_rows(self, table_name, where = None, values=tuple()):
        query = f"DELETE FROM {table_name}"
        if where is not None:
            query += f" WHERE {where}"
        self.exec_query(query, values)

    def get_rows_query(self, query, values=tuple()):
        cursor = self.conn.cursor()
        cursor.execute(query, values)
        result = cursor.fetchall()
        cursor.close()
        return result
    
    def get_row_query(self, query, values=tuple()):
        cursor = self.conn.cursor()
        cursor.execute(query, values)
        result = cursor.fetchone()
        cursor.close()
        return result
    
    def exec_query(self, query, values=list()):
        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()
        cursor.close()

    def create_users_table(self):
        self.create_table('users', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'username': 'TEXT UNIQUE',
            'fullname': 'TEXT',
            'password': 'TEXT',
            'salt': 'TEXT',
            'super': 'INTEGER',
            'corporate': 'INTEGER',
            'reviewed': 'INTEGER',
            'denied': 'INTEGER',
            'reason': 'TEXT',
            'warnings': 'INTEGER',
            'balance': 'REAL',
            'bio': 'TEXT',
            'profile_picture': 'TEXT',
            'first_payment_done': 'INTEGER',
            'first_password_changed': 'INTEGER',
            'reported': 'INTEGER',
            'demoted': 'INTEGER',
        })

    def create_taboo_words_table(self):
        self.create_table('taboo_words', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'word': 'TEXT UNIQUE'
        })
    
    def create_messages_table(self):
        self.create_table('messages', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'message': 'TEXT',
            'keywords': 'TEXT',
            'author_id': 'INTEGER REFERENCES users(id)',
            'reads': 'INTEGER',
            'reported': 'INTEGER',
            'ad': 'INTEGER',
            'job_ad': 'INTEGER',
            'words': 'INTEGER',
            'price': 'REAL',
            'date': 'TEXT',
            'time': 'TEXT',
            'attachment': 'TEXT',
            'original_id': 'INTEGER REFERENCES messages(id)',
        })

    def create_likes_table(self):
        self.create_table('likes', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'user_id': 'INTEGER REFERENCES users(id)',
            'message_id': 'INTEGER REFERENCES messages(id)',
            'positive': 'INTEGER',
        })

    def create_follows_table(self):
        self.create_table('follows', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'followed_id': 'INTEGER REFERENCES users(id)',
            'follower_id': 'INTEGER REFERENCES users(id)',
        })

    def create_tips_table(self):
        self.create_table('tips', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'user_id': 'INTEGER REFERENCES users(id)',
            'author_id': 'INTEGER REFERENCES users(id)',
            'amount': 'REAL',
        })

    def create_comments_table(self):
        self.create_table('comments', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'user_id': 'INTEGER REFERENCES users(id)',
            'message_id': 'INTEGER REFERENCES messages(id)',
            'comment': 'TEXT',
            'reported': 'INTEGER',
        })

    def create_job_applications_table(self):
        self.create_table('job_applications', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'user_id': 'INTEGER REFERENCES users(id)',
            'message_id': 'INTEGER REFERENCES messages(id)',
            'answered': 'INTEGER',
            'accepted': 'INTEGER',
        })

    def create_warnings_table(self):
        self.create_table('warnings', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'type': 'TEXT',
            'reported_by_user_id': 'INTEGER REFERENCES users(id)',
            'user_id': 'INTEGER REFERENCES users(id)',
            'message_id': 'INTEGER REFERENCES messages(id)',
            'comment_id': 'INTEGER REFERENCES comments(id)',
            'disputable': 'INTEGER',
            'disputed': 'INTEGER',
            'dispute_closed': 'INTEGER',
            'forgiven': 'INTEGER',
            'reason': 'TEXT',
            'fine': 'REAL',
            'date': 'TEXT',
            'time': 'TEXT'
        })

    def create_payments_table(self):
        self.create_table('payments', {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'user_id': 'INTEGER REFERENCES users(id)',
            'payment_amount': 'REAL',
            'message_id': 'INTEGER REFERENCES messages(id)',
            'explanation': 'TEXT',
            'date': 'TEXT',
            'time': 'TEXT'
        })

    def create_admin_user(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USERNAME,))
        row = cursor.fetchone()
        cursor.close()
        if row is not None:
            return
        from User import User
        salt = User.get_random_salt()
        self.insert_row('users', {
            'username': ADMIN_USERNAME,
            'fullname': 'Admin',
            'password': User.get_hashed_password(ADMIN_PASSWORD, salt),
            'salt': salt,
            'first_password_changed': 1,
            'first_payment_done': 1,
            'balance': 0,
            'bio': 'I am the admin',
            'profile_picture': '',
            'reviewed': 1,
            'denied': 0,
            'reason': '',
            'corporate': 1,
            'super': 1,
        })

    def create_tables(self):
        self.create_users_table()
        self.create_taboo_words_table()
        self.create_messages_table()
        self.create_likes_table()
        self.create_follows_table()
        self.create_job_applications_table()
        self.create_warnings_table()
        self.create_tips_table()
        self.create_payments_table()
        self.create_comments_table()

    def drop_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS taboo_words")
        cursor.execute("DROP TABLE IF EXISTS messages")
        cursor.execute("DROP TABLE IF EXISTS likes")
        cursor.execute("DROP TABLE IF EXISTS dislikes")
        cursor.execute("DROP TABLE IF EXISTS follows")
        cursor.execute("DROP TABLE IF EXISTS reports")
        cursor.execute("DROP TABLE IF EXISTS warnings")
        cursor.execute("DROP TABLE IF EXISTS tips")
        cursor.execute("DROP TABLE IF EXISTS transactions")
        self.conn.commit()
        cursor.close()