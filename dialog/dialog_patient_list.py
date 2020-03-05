#!/usr/bin/env python3
# 病患查詢 2019.03.18
#coding: utf-8

from PyQt5 import QtWidgets
import re
import calendar

from libs import date_utils
from libs import validator_utils
from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import number_utils


# 病患查詢
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
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.label_patient_key.setEnabled(False)
        self.ui.lineEdit_start.setEnabled(False)
        self.ui.label_to.setEnabled(False)
        self.ui.lineEdit_end.setEnabled(False)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.radioButton_all_range.clicked.connect(self._set_patient)
        self.ui.radioButton_range.clicked.connect(self._set_patient)
        self.ui.lineEdit_start.textChanged.connect(self._range_check)
        self.ui.lineEdit_end.textChanged.connect(self._range_check)

    # 設定 mysql script
    def get_sql(self):
        sql = 'SELECT * FROM patient '
        start = string_utils.xstr(self.ui.lineEdit_start.text())
        end = string_utils.xstr(self.ui.lineEdit_end.text())
        condition = None

        if self.ui.radioButton_range.isChecked() and start != '' and end != '':
            sql += '''
                WHERE (PatientKey BETWEEN {0} AND {1})
            '''.format(start, end)
            condition = True

        if self.ui.radioButton_keyword.isChecked():
            keyword = string_utils.xstr(self.ui.lineEdit_keyword.text())
            if keyword.isdigit():
                if len(keyword) >= 7:
                    if not condition:
                        sql += 'WHERE '
                    else:
                        sql += 'AND '

                    sql += '''
                        (Telephone LIKE "%{0}%" OR Cellphone LIKE "%{0}%")
                        ORDER BY PatientKey
                    '''.format(keyword)
                else:
                    sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(keyword)
            else:
                if not condition:
                    sql += 'WHERE '
                else:
                    sql += 'AND '

                if re.compile(validator_utils.DATE_REGEXP).match(keyword):
                    query_str = date_utils.date_to_west_date(keyword)
                    sql += '''
                        Birthday = "{0}"
                        ORDER BY PatientKey
                    '''.format(query_str)
                elif re.compile('^[0-9]{1,4}[-/.][0-9]{1,2}').match(keyword):
                    date_separator = date_utils.get_date_separator(keyword)
                    if date_separator == '':
                        return

                    try:
                        year, month = keyword.split(date_separator)
                    except ValueError:
                        return

                    year = number_utils.get_integer(year)
                    month = number_utils.get_integer(month)
                    if month <= 0:
                        return

                    if year < 1000:
                        year += 1911

                    try:
                        last_day = calendar.monthrange(year, month)[1]
                    except calendar.IllegalMonthError:
                        return

                    start_date = '{year}{separator}{month}{separator}01'.format(
                        year=year,
                        month=month,
                        separator=date_separator,
                    )
                    end_date = '{year}{separator}{month}{separator}{last_day}'.format(
                        year=year,
                        month=month,
                        last_day=last_day,
                        separator=date_separator,
                    )

                    sql += '''
                        Birthday BETWEEN "{0}" AND "{1}"
                        ORDER BY Birthday 
                    '''.format(start_date, end_date)
                elif re.compile('^[0-9]{1,4}[-/.]').match(keyword):
                    if '-' in keyword:
                        separator = '-'
                    elif '/' in keyword:
                        separator = '/'
                    elif '.' in keyword:
                        separator = '.'
                    else:
                        return

                    year, _ = keyword.split(separator)
                    year = number_utils.get_integer(year)
                    if year < 1000:
                        year += 1911

                    start_date = '{year}{separator}01{separator}01'.format(
                        year=year,
                        separator=separator,
                    )
                    end_date = '{year}{separator}12{separator}31'.format(
                        year=year,
                        separator=separator,
                    )

                    sql += '''
                        Birthday BETWEEN "{0}" AND "{1}"
                        ORDER BY Birthday 
                    '''.format(start_date, end_date)
                else:
                    sql += '''
                        ((Name LIKE "%{0}%") OR
                         (ID LIKE "{0}%") OR
                         (Address LIKE "%{0}%") OR
                         (EMail LIKE "%{0}%"))
                         ORDER BY PatientKey
                    '''.format(keyword)

        return sql

    def accepted_button_clicked(self):
        pass

    def _set_patient(self):
        if self.ui.radioButton_all_range.isChecked():
            self.ui.lineEdit_start.setText('')
            self.ui.lineEdit_end.setText('')
            enabled = False
        else:
            enabled = True

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(not enabled)
        self.ui.label_patient_key.setEnabled(enabled)
        self.ui.lineEdit_start.setEnabled(enabled)
        self.ui.label_to.setEnabled(enabled)
        self.ui.lineEdit_end.setEnabled(enabled)

    def _range_check(self):
        if self.ui.lineEdit_start.text() == '' or self.ui.lineEdit_end.text() == '':
            enabled = False
        else:
            enabled = True

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)
