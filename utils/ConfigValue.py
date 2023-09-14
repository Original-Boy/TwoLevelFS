import mysql.connector


class ConfigValue:
    def __init__(self):  # 传实例作为参数时，传递的是实例的引用（类似指针），而不是实例的拷贝

        self.BASE_DIR = "base"
        self.current_dir = self.BASE_DIR
        self.DEFAULT_USR = "everyone"
        self.username = self.DEFAULT_USR
        self.password_db_path = "password_db.txt"
        self.db = self.connect_to_database()

    def connect_to_database(self):
        password = self.get_password(self.password_db_path)
        return mysql.connector.connect(
            host="localhost", user="root", password=password, database="TwoLevelFS"
        )

    def get_password(self, path):
        with open(path, "r") as password:
            return password.read()
