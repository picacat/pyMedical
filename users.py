#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from classes import table_widget
from libs import ui_utils
from libs import string_utils
from dialog import dialog_input_user
from dialog import dialog_permission


# 使用者管理 2018.06.26
class Users(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Users, self).__init__(parent)
        self.parent = parent
        self.args = args
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_users()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_USERS, self)
        self.table_widget_users = table_widget.TableWidget(self.ui.tableWidget_users, self.database)
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_template)
        self.ui.tableWidget_users.doubleClicked.connect(self.open_user_dialog)
        self.ui.toolButton_add_user.clicked.connect(self.add_user)
        self.ui.toolButton_remove_user.clicked.connect(self.remove_user)
        self.ui.toolButton_edit_user.clicked.connect(self.open_user_dialog)
        self.ui.toolButton_permission.clicked.connect(self._set_permission)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_template(self):
        self.close_all()
        self.close_tab()

    # 設定欄位寬度
    def _set_table_width(self):
        width = [
            100,
            80, 100, 100, 50, 120, 120, 100, 50, 180, 150, 80,
            130, 130, 400, 250, 100, 120, 120, 120, 300,
        ]
        self.table_widget_users.set_table_heading_width(width)
        self.table_widget_users.set_column_hidden([0])

    def _read_users(self):
        sql = '''
            SELECT * FROM person 
            ORDER BY FIELD(
                Position, "醫師", "支援醫師", "藥師", "護士", "職員", "理療師", NULL), 
                Code, PersonKey
        '''
        self.table_widget_users.set_db_data(sql, self._set_user_data)

    def _set_user_data(self, row_no, row):
        password = string_utils.xstr(row['Password'])
        if self.system_settings.field('使用者') != '超級使用者':
            password = '********'

        users_rec = [
            string_utils.xstr(row['PersonKey']),
            string_utils.xstr(row['Code']),
            string_utils.xstr(row['Title']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['ID']),
            string_utils.xstr(row['Position']),
            string_utils.xstr(row['FullTime']),
            string_utils.xstr(row['Certificate']),
            string_utils.xstr(row['CertCardNo']),
            password,
            string_utils.xstr(row['Telephone']),
            string_utils.xstr(row['Cellphone']),
            string_utils.xstr(row['Address']),
            string_utils.xstr(row['Email']),
            string_utils.xstr(row['Department']),
            string_utils.xstr(row['InitDate']),
            string_utils.xstr(row['QuitDate']),
            string_utils.xstr(row['InputDate']),
            string_utils.xstr(row['Remark']),
        ]

        for column in range(len(users_rec)):
            self.ui.tableWidget_users.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(users_rec[column])
            )

            if column in [4]:
                self.ui.tableWidget_users.item(row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def open_user_dialog(self):
        person_key = self.table_widget_users.field_value(0)
        dialog = dialog_input_user.DialogInputUser(
            self, self.database, self.system_settings, person_key)

        dialog.exec_()
        dialog.deleteLater()

        sql = 'SELECT * FROM person WHERE PersonKey = {0}'.format(person_key)
        row_data = self.database.select_record(sql)[0]
        self._set_user_data(self.ui.tableWidget_users.currentRow(), row_data)

    # 新增使用者資料
    def add_user(self):
        person_key = None
        dialog = dialog_input_user.DialogInputUser(
            self, self.database, self.system_settings, person_key)
        result = dialog.exec_()
        if result != 0:
            sql = 'SELECT * FROM person ORDER BY PersonKey desc limit 1'
            row_data = self.database.select_record(sql)[0]
            row_no = self.ui.tableWidget_users.rowCount()
            self.ui.tableWidget_users.insertRow(row_no)
            self._set_user_data(row_no, row_data)

        dialog.close_all()
        dialog.deleteLater()

    # 移除使用者資料
    def remove_user(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除使用者資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此筆使用者資料?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        key = self.table_widget_users.field_value(0)
        self.database.delete_record('person', 'PersonKey', key)
        self.ui.tableWidget_users.removeRow(self.ui.tableWidget_users.currentRow())

    # 編輯使用者資料
    def edit_user(self):
        self.open_user_dialog()

    # 設定權限
    def _set_permission(self):
        person_key = self.table_widget_users.field_value(0)
        if person_key is None:
            return

        dialog = dialog_permission.DialogPermission(self, self.database, self.system_settings, person_key)
        dialog.exec_()
        dialog.deleteLater()
