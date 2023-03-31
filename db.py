from pathlib import Path
import sqlite3
import os.path
import logging
from datetime import date
from typing import Optional

from settings import DATABASE, LOG_FILE


logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    filemode='a',
                    datefmt='%Y-%m-%d, %H:%M',
                    format='%(asctime)s: %(name)s: %(levelname)s: %(message)s')
log = logging.getLogger('database')


class Users:
    """
    build in functions:

    with.. as..:
    with Users() as db:
        ...

    in:
    if user_id in db...

    set item:
    db[user_id] = user_info  # firstname, username, date

    get item:
    user_info = db[user_id]

    """

    # Singleton connector to database
    # sqlite3 module support only one connection to db.
    def __new__(cls):
        if not hasattr(cls, 'sync_db_connector'):
            cls.singleton_db_connector = super(Users, cls).__new__(cls)
        return cls.singleton_db_connector

    def __init__(self):
        # to real path to 'db.sqlite3' file. If database file should be a parent dir,
        # set parent_dir = Path(__file__).resolve().parent.parent
        parent_dir = Path(__file__).resolve().parent
        self.db = os.path.join(parent_dir, DATABASE)  # path + file with any OS
        self.conn = sqlite3.connect(self.db)
        self.cur = self.conn.cursor()
        sql_check_users_table = """CREATE TABLE IF NOT EXISTS `users` (`id`	INTEGER,
                                                                    `firstname`	TEXT,
                                                                    `username`	TEXT,
                                                                    `register`	TEXT NOT NULL,
                                                                    PRIMARY KEY(`id`));
        """
        self.cur.execute(sql_check_users_table)
        self.conn.commit()

        if self.conn and self.cur:
            log.warning(f'Connection to: {self.db} success. Work with "users" table, OK.')
        else:
            log.error(f'Failed connection to: {self.db}')

    def __contains__(self, user_id: int):
        if self.is_user(user_id):
            return True
        else:
            return False

    def __getitem__(self, user_id: int):
        if self.is_user(user_id):
            sql = "SELECT id, firstname, username, register " \
                  "FROM users " \
                  "WHERE id={}".format(str(user_id))
            self.cur.execute(sql)
            self.conn.commit()
            result = self.cur.fetchone()
            return result
        return None

    def __setitem__(self, user_id, user_info: tuple):
        # new user
        if not self.is_user(user_id):
            sql = "INSERT INTO users (`id`, `firstname`, `username`, `register`) VALUES (?,?,?,?);"
            self.cur.execute(sql, user_info)
            self.conn.commit()
            result = self.cur.fetchone()
            return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn is not None and self.cur is not None:
            self.cur.close()
            self.cur = None
            self.conn.close()
            self.conn = None

    def __del__(self):
        if self.conn is not None and self.cur is not None:
            self.cur.close()
            self.cur = None
            self.conn.close()
            self.conn = None

    def is_user(self, user_id: int):
        sql = "SELECT 1 FROM users WHERE id={};".format(str(user_id))
        self.cur.execute(sql)
        self.conn.commit()
        result = self.cur.fetchone()

        if result is None:
            return False
        elif result == (1,):
            return True

    def keys(self):
        sql = "SELECT `id` FROM `users`;"
        self.cur.execute(sql)
        self.conn.commit()
        result = [i[0] for i in self.cur.fetchall()]
        return result


class Incident:
    """
    build in functions:

    with.. as..:
    with Incident() as db:
        ...

    in:
    if incident_id in db...

    set item:
    db[incident_id] = incident_info  # id, theme, description, user, contact, file

    get item:
    incident_info = db[incident_id]

    """

    # Singleton connector to database
    # sqlite3 module support only one connection to db.
    def __new__(cls):
        if not hasattr(cls, 'sync_db_connector'):
            cls.singleton_db_connector = super(Incident, cls).__new__(cls)
        return cls.singleton_db_connector

    def __init__(self):
        # to real path to 'db.sqlite3' file. If database file should be a parent dir,
        # set parent_dir = Path(__file__).resolve().parent.parent
        parent_dir = Path(__file__).resolve().parent
        self.db = os.path.join(parent_dir, DATABASE)  # path + file with any OS
        self.conn = sqlite3.connect(self.db)
        self.cur = self.conn.cursor()
        sql_check_incident_table = """CREATE TABLE IF NOT EXISTS `incident`(
                                                    `id` INTEGER,
                                                    `user` INTEGER,
                                                    `theme` TEXT NOT NULL, 
                                                    `description` TEXT NOT NULL, 
                                                    `contact` TEXT, 
                                                    `file` TEXT,
                                                    PRIMARY KEY(`id` AUTOINCREMENT),
                                                    FOREIGN KEY(`user`) REFERENCES `users`(`id`) ON DELETE CASCADE);
        """
        self.cur.execute(sql_check_incident_table)
        self.conn.commit()

        if self.conn and self.cur:
            log.warning(f'Connection to: {self.db} success. Work with "incident" table, OK.')
        else:
            log.error(f'Failed connection to: {self.db}')


    def __contains__(self, user_id: int):
        if self.is_user(user_id):
            return True
        else:
            return False

    def __getitem__(self, user_id: int):
        if self.is_user(user_id):
            sql = "SELECT `id`, `user`, `theme`, `description`, `contact`, `file` " \
                  "FROM `incident` " \
                  "WHERE `user`={}".format(str(user_id))
            self.cur.execute(sql)
            self.conn.commit()
            result = self.cur.fetchone()
            return result
        return None

    def __setitem__(self, user_id, incident_info):
        # new incident
        sql = "INSERT INTO `incident` (`user`, `theme`, `description`, `contact`, `file`) " \
              "VALUES (?,?,?,?,?);"
        self.cur.execute(sql, incident_info)
        self.conn.commit()
        result = self.cur.fetchone()
        return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn is not None and self.cur is not None:
            self.cur.close()
            self.cur = None
            self.conn.close()
            self.conn = None

    def __del__(self):
        if self.conn is not None and self.cur is not None:
            self.cur.close()
            self.cur = None
            self.conn.close()
            self.conn = None

    def is_user(self, user_id: int):
        sql = "SELECT 1 FROM `incident` WHERE `user`={};".format(str(user_id))
        self.cur.execute(sql)
        self.conn.commit()
        result = self.cur.fetchone()
        if result is None:
            return False
        elif result == (1,):
            return True

    def keys(self):
        sql = "SELECT `id` FROM `incident`;"
        self.cur.execute(sql)
        self.conn.commit()
        result = [i[0] for i in self.cur.fetchall()]
        return result


def register_user(user_id: int, firstname: str, username: str):
    user_info = (user_id, firstname, username, date.today())
    with Users() as db:
        if user_id not in db:
            db[user_id] = user_info


def register_incident(user_id: int, theme: str, description: str,
                      contact: Optional[str] = None, file: Optional[str] = None):
    incident_info = (user_id, theme, description, contact, file)
    with Incident() as db:
        db[user_id] = incident_info


if __name__ == '__main__':

    test_user = 777777777
    user_info = (test_user, 'Test_Dim', 'Test_Dim_username')
    incident_info = (test_user, 'Плохая связь', 'Раньше было лучше!')

    users = Users()
    register_user(*user_info)
    incedent = Incident()
    register_incident(*incident_info)
