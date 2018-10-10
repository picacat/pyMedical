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
class CheckInsDrug(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckInsDrug, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = int(args[2])
        self.apply_month = int(args[3])
        self.apply_type = args[4]
        self.ui = None

        self.start_date = date_utils.get_start_date_by_year_month(
            self.apply_year, self.apply_month)
        self.end_date = date_utils.get_end_date_by_year_month(
            self.apply_year, self.apply_month)
        self.errors = 0

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHECK_INS_DRUG, self)
        self._set_table_widget()

    def _set_table_widget(self):
        self.table_widget_prescript = table_widget.TableWidget(
            self.ui.tableWidget_prescript, self.database)
        self.table_widget_prescript.set_column_hidden([0])
        width = [
            100, 120, 80, 80, 100, 180,
            120, 150, 180, 120, 200, 250,
        ]
        self.table_widget_prescript.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_prescript.doubleClicked.connect(self.open_medical_record)
        self.ui.toolButton_find_error.clicked.connect(self._find_error)

    def _find_error(self):
        self.table_widget_prescript.find_error(11)

    def open_medical_record(self):
        case_key = self.table_widget_prescript.field_value(0)
        self.parent.open_medical_record(case_key)

    def read_data(self):
        sql = '''
            SELECT 
                prescript.MedicineName, prescript.Dosage, prescript.InsCode, 
                cases.CaseKey, cases.CaseDate, cases.PatientKey, cases.Name, 
                cases.Doctor,
                presextend.Content,
                drug.Supplier, drug.DrugName, drug.ValidDate
            FROM prescript 
                LEFT JOIN cases ON prescript.CaseKey = cases.CaseKey
                LEFT JOIN drug ON prescript.InsCode = drug.InsCode
                LEFT JOIN presextend ON presextend.PrescriptKey = prescript.PrescriptKey
            WHERE
                (cases.CaseDate BETWEEN "{0}" AND "{1}") AND
                (cases.InsType = "健保") AND
                (cases.Card != "欠卡") AND
                (prescript.MedicineSet = 1) AND
                (prescript.InsCode IS NOT NULL) AND
                (prescript.MedicineType IN ("單方", "複方")) AND
                (cases.ApplyType = "{2}")
            ORDER BY cases.PatientKey, cases.CaseKey, prescript.PrescriptKey
        '''.format(self.start_date, self.end_date, self.apply_type)
        self.rows = self.database.select_record(sql)

    def row_count(self):
        return len(self.rows)

    def start_check(self):
        self.ui.tableWidget_prescript.setRowCount(0)
        for row_no, row in zip(range(len(self.rows)), self.rows):
            error_messages = []
            error_messages += self._check_valid_date(row)
            error_messages += self._check_drug_name(row)
            self._insert_error_record(row_no, row, error_messages)

            self.parent.ui.progressBar.setValue(
                self.parent.ui.progressBar.value() + 1
            )

        self.ui.tableWidget_prescript.setAlternatingRowColors(True)
        if self.errors <= 0:
            self.ui.toolButton_find_error.setEnabled(False)
        else:
            self.ui.toolButton_find_error.setEnabled(True)

    def _check_valid_date(self, row):
        error_message = []
        if row['ValidDate'] is None:
            error_message.append('健保藥碼無效')
        elif row['CaseDate'].date() > row['ValidDate']:
            error_message.append('有效期限過期')

        if len(error_message) > 0:
            self.errors += 1

        return error_message

    def _check_drug_name(self, row):
        error_message = []
        if string_utils.xstr(row['DrugName']) not in string_utils.xstr(row['MedicineName']):
            error_message.append('健保藥名不一致')

        return error_message

    def error_count(self):
        return self.errors

    def _insert_error_record(self, row_no, row, error_messages):
        row_no = self.ui.tableWidget_prescript.rowCount()
        self.ui.tableWidget_prescript.setRowCount(row_no + 1)

        case_key = string_utils.xstr(row['CaseKey'])
        try:
            last_case_key = self.ui.tableWidget_prescript.item(row_no-1, 0).text()
        except AttributeError:
            last_case_key = 0

        case_date = '{0}-{1:0>2}-{2:0>2}'.format(
            row['CaseDate'].year, row['CaseDate'].month, row['CaseDate'].day
        )
        patient_key = string_utils.xstr(row['PatientKey'])
        name = string_utils.xstr(row['Name'])
        doctor = string_utils.xstr(row['Doctor'])
        if case_key == last_case_key:
            case_date = ''
            patient_key = ''
            name = ''
            doctor = ''

        medical_record = [
            case_key,
            case_date,
            patient_key,
            name,
            doctor,
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['Supplier']),
            string_utils.xstr(row['DrugName']),
            string_utils.xstr(row['ValidDate']),
            string_utils.xstr(row['Content']),
            ', '.join(error_messages),
        ]
        for column_no in range(len(medical_record)):
            self.ui.tableWidget_prescript.setItem(
                row_no, column_no,
                QtWidgets.QTableWidgetItem(medical_record[column_no])
            )
            if column_no in [2]:
                self.ui.tableWidget_prescript.item(
                    row_no, column_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            if len(error_messages) > 0:
                if '健保藥名不一致' in error_messages:
                    color = QtGui.QColor('green')
                else:
                    color = QtGui.QColor('red')

                self.ui.tableWidget_prescript.item(row_no, column_no).setForeground(color)
