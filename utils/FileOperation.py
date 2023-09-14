import os
import shutil
from utils.PermissionCheck import PermissionCheck


class FileOperation:
    # configv = None 想在类内其他地方调用的话，应该输入FileOperation.configv
    def __init__(self, configv):
        self.configv = configv  # 这是对传进来的实例的引用，而不是把实例的值赋给self.configv
        self.permissionc = PermissionCheck(configv)

    def create_file(self, filename, content, protection):
        if not self.permissionc.is_valid_protection(protection):
            print(f"Invalid protection string {protection}")
            return

        db = self.configv.db
        cursor = db.cursor()

        if filename.startswith(self.configv.BASE_DIR):
            file_path = filename
            filename = os.path.basename(file_path)
            if file_path != self.configv.BASE_DIR:
                dir_path = os.path.dirname(file_path)
            else:
                dir_path = self.configv.BASE_DIR
        else:
            dir_path = self.configv.current_dir
            file_path = os.path.join(self.configv.current_dir, filename)

        if not (
            (
                self.permissionc.check_permission(dir_path, self.configv.username, "w")
                and self.permissionc.check_permission(
                    dir_path, self.configv.username, "x"
                )
            )
            or self.permissionc.is_admin(self.configv.username)
        ):
            return

        # Check if file with the given name already exists
        cursor.execute(
            "SELECT COUNT(*) FROM Files WHERE filename=%s and content_path=%s",
            (filename, file_path),
        )
        if cursor.fetchone()[0] > 0:
            print(f"A file/directory with the name '{filename}' already exists!")
            return

        # Rest of the file creation logic
        cursor.execute(
            "SELECT user_id FROM Users WHERE username=%s", (self.configv.username,)
        )
        user = cursor.fetchone()
        if not user:  # 其实没什么用
            print("User not found!")
            return

        with open(file_path, "w") as file:
            file.write(content)

        cursor.execute("SELECT group_id FROM Users WHERE user_id=%s", (user[0],))
        group_id = cursor.fetchone()[0]
        cursor.execute(  # 把owner_id删掉了, is_directory默认为0
            "INSERT INTO Files (user_id, group_id, filename, physical_address, protection, content_path) VALUES (%s, %s, %s, %s, %s, %s)",
            (user[0], group_id, filename, str(id(file_path)), protection, file_path),
        )
        db.commit()
        print(f"File {filename} create successfully!")

    def delete_file(self, filename):
        db = self.configv.db
        cursor = db.cursor()

        if filename.startswith("base"):
            file_path = filename
            if file_path != "base":
                dir_path = os.path.dirname(file_path)
            else:
                dir_path = self.configv.BASE_DIR
        else:
            dir_path = self.configv.current_dir
            file_path = os.path.join(self.configv.current_dir, filename)

        cursor.execute(
            "SELECT Users.user_id, content_path, is_directory FROM Users JOIN Files ON Users.user_id = Files.user_id WHERE username=%s AND content_path=%s",
            (self.configv.username, file_path),
        )
        file_entry = cursor.fetchone()
        if not file_entry:
            print(f"File {filename} is not found!")
            return
        elif file_entry[2]:
            print(f"Cannot delete directory {filename}!")
            return
        elif not (
            (
                self.permissionc.check_permission(dir_path, self.configv.username, "w")
                and self.permissionc.check_permission(
                    dir_path, self.configv.username, "x"
                )
            )
            or self.permissionc.is_admin(self.configv.username)
        ):
            return
        else:
            os.remove(file_entry[1])

        cursor.execute(
            "DELETE FROM Files WHERE user_id=%s AND content_path=%s",
            (file_entry[0], file_path),
        )
        db.commit()
        print(f"File {filename} delete successfully!")

    def read_file(self, filename):
        db = self.configv.db
        cursor = db.cursor()

        if filename.startswith(self.configv.BASE_DIR):
            file_path = filename
            filename = os.path.basename(filename)
        else:
            file_path = os.path.join(self.configv.current_dir, filename)

        cursor.execute(
            "SELECT content_path, is_directory, filename FROM Users JOIN Files ON Users.user_id = Files.user_id WHERE content_path=%s",
            (file_path,),
        )
        file_entry = cursor.fetchone()
        if not file_entry:
            print(f"File {filename} is not found!")
        elif file_entry[1]:
            print(f"Cannot read directory {file_entry[2]}!")
        elif not (
            self.permissionc.check_permission(file_path, self.configv.username, "r")
            or self.permissionc.is_admin(self.configv.username)
        ):
            return
        else:
            with open(file_entry[0], "r") as file:
                print(file.read())

    def write_file(self, filename, content):
        db = self.configv.db
        cursor = db.cursor()

        if filename.startswith(self.configv.BASE_DIR):
            file_path = filename
            filename = os.path.basename(filename)
        else:
            file_path = os.path.join(self.configv.current_dir, filename)

        cursor.execute(
            "SELECT content_path FROM Users JOIN Files ON Users.user_id = Files.user_id WHERE username=%s AND content_path=%s",
            (self.configv.username, file_path),
        )
        file_entry = cursor.fetchone()
        if not file_entry:
            print(f"File {filename} not found!")
        elif not (
            self.permissionc.check_permission(file_path, self.configv.username, "w")
            or self.permissionc.is_admin(self.configv.username)
        ):
            return
        else:
            with open(file_entry[0], "a") as file:  # 将书写的内容追加到末尾
                file.write(content)
            print(f"Content written to {filename} successfully!")

    def create_directory(self, dir_name, protection, if_register=False, username=None):
        if not self.permissionc.is_valid_protection(protection):
            print(f"Invalid protection string {protection}")
            return

        if dir_name.startswith(self.configv.BASE_DIR):
            file_path = dir_name
            if file_path != self.configv.BASE_DIR:
                dir_path = os.path.dirname(dir_name)
                dir_name = os.path.basename(dir_name)
            else:
                dir_path = self.configv.BASE_DIR
        else:
            dir_path = self.configv.current_dir
            file_path = os.path.join(self.configv.current_dir, dir_name)

        db = self.configv.db
        cursor = db.cursor()
        if if_register == True:
            file_path = os.path.join(self.configv.BASE_DIR, dir_name)
            dir_path = self.configv.BASE_DIR

        if not (
            (
                self.permissionc.check_permission(dir_path, self.configv.username, "w")
                and self.permissionc.check_permission(
                    dir_path, self.configv.username, "x"
                )
            )
            or self.permissionc.is_admin(self.configv.username)
        ):
            return

        # Check if directory with the given name already exists
        cursor.execute(
            "SELECT COUNT(*) FROM Files WHERE filename=%s and content_path=%s",
            (dir_name, file_path),
        )
        if cursor.fetchone()[0] > 0:
            print(f"A directory with the name '{dir_name}' already exists!")
            return

        # Rest of the directory creation logic
        if if_register == True:
            cursor.execute(
                "SELECT user_id, group_id FROM Users WHERE username=%s",
                (username,),
            )
        else:
            cursor.execute(
                "SELECT user_id, group_id FROM Users WHERE username=%s",
                (self.configv.username,),
            )
        user_data = cursor.fetchone()
        user_id, group_id = user_data

        os.makedirs(file_path, exist_ok=True)

        cursor.execute(
            "INSERT INTO Files (user_id, group_id, filename, physical_address, protection, content_path, is_directory) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                user_id,
                group_id,
                dir_name,
                str(id(file_path)),
                protection,
                file_path,
                True,
            ),
        )
        db.commit()
        print(f"Directory {dir_name} created successfully!")

    def delete_directory(self, directory_name):
        # Connect to the database to fetch file and directory details
        db = self.configv.db
        cursor = db.cursor()

        if directory_name.startswith("base"):
            file_path = directory_name
            if file_path != "base":
                dir_path = os.path.dirname(file_path)
            else:
                dir_path = "base"
        else:
            dir_path = self.configv.current_dir
            file_path = os.path.join(self.configv.current_dir, directory_name)

        # Fetch all files and subdirectories inside the directory
        cursor.execute(
            "SELECT content_path, is_directory FROM Files WHERE content_path LIKE %s",
            (dir_path + "%",),
        )  # % 代表任何序列
        items = cursor.fetchall()

        if len(items) == 1 and items[0][1] == False:  # 这肯定是一个文件
            print(f"{directory_name} is not a directory!")
            return
        elif len(items) == 0:
            print(f"{directory_name} is not found!")
            return
        elif not (
            (
                self.permissionc.check_permission(dir_path, self.configv.username, "w")
                and self.permissionc.check_permission(
                    dir_path, self.configv.username, "x"
                )
            )
            or self.permissionc.is_admin(self.configv.username)
        ):
            return

        # 调用函数递归删除整个文件夹
        shutil.rmtree(file_path)

        cursor.execute(
            "DELETE FROM Files WHERE content_path LIKE %s", (file_path + "%",)
        )
        db.commit()
        print(f"{directory_name} deleted successfully!")

    # dir
    def list_directory(self):
        if not (
            self.permissionc.check_permission(
                self.configv.current_dir, self.configv.username, "r"
            )
            or self.permissionc.is_admin(self.configv.username)
        ):
            return

        db = self.configv.db
        cursor = db.cursor()

        cursor.execute(
            "SELECT filename, physical_address, protection, content_path FROM Users JOIN Files ON Users.user_id = Files.user_id WHERE Files.content_path LIKE %s",
            (self.configv.current_dir + "%",),
        )
        files = cursor.fetchall()

        header = "{:<20} {:<50} {:<10} {:<10}".format(
            "Filename", "Physical Address", "Protection", "Length"
        )
        file_list = [header]

        for file_entry in files:
            if (
                os.path.join(self.configv.current_dir, file_entry[0]) == file_entry[3]
            ):  # 只读取当前子目录下的内容
                line = "{:<20} {:<50} {:<10} {:<10}".format(
                    file_entry[0],
                    file_entry[3],
                    file_entry[2],
                    os.path.getsize(file_entry[3]),
                )
                file_list.append(line)
        print("\n".join(file_list))

    def change_directory(self, directory):  # cd命令的实现
        # 当目录是.，表示当前目录，所以不更改
        if directory == "." or directory == "./":
            return
        elif directory == "..":
            # 如果当前目录不是逻辑基础目录，就向上移动一级
            if self.configv.current_dir != self.configv.BASE_DIR:
                self.configv.current_dir = os.path.dirname(self.configv.current_dir)
        # 当输入/时，设置为逻辑基础目录
        elif directory == "/":
            self.configv.current_dir = self.configv.BASE_DIR
        else:
            # 当给定的是绝对路径或者相对路径
            if os.path.isabs(directory):
                new_path = directory
            else:
                new_path = os.path.join(self.configv.current_dir, directory)
            # 标准化路径，这会处理多余的/或./之类的情况
            new_path = os.path.normpath(new_path).lstrip("/")
            # 额外的检查以确保不会超出逻辑根目录
            if not new_path.startswith(self.configv.BASE_DIR):
                print(f"Directory {directory} is not allowed!")
                return
            if not (
                self.permissionc.check_permission(
                    self.configv.current_dir, self.configv.username, "x"
                )
                or self.permissionc.is_admin(self.configv.username)
            ):
                return
            if os.path.exists(new_path) and os.path.isdir(new_path):
                self.configv.current_dir = new_path
            else:
                print(f"Directory {directory} is not found!")
