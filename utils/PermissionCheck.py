import os


class PermissionCheck:  # 还需要再调整
    def __init__(self, configv):
        self.configv = configv

    def is_valid_protection(self, protection: str) -> bool:
        # 检查字符串长度是否为9
        if len(protection) != 9:
            return False

        # 检查指定位置的字符是否符合规则
        for i, char in enumerate(protection):
            if i in [0, 3, 6] and char not in ["r", "-"]:
                return False
            elif i in [1, 4, 7] and char not in ["w", "-"]:
                return False
            elif i in [2, 5, 8] and char not in ["x", "-"]:
                return False

        return True

    def is_admin(self, verify_name=None):
        db = self.configv.db
        cursor = db.cursor()
        if not verify_name:
            user_name = self.configv.username
        else:
            user_name = verify_name
        cursor.execute(
            "SELECT group_name FROM `Groups` WHERE group_id=(SELECT group_id FROM Users WHERE username=%s)",
            (user_name,),
        )
        group_data = cursor.fetchone()
        if group_data and group_data[0] == "admin":
            return True
        return False

    def check_permission(self, path, username, operation):  # path只能传入以base为开头的绝对地址
        # Define a mapping from operation to its position in the permission string
        operation_map = {"r": 0, "w": 1, "x": 2}  # r: read, w: write, x: execute

        # Connect to the database to fetch the file/directory's permissions
        db = self.configv.db
        cursor = db.cursor()

        # Get file's protection and owner details
        cursor.execute(
            "SELECT protection, user_id, group_id FROM Files WHERE content_path=%s",
            (path,),
        )
        file_details = cursor.fetchone()

        if not file_details:
            print(f"{path} not found!")
            return False

        protection, owner_id, group_id = file_details

        # Get user's details
        cursor.execute(
            "SELECT user_id, group_id FROM Users WHERE username=%s", (username,)
        )
        user_details = cursor.fetchone()

        if not user_details:
            print(f"User {username} not found!")
            return False

        user_id, user_group_id = user_details

        # Check the role of the user for the file
        if user_id == owner_id:
            role = "owner"
        elif user_group_id == group_id:
            role = "group"
        else:
            role = "other"

        # Define a mapping from role to its position in the protection string
        role_map = {"owner": 0, "group": 3, "other": 6}

        # Check the permission
        permission_position = role_map[role] + operation_map[operation]
        full_name = {"r": "read", "w": "write", "x": "execute"}
        if protection[permission_position] != operation:
            print(
                f"User {username} does not have permission to {full_name[operation]}!"
            )
            return False
        return True
