#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets
import re

from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import date_utils
from libs import validator_utils


# 選擇病患  2018.12.25
class DialogSelectPatient(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogSelectPatient, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]

        self.patient_key = None
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_SELECT_PATIENT, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_patient_list = table_widget.TableWidget(self.ui.tableWidget_patient_list, self.database)
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.button_accepted)
        self.ui.buttonBox.rejected.connect(self.button_rejected)
        self.ui.tableWidget_patient_list.doubleClicked.connect(self.table_double_clicked)
        self.ui.lineEdit_query.textChanged.connect(self._query_patient)

    def _set_table_width(self):
        width = [80, 80, 40, 120, 120, 80, 120, 120, 500]
        self.table_widget_patient_list.set_table_heading_width(width)

    def button_accepted(self):
        self.patient_key = self.table_widget_patient_list.field_value(0)

    def button_rejected(self):
        self.patient_key = None

    def table_double_clicked(self):
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).animateClick()

    def get_patient_key(self):
        return self.patient_key

    def _query_patient(self):
        query_str = string_utils.xstr(self.ui.lineEdit_query.text()).strip()
        if query_str == '':
            self.ui.tableWidget_patient_list.setRowCount(0)
            return

        self._read_patient(query_str)
        self.ui.lineEdit_query.setFocus(True)
        self.ui.lineEdit_query.setCursorPosition(len(query_str))

    def _read_patient(self, query_str):
        pattern = re.compile(validator_utils.DATE_REGEXP)
        if pattern.match(query_str):
            query_str = date_utils.date_to_west_date(query_str)
            sql = '''
                SELECT * FROM patient 
                WHERE 
                    Birthday = "{0}"
                ORDER BY PatientKey 
            '''.format(query_str)
        elif query_str.isnumeric():
            if len(query_str) >= 7:
                sql = '''
                    SELECT * FROM patient 
                    WHERE 
                        Telephone LIKE "%{0}%" OR 
                        Cellphone LIKE "%{0}%"
                '''.format(query_str)
            else:
                sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(query_str)
        else:
            sql = '''
                SELECT * FROM patient 
                WHERE 
                    (Name like "%{0}%") or 
                    (ID like "{0}%") or 
                    (Birthday = "{0}")
                ORDER BY PatientKey
            '''.format(query_str)

        rows = self.database.select_record(sql)
        self.table_widget_patient_list.set_db_data(None, self._set_table_data, rows)

    def _set_table_data(self, row_no, row):
        patient_rec = [
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['ID']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Telephone']),
            string_utils.xstr(row['Cellphone']),
            string_utils.xstr(row['Address'])
        ]

        for column in range(len(patient_rec)):
            self.ui.tableWidget_patient_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(patient_rec[column])
            )
