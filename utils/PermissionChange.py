import os
from utils.PermissionCheck import PermissionCheck


class PermissionChange:
    def __init__(self, configv):
        self.configv = configv
        self.permissionc = PermissionCheck(configv)

    def change_protection(self, filename, protection):  # 只有owner和admin组可以改, 只支持相对路径
        if not self.permissionc.is_valid_protection(protection):
            print(f"Invalid protection string {protection}")
            return

        # Connect to the database
        db = self.configv.db
        cursor = db.cursor()

        path = os.path.join(self.configv.current_path, filename)
        cursor.execute("SELECT user_id FROM Files WHERE content_path=%s", (path,))
        user_id = cursor.fetchone()[0]
        if not user_id:
            print(f"File {filename} is not found!")
            return

        cursor.execute(
            "SELECT user_id FROM Users WHERE username=%s", (self.configv.username,)
        )
        current_user_id = cursor.fetchone()[0]

        # Check if the user has write permission to change protection
        if not (self.permissionc.is_admin() or (user_id == current_user_id)):
            print(f"You don't have permission to change protection for {filename}.")
            return

        # Update protection in the database
        cursor.execute(
            "UPDATE Files SET protection=%s WHERE content_path=%s", (protection, path)
        )
        db.commit()
        print(f"Protection for {filename} has been updated to {protection}.")

    def change_user_group(self, username, new_group_name):
        db = self.configv.db
        cursor = db.cursor()

        if not self.permissionc.is_admin():
            print(f"User {self.configv.username} does not have permission!")
            return

        cursor.execute(
            "SELECT group_id FROM `Groups` WHERE group_name=%s", (new_group_name,)
        )
        group_data = cursor.fetchone()
        if not group_data:
            print(f"Group {new_group_name} not found!")
            return

        group_id = group_data[0]
        cursor.execute(
            "UPDATE Users SET group_id=%s WHERE username=%s", (group_id, username)
        )  # 通过绑定相同的group_id确定是否在同一个group
        db.commit()

        cursor.execute(
            "UPDATE Files SET group_id=%s WHERE user_id=(SELECT user_id FROM Users WHERE username=%s)",
            (group_id, username),
        )
        db.commit()
        print(f"User {username} group changed to {new_group_name}!")
