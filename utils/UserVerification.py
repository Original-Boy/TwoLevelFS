import hashlib
import os

from utils.FileOperation import FileOperation


class UserVerification:
    def __init__(self, configv):
        self.configv = configv
        self.fileo = FileOperation(configv)

    def register_user(self, username, password, group="ordinary_user"):
        db = self.configv.db
        cursor = db.cursor()

        cursor.execute("SELECT * FROM Users WHERE username=%s", (username,))
        user = cursor.fetchone()
        if user:
            print("User already exists!")
            return

        cursor.execute("SELECT group_id FROM `Groups` WHERE group_name=%s", (group,))
        group_id = cursor.fetchone()[0]
        if not group_id:
            print(f"Group {group} does not exist!")
            return

        cursor.execute(
            "INSERT INTO Users (username, password) VALUES (%s, %s)",
            (username, hashlib.sha256(password.encode()).hexdigest()),
        )

        cursor.execute(
            "UPDATE Users SET group_id=%s WHERE username=%s", (group_id, username)
        )
        db.commit()

        self.fileo.create_directory(
            username, "rwxrwxrwx", if_register=True, username=username
        )
        print(f"User {username} registered successfully!")

    def login(self, username, password):
        cursor = self.configv.db.cursor()

        cursor.execute(
            "SELECT * FROM Users WHERE username=%s AND password=%s",
            (username, hashlib.sha256(password.encode()).hexdigest()),
        )
        user = cursor.fetchone()
        if not user:
            print("Invalid username or password!")
            return False
        print(f"User {username} logged in successfully!")
        return True
