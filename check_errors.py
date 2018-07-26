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
class CheckErrors(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckErrors, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHECK_ERRORS, self)
        self._set_table_widget()

    def _set_table_widget(self):
        self.table_widget_errors = table_widget.TableWidget(self.ui.tableWidget_errors, self.database)
        self.table_widget_errors.set_column_hidden([0])
        width = [
            100, 120, 60, 80, 80, 120, 120, 100, 80, 100,
            80, 60, 60, 60, 60, 60, 60, 60, 250,
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
        start_date = date_utils.get_start_date_by_year_month(
            self.apply_year, self.apply_month)
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
                cases.*, patient.*
            FROM cases 
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                (CaseDate BETWEEN "{0}" AND "{1}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") {2}
            ORDER BY CaseDate
        '''.format(start_date, end_date, apply_condition)
        rows = self.database.select_record(sql)

        self.ui.tableWidget_errors.setRowCount(0)
        for row in rows:
            error_messages = []
            error_messages += self._check_patient(row)
            error_messages += self._check_medical_record(row)

            if len(error_messages) > 0:
                self._insert_error_record(row, error_messages)

    def _insert_error_record(self, row, error_messages):
        row_no = self.ui.tableWidget_errors.rowCount()
        self.ui.tableWidget_errors.setRowCount(row_no + 1)
        card = string_utils.xstr(row['Card']) \
            if string_utils.xstr(row['Continuance']) == '' \
            else string_utils.xstr(row['Card']) + '-' + string_utils.xstr(row['Continuance'])
        error_record = [
            string_utils.xstr(row['CaseKey']),
            '{0}-{1:0>2}-{2:0>2}'.format(
                row['CaseDate'].year, row['CaseDate'].month, row['CaseDate'].day
            ),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['ID']),
            string_utils.xstr(row['Share']),
            card,
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['DiagFee']),
            string_utils.xstr(row['InterDrugFee']),
            string_utils.xstr(row['PharmacyFee']),
            string_utils.xstr(
                number_utils.get_integer(row['AcupunctureFee']) +
                number_utils.get_integer(row['MassageFee']) +
                number_utils.get_integer(row['DislocateFee'])
            ),
            string_utils.xstr(row['DiagShareFee']),
            string_utils.xstr(row['DrugShareFee']),
            string_utils.xstr(row['InsApplyFee']),
            ', '.join(error_messages),
        ]
        for column_no in range(len(error_record)):
            self.ui.tableWidget_errors.setItem(
                row_no, column_no,
                QtWidgets.QTableWidgetItem(error_record[column_no])
            )
            if column_no in [3, 11, 12, 13, 14, 15, 16, 17]:
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
