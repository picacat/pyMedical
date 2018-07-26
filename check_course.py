#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import datetime

from classes import table_widget

from libs import ui_utils
from libs import date_utils
from libs import number_utils
from libs import string_utils
from libs import validator_utils
from libs import personnel_utils
from libs import nhi_utils


# 候診名單 2018.01.31
class CheckCourse(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckCourse, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = int(args[2])
        self.apply_month = int(args[3])
        self.apply_type = args[4]
        self.ui = None
        self.doctor_list = personnel_utils.get_personnel(self.database, '醫師')

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_app(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHECK_COURSE, self)
        self._set_table_widget()

    def _set_table_widget(self):
        self.table_widget_errors = table_widget.TableWidget(self.ui.tableWidget_errors, self.database)
        self.table_widget_errors.set_column_hidden([0])
        width = [
            100, 120, 60, 80, 80, 100, 70, 30, 100, 180, 100,
            80, 80, 250,
        ]
        self.table_widget_errors.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_errors.doubleClicked.connect(self.open_medical_record)
        # self.ui.action_close.triggered.connect(self.close_app)

    def open_medical_record(self):
        case_key = self.table_widget_errors.field_value(0)
        self.parent.open_medical_record(case_key)

    def start_check(self):
        month = int(self.apply_month)
        if month > 1:
            month -= 1
        else:
            month = 12

        start_date = date_utils.get_start_date_by_year_month(
            self.apply_year, str(month))
        end_date = date_utils.get_end_date_by_year_month(
            self.apply_year, self.apply_month)
        if self.apply_type == '申報':
            apply_condition = \
                'AND (ApplyType = "{0}" OR ApplyType = "調劑不報" OR ApplyType = "")'.format(
                    self.apply_type)  # for 友杏
        else:
            apply_condition = 'AND (ApplyType = "{0}"))'.format(self.apply_type)

        sql = '''
            SELECT 
                *
            FROM cases 
            WHERE
                (CaseDate BETWEEN "{0}" AND "{1}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") AND
                (Continuance >= 1)
                {2}
            ORDER BY PatientKey, CaseDate
        '''.format(start_date, end_date, apply_condition)
        rows = self.database.select_record(sql)

        self.ui.tableWidget_errors.setRowCount(0)
        for row in rows:
            error_messages = []
            self._insert_error_record(row, error_messages)

        self._remove_useless_record()
        self._set_last_month_color()

    def _remove_useless_record(self):
        for row_no in reversed(range(self.ui.tableWidget_errors.rowCount())):
            case_date = self.ui.tableWidget_errors.item(row_no, 1).text()
            start_date = date_utils.get_start_date_by_year_month(
                self.apply_year, self.apply_month)
            if (datetime.datetime.strptime(case_date, '%Y-%m-%d') <
                    datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')):
                self._check_remove_need(row_no)

    def _check_remove_need(self, row_no):
        start_date = date_utils.get_start_date_by_year_month(
            self.apply_year, self.apply_month)
        patient_key = self.ui.tableWidget_errors.item(row_no, 3).text()
        card = self.ui.tableWidget_errors.item(row_no, 6).text()
        sql = '''
            SELECT CaseKey FROM cases WHERE
            PatientKey = {0} AND Card = "{1}" AND
            CaseDate >= "{2}"
        '''.format(patient_key, card, start_date)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            self.ui.tableWidget_errors.removeRow(row_no)

    def _set_last_month_color(self):
        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            case_date = self.ui.tableWidget_errors.item(row_no, 1).text()
            start_date = date_utils.get_start_date_by_year_month(
                self.apply_year, self.apply_month)
            if (datetime.datetime.strptime(case_date, '%Y-%m-%d') <
                    datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')):
                for column in range(0, self.ui.tableWidget_errors.columnCount()):
                    self.ui.tableWidget_errors.item(row_no, column).setForeground(
                        QtGui.QColor('darkGray'))

    def _insert_error_record(self, row, error_messages):
        row_no = self.ui.tableWidget_errors.rowCount()
        self.ui.tableWidget_errors.setRowCount(row_no + 1)
        error_record = [
            string_utils.xstr(row['CaseKey']),
            '{0}-{1:0>2}-{2:0>2}'.format(
                row['CaseDate'].year, row['CaseDate'].month, row['CaseDate'].day
            ),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Continuance']),
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['Treatment']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(
                number_utils.get_integer(row['AcupunctureFee']) +
                number_utils.get_integer(row['MassageFee']) +
                number_utils.get_integer(row['DislocateFee'])
            ),
            ', '.join(error_messages),
        ]
        for column_no in range(len(error_record)):
            self.ui.tableWidget_errors.setItem(
                row_no, column_no,
                QtWidgets.QTableWidgetItem(error_record[column_no])
            )
            if column_no in [7]:
                self.ui.tableWidget_errors.item(
                    row_no, column_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            elif column_no in [3, 12]:
                self.ui.tableWidget_errors.item(
                    row_no, column_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _check_patient(self, row):
        error_messages = []

        if self._check_patient_error_exists(row['PatientKey']):
            return error_messages

        if string_utils.xstr(row['Name']) == '':
            error_messages.append('姓名空白')
        try:
            if row['Birthday'] > row['CaseDate']:
                error_messages.append('生日不合理')
        except:
            if string_utils.xstr(row['Birthday']) == '':
                error_messages.append('生日空白')

        if string_utils.xstr(row['ID']) == '':
            error_messages.append('身分證空白')
        if not validator_utils.verify_id(string_utils.xstr(row['ID'])):
            error_messages.append('身份證錯誤')
        if string_utils.xstr(row['InsType']) == '':
            error_messages.append('保險類別空白')

        return error_messages

    def _check_patient_error_exists(self, patient_key):
        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            if self.ui.tableWidget_errors.item(row_no, 3).text() == string_utils.xstr(patient_key):
                return True

        return  False

    def _check_medical_record(self, row):
        error_messages = []

        if string_utils.xstr(row['Card']) == '':
            error_messages.append('卡序空白')
        if string_utils.xstr(row['Doctor']) == '':
            error_messages.append('無醫師')
        elif string_utils.xstr(row['Doctor']) not in self.doctor_list:
            error_messages.append('非醫師')
        if (string_utils.xstr(row['Treatment']) in nhi_utils.INS_TREAT and
                number_utils.get_integer(row['Continuance']) < 1):
            error_messages.append('非療程')
        if string_utils.xstr(row['DiseaseCode1']) == '':
            error_messages.append('無主診斷碼')
        elif string_utils.xstr(row['DiseaseCode1'])[0] in [str(i) for i in range(10)]:
            error_messages.append('非ICD10碼')

        return error_messages
