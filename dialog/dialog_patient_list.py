#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from libs import system_utils
from libs import ui_utils
from libs import string_utils


# 主視窗
class DialogPatientList(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogPatientList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_PATIENT_LIST, self)
        system_utils.set_css(self)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    # 設定 mysql script
    def get_sql(self):
        sql = 'SELECT * FROM patient '
        start = string_utils.xstr(self.ui.lineEdit_start.text())
        end = string_utils.xstr(self.ui.lineEdit_end.text())

        if self.ui.radioButton_all.isChecked():
            sql = 'SELECT * FROM patient '
            if self.ui.radioButton_range.isChecked():
                sql += '''
                    WHERE (PatientKey BETWEEN {0} AND {1})
                '''.format(start, end)
        elif self.ui.radioButton_keyword.isChecked():
            keyword = string_utils.xstr(self.ui.lineEdit_keyword.text())
            if keyword.isnumeric():
                if len(keyword) >= 7:
                    sql = '''
                        SELECT * FROM patient WHERE Telephone like "%{0}%" or Cellphone like "%{0}%"
                    '''.format(keyword)
                else:
                    sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(keyword)
            else:
                sql = '''
                    SELECT * FROM patient WHERE 
                        (Name LIKE "%{0}%") OR
                        (ID LIKE "{0}%") OR
                        (Birthday = "{0}") OR
                        (Address LIKE "%{0}%") OR
                        (EMail LIKE "%{0}%")
                '''.format(keyword)
                if self.ui.radioButton_range.isChecked():
                    sql += '''
                        AND (PatientKey BETWEEN {0} AND {1})
                    '''.format(start, end)

        sql += ' ORDER BY PatientKey'

        return sql

    def accepted_button_clicked(self):
        pass
