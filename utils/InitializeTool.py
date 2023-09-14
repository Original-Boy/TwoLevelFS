import hashlib
import os.path

from utils.ConfigValue import ConfigValue
from utils.UserVerification import UserVerification
from utils.FileOperation import FileOperation
from utils.PermissionChange import PermissionChange
from utils.PermissionCheck import PermissionCheck


class InitializeTool:
    def __init__(self):
        self.configv = ConfigValue()
        self.userv = UserVerification(self.configv)
        self.fileo = FileOperation(self.configv)
        self.permissionc = PermissionChange(self.configv)
        self.permission_check = PermissionCheck(self.configv)

    def initialize_system(self):
        # Connect to database
        db = self.configv.db
        cursor = db.cursor()

        # Check if admin group exists
        cursor.execute("SELECT group_id FROM `Groups` WHERE group_name='admin'")
        group_data = cursor.fetchone()

        # Create admin group if it doesn't exist
        if not group_data:
            cursor.execute("INSERT INTO `Groups` (group_name) VALUES ('admin')")
            db.commit()
            admin_group_id = cursor.lastrowid
        else:
            admin_group_id = group_data[0]

        # Check if admin user exists
        cursor.execute("SELECT user_id FROM Users WHERE username='admin'")
        user_data = cursor.fetchone()

        # Create admin user if it doesn't exist
        if not user_data:
            password_hash = hashlib.sha256("rootpassword".encode()).hexdigest()
            cursor.execute(
                "INSERT INTO Users (username, password, group_id) VALUES ('admin', %s, %s)",
                (password_hash, admin_group_id),
            )
            db.commit()

    def help(self):
        commands = {
            "register": "Register a new user. Usage: register <username> <password> <group> (default=ordinary_user)",
            "login": "Login a user. Usage: login <username> <password>",
            "logout": "Logout a user. Usage: logout",
            "create": "Create a new file. Usage: create <filename> <content> <protection>",
            "delete": "Delete a file. Usage: delete <filename>",
            "read": "Read a file. Usage: read <filename>",
            "write": "Write to a file. Usage: write <filename> <content>",
            "dir": "List directory contents. Usage: dir",
            "cd": "Change the current directory. Usage: cd <directory>",
            "exit": "Exit the program.",
            "mkdir": "Create a new directory. Usage: mkdir <dir_name> <protection>",
            "rmdir": "Delete a directory. Usage: rmdir <dir_name>",
            "chmod": "Change the protection of a file. Usage: chmod <filename> <protection>",
            "chgroup": "Change the group of a user (admin-only). Usage: chgroup <username> <new_user_group>",
        }

        for command, description in commands.items():
            print(f"{command}: {description}")
    # 主循环，匹配命令
    def interactive_command_loop(self):
        self.initialize_system()

        while True:
            command_line = input(
                f"{self.configv.username}@Laptop {self.configv.current_dir} % "
            )

            if command_line.strip().lower() == "exit":
                print(f"Goodbye! {self.configv.current_dir}")
                break

            commands = command_line.split()
            if not commands:
                continue

            cmd = commands[0].lower()

            if cmd == "register":
                if len(commands) < 3:
                    print(
                        "Usage: register <username> <password> <group> (default=ordinary_user)"
                    )
                elif len(commands) == 3:
                    self.userv.register_user(commands[1], commands[2])
                elif len(commands) == 4:
                    self.userv.register_user(commands[1], commands[2], commands[3])

            elif cmd == "login":
                if len(commands) < 3:
                    print("Usage: login <username> <password>")
                    continue
                response = self.userv.login(commands[1], commands[2])
                if response:
                    self.configv.username = commands[1]
                    if not self.permission_check.is_admin(
                        commands[1]
                    ):  # admin用户没有自己的文件夹
                        self.configv.current_dir = os.path.join(
                            self.configv.BASE_DIR, commands[1]
                        )
                    else:
                        self.configv.current_dir = self.configv.BASE_DIR

            elif cmd == "help":
                self.help()

            elif cmd == "cd":
                if len(commands) < 2:
                    print("Usage: cd <directory>")
                    continue
                self.fileo.change_directory(commands[1])

            elif cmd == "dir":
                self.fileo.list_directory()

            elif self.configv.username == self.configv.DEFAULT_USR:
                print("Please login first!")

            elif cmd == "logout":
                self.configv.current_dir = self.configv.BASE_DIR
                self.configv.username = self.configv.DEFAULT_USR
                print("Logout successfully!")

            elif cmd == "create":
                if len(commands) < 3:
                    print("Usage: create <filename> <content> <protection>")
                    continue
                self.fileo.create_file(
                    commands[1],
                    " ".join(commands[2:-1]),
                    commands[-1],
                )

            elif cmd == "delete":
                if len(commands) < 2:
                    print("Usage: delete <filename>")
                    continue
                self.fileo.delete_file(commands[1])

            elif cmd == "read":
                if len(commands) < 2:
                    print("Usage: read <filename>")
                    continue
                self.fileo.read_file(commands[1])

            elif cmd == "write":
                if len(commands) < 3:
                    print("Usage: write <filename> <content>")
                    continue
                self.fileo.write_file(commands[1], " ".join(commands[2:]))

            elif cmd == "mkdir":
                if len(commands) < 3:
                    print("Usage: mkdir <dir_name> <protection>")
                    continue
                self.fileo.create_directory(commands[1], commands[2])

            elif cmd == "rmdir":
                if len(commands) < 2:
                    print("Usage: rmdir <dir_name>")
                    continue
                self.fileo.delete_directory(commands[1])

            elif cmd == "chmod":
                if len(commands) < 3:
                    print("Usage: chmod <filename> <protection>")
                    continue
                self.permissionc.change_protection(self.configv.username, commands[1])

            elif cmd == "chgroup":
                if len(commands) < 3:
                    print("Usage: chgroup <username> <new_user_group>")  #
                    continue
                self.permissionc.change_user_group(commands[1], commands[2])

            else:
                print(f"Unknown command: {cmd}")
