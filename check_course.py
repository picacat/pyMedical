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
        self.ui.toolButton_find_error.clicked.connect(self._find_error)

    def _find_error(self):
        self.table_widget_errors.find_error(13)

    def open_medical_record(self):
        case_key = self.table_widget_errors.field_value(0)
        self.parent.open_medical_record(case_key)

    def read_data(self):
        month = int(self.apply_month)
        if month > 1:
            year = self.apply_year
            month -= 1
        else:
            year = self.apply_year - 1
            month = 12

        start_date = date_utils.get_start_date_by_year_month(
            str(year), str(month))  # 雙月檢查
        end_date = date_utils.get_end_date_by_year_month(
            self.apply_year, self.apply_month)

        sql = '''
            SELECT 
                *
            FROM cases 
            WHERE
                (CaseDate BETWEEN "{0}" AND "{1}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") AND
                (Treatment IS NOT NULL AND Treatment != "") AND
                (ApplyType = "{2}") 
            ORDER BY PatientKey, CaseDate
        '''.format(start_date, end_date, self.apply_type)
        self.rows = self.database.select_record(sql)

    def row_count(self):
        return len(self.rows)

    def start_check(self):
        self.parent.ui.label_progress.setText('檢查進度: 療程檢查')
        self.read_data()

        self.ui.tableWidget_errors.setRowCount(0)
        for row in self.rows:
            self._insert_record(row)


        self._remove_useless_record()
        self._set_last_month_color()
        self.ui.tableWidget_errors.setAlternatingRowColors(True)

        self._check_course()
        if self.errors <= 0:
            self.ui.toolButton_find_error.setEnabled(False)
        else:
            self.ui.toolButton_find_error.setEnabled(True)

    def _check_course(self):
        self.parent.ui.progressBar.setMaximum(self.ui.tableWidget_errors.rowCount()-1)
        self.parent.ui.progressBar.setValue(0)

        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            errors = 0
            patient_key = self.ui.tableWidget_errors.item(row_no, 3).text()
            card = self.ui.tableWidget_errors.item(row_no, 6).text()
            course = int(self.ui.tableWidget_errors.item(row_no, 7).text())

            try:
                next_patient_key = self.ui.tableWidget_errors.item(row_no+1, 3).text()
                next_card = self.ui.tableWidget_errors.item(row_no+1, 6).text()
                next_course = int(self.ui.tableWidget_errors.item(row_no+1, 7).text())
            except AttributeError:
                next_patient_key = 0
                next_card = None
                next_course = 0

            if next_patient_key == 0:
                pass
            elif (patient_key != next_patient_key):
                if next_course >= 2:
                    self.ui.tableWidget_errors.setItem(
                        row_no+1, 13,
                        QtWidgets.QTableWidgetItem('療程未見首次')
                    )
                    self.errors += 1
                    errors += 1
            else:
                if card != next_card:
                    if course < 6:
                        self.ui.tableWidget_errors.setItem(
                            row_no, 13,
                            QtWidgets.QTableWidgetItem('療程未滿6次')
                        )
                        self._set_row_color(QtGui.QColor('red'), row_no)
                        self.errors += 1
                else:
                    if next_course == course:
                        self.ui.tableWidget_errors.setItem(
                            row_no+1, 13,
                            QtWidgets.QTableWidgetItem('療程重複')
                        )
                        self._set_row_color(QtGui.QColor('red'), row_no+1)
                        self.errors += 1
                    elif next_course - course != 1:
                        self.ui.tableWidget_errors.setItem(
                            row_no+1, 13,
                            QtWidgets.QTableWidgetItem('療程不連續')
                        )
                        self._set_row_color(QtGui.QColor('red'), row_no+1)
                        self.errors += 1


            self.parent.ui.progressBar.setValue(
                self.parent.ui.progressBar.value() + 1
            )

    def _set_row_color(self, color, row_no):
        for column_no in range(self.ui.tableWidget_errors.columnCount()):
            self.ui.tableWidget_errors.item(row_no, column_no).setForeground(color)

    def error_count(self):
        return self.errors

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

    def _insert_record(self, row):
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
            None,
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

