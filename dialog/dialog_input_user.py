#!/usr/bin/env python3
# 輸入處方 2018.06.15
#coding: utf-8

import datetime
from PyQt5 import QtWidgets
from libs import ui_utils
from libs import nhi_utils
from libs import system_utils
from libs import string_utils


# 主視窗
class DialogInputUser(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInputUser, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        try:
            self.person_key = args[2]
        except IndexError:
            self.person_key = None

        self.ui = None

        self._set_ui()
        self._set_signal()
        if self.person_key is not None:
            self._read_person()
        else:
            self._add_person()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INPUT_USER, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('存檔')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self._set_combo_box()
        self.ui.lineEdit_name.setFocus()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    # 設定 comboBox
    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_gender, nhi_utils.GENDER, None)
        ui_utils.set_combo_box(self.ui.comboBox_position, nhi_utils.POSITION, None)
        ui_utils.set_combo_box(self.ui.comboBox_fulltime, nhi_utils.FULLTIME, None)

    def _read_person(self):
        sql = 'SELECT * FROM person WHERE PersonKey = {0}'.format(self.person_key)
        row = self.database.select_record(sql)[0]
        self.ui.lineEdit_code.setText(string_utils.xstr(row['Code']))
        self.ui.lineEdit_name.setText(string_utils.xstr(row['Name']))
        self.ui.comboBox_gender.setCurrentText(string_utils.xstr(row['Gender']))
        self.ui.lineEdit_birthday.setText(string_utils.xstr(row['Birthday']))
        self.ui.lineEdit_id.setText(string_utils.xstr(row['ID']))
        self.ui.comboBox_position.setCurrentText(string_utils.xstr(row['Position']))
        self.ui.comboBox_fulltime.setCurrentText(string_utils.xstr(row['FullTime']))
        self.ui.lineEdit_certificate.setText(string_utils.xstr(row['Certificate']))
        self.ui.lineEdit_password.setText(string_utils.xstr(row['Password']))
        self.ui.lineEdit_telephone.setText(string_utils.xstr(row['Telephone']))
        self.ui.lineEdit_cellphone.setText(string_utils.xstr(row['Cellphone']))
        self.ui.lineEdit_address.setText(string_utils.xstr(row['Address']))
        self.ui.lineEdit_email.setText(string_utils.xstr(row['Email']))
        self.ui.lineEdit_department.setText(string_utils.xstr(row['Department']))
        self.ui.lineEdit_input_date.setText(string_utils.xstr(row['InputDate']))
        self.ui.lineEdit_init_date.setText(string_utils.xstr(row['InitDate']))
        self.ui.lineEdit_quit_date.setText(string_utils.xstr(row['QuitDate']))
        self.ui.lineEdit_remark.setText(row['Remark'])

    def _add_person(self):
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.ui.lineEdit_input_date.setText(today)

    def accepted_button_clicked(self):
        self.save_user()

    def save_user(self):
        fields = [
            'Code', 'Name', 'Gender', 'Birthday', 'ID', 'Position',
            'FullTime', 'Certificate', 'Password', 'Telephone', 'Cellphone', 'Address', 'Email',
            'Department', 'InputDate', 'InitDate', 'QuitDate', 'Remark',
        ]
        data = [
            self.ui.lineEdit_code.text(),
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_gender.currentText(),
            self.ui.lineEdit_birthday.text(),
            self.ui.lineEdit_id.text(),
            self.ui.comboBox_position.currentText(),
            self.ui.comboBox_fulltime.currentText(),
            self.ui.lineEdit_certificate.text(),
            self.ui.lineEdit_password.text(),
            self.ui.lineEdit_telephone.text(),
            self.ui.lineEdit_cellphone.text(),
            self.ui.lineEdit_address.text(),
            self.ui.lineEdit_email.text(),
            self.ui.lineEdit_department.text(),
            self.ui.lineEdit_input_date.text(),
            self.ui.lineEdit_init_date.text(),
            self.ui.lineEdit_quit_date.text(),
            self.ui.lineEdit_remark.text(),
        ]

        if self.person_key is not None:
            self.database.update_record('person', fields, 'PersonKey',
                                        self.person_key, data)
        else:
            self.database.insert_record('person', fields, data)
