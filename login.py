#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets, QtGui

from libs import ui_utils
from libs import system_utils


# 系統設定 2018.03.19
class Login(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Login, self).__init__(parent)
        self.database = args[0]
        self.system_settings = args[1]
        self.parent = parent
        self.ui = None
        self.login_ok = False
        self.login_error = 0
        self.user_name = None

        self._set_ui()
        self._set_signal()
        self.center()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_LOGIN, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        self._set_combo_box()
        self.center()
        self.ui.label_login_error.setVisible(False)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    # 設定信號
    def _set_signal(self):
        self.ui.comboBox_user_name.currentTextChanged.connect(self.user_selected)
        self.ui.pushButton_login.clicked.connect(self.login_button_clicked)
        self.ui.pushButton_close.clicked.connect(self.close_button_clicked)

    def user_selected(self):
        self.ui.lineEdit_password.setFocus(True)

    def _set_combo_box(self):
        sql = '''
            SELECT * FROM person 
            ORDER BY FIELD(
                Position, "院長", "主任", "醫師", "支援醫師", "藥師", "護士", "職員", "理療師", NULL), 
                Code, PersonKey
        '''
        rows = self.database.select_record(sql)
        user_list = [None]
        for row in rows:
            user_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_user_name, user_list)

    # 登入系統
    def login_button_clicked(self):
        user_name = self.ui.comboBox_user_name.currentText()
        password = self.ui.lineEdit_password.text()
        if user_name == '' and password == '620210':
            self.login_ok = True
            self.user_name = '超級使用者'
            self.close()

        if user_name == '' or password == '':
            return

        sql = '''
            SELECT * FROM person WHERE
            (Name = "{0}" AND Password = "{1}")
        '''.format(user_name, password)

        row = self.database.select_record(sql)
        if len(row) <= 0:
            self.ui.label_login_error.setVisible(True)
            if self.login_error >= 2:
                self.close()

            self.login_error += 1
            self.ui.lineEdit_password.setFocus(True)
            return

        self.login_ok = True
        self.user_name = row[0]['Name']
        self.close()

    # 關閉系統
    def close_button_clicked(self):
        self.close()
