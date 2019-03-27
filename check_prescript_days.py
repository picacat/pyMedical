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
class CheckPrescriptDays(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckPrescriptDays, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = int(args[2])
        self.apply_month = int(args[3])
        self.apply_type = args[4]
        self.duplicated_days = args[5]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHECK_PRESCRIPT_DAYS, self)
        self._set_table_widget()

    def _set_table_widget(self):
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_medical_record, self.database)
        self.table_widget_medical_record.set_column_hidden([0])
        width = [
            100, 120, 60, 80, 80, 100, 70, 30, 50, 100, 400, 100,
            80, 80, 250,
        ]
        self.table_widget_medical_record.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_medical_record.doubleClicked.connect(self.open_medical_record)
        self.ui.toolButton_find_error.clicked.connect(self._find_error)

    def _find_error(self):
        self.table_widget_medical_record.find_error(14)

    def open_medical_record(self):
        case_key = self.table_widget_medical_record.field_value(0)
        self.parent.open_medical_record(case_key)

    def read_data(self):
        sql = '''
            SELECT 
                cases.*, dosage.* 
            FROM cases 
                LEFT JOIN dosage ON dosage.CaseKey = cases.CaseKey
            WHERE
                (CaseDate BETWEEN "{0}" AND "{1}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") AND
                (dosage.MedicineSet = 1) AND
                (dosage.Days > 0) AND
                (cases.ApplyType = "{2}")
            ORDER BY PatientKey, CaseDate
        '''.format(self.start_date, self.end_date, self.apply_type)
        self.rows = self.database.select_record(sql)

    def row_count(self):
        return len(self.rows)

    def start_check(self):
        self.parent.ui.label_progress.setText('檢查進度: 用藥天數檢查')
        self.read_data()

        self.parent.ui.progressBar.setMaximum(self.row_count()-1)
        self.parent.ui.progressBar.setValue(0)

        self.ui.tableWidget_medical_record.setRowCount(0)
        for row_no, row in zip(range(len(self.rows)), self.rows):
            error_messages = []
            error_messages += self._check_duplicated_days(row_no, row)
            self._insert_error_record(row, error_messages)

            self.parent.ui.progressBar.setValue(
                self.parent.ui.progressBar.value() + 1
            )

        self.ui.tableWidget_medical_record.setAlternatingRowColors(True)
        if self.errors <= 0:
            self.ui.toolButton_find_error.setEnabled(False)
        else:
            self.ui.toolButton_find_error.setEnabled(True)

        self.parent.ui.label_progress.setText('檢查進度: 檢查完成')
        self.ui.tableWidget_medical_record.resizeRowsToContents()

    def _check_duplicated_days(self, row_no, row):
        error_message = []

        patient_key = string_utils.xstr(row['PatientKey'])
        try:
            last_case_date = datetime.datetime.strptime(
                self.ui.tableWidget_medical_record.item(row_no-1, 1).text(), '%Y-%m-%d').date()
            last_patient_key = self.ui.tableWidget_medical_record.item(row_no-1, 3).text()
            last_prescript_days = int(self.ui.tableWidget_medical_record.item(row_no-1, 8).text())
        except AttributeError:
            last_case_date = None
            last_patient_key = None
            last_prescript_days = 0

        if patient_key == last_patient_key:
            duplicated_days = (last_case_date +
                               datetime.timedelta(
                                   days=last_prescript_days + self.duplicated_days - 1) -
                               row['CaseDate'].date()).days
            if duplicated_days > 0:
                error_message.append('給藥重複{0}日'.format(duplicated_days))
                self.errors += 1

        return error_message

    def error_count(self):
        return self.errors

    def _insert_error_record(self, row, error_messages):
        row_no = self.ui.tableWidget_medical_record.rowCount()
        self.ui.tableWidget_medical_record.setRowCount(row_no + 1)

        medical_record = [
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
            string_utils.xstr(row['Days']),
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['InterDrugFee']),
            string_utils.xstr(row['PharmacyFee']),
            ', '.join(error_messages),
        ]
        for column_no in range(len(medical_record)):
            self.ui.tableWidget_medical_record.setItem(
                row_no, column_no,
                QtWidgets.QTableWidgetItem(medical_record[column_no])
            )
            if column_no in [7]:
                self.ui.tableWidget_medical_record.item(
                    row_no, column_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            elif column_no in [3, 8, 12, 13]:
                self.ui.tableWidget_medical_record.item(
                    row_no, column_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

            if len(error_messages) > 0:
                color = QtGui.QColor('red')
                self.ui.tableWidget_medical_record.item(row_no, column_no).setForeground(color)
