#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import datetime

from classes import table_widget

from libs import ui_utils
from libs import date_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils


# 候診名單 2018.01.31
class CheckInsTreat(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckInsTreat, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHECK_INS_TREAT, self)
        system_utils.set_css(self, self.system_settings)
        self.center()
        self._set_table_widget()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def _set_table_widget(self):
        self.table_widget_prescript = table_widget.TableWidget(
            self.ui.tableWidget_prescript, self.database)
        self.table_widget_prescript.set_column_hidden([0])
        width = [
            100, 120, 80, 80, 120, 180, 80, 40,
            120, 300, 150, 80, 250,
        ]
        self.table_widget_prescript.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_prescript.doubleClicked.connect(self.open_medical_record)
        self.ui.toolButton_find_error.clicked.connect(self._find_error)

    def _find_error(self):
        self.table_widget_prescript.find_error(12)

    def open_medical_record(self):
        case_key = self.table_widget_prescript.field_value(0)
        self.parent.open_medical_record(case_key)

    def read_data(self):
        apply_type_sql = nhi_utils.get_apply_type_sql(self.apply_type)

        sql = '''
            SELECT
                *
            FROM cases
                LEFT JOIN presextend ON presextend.PrescriptKey = cases.CaseKey
            WHERE
                (cases.CaseDate BETWEEN "{start_date}" AND "{end_date}") AND
                (cases.InsType = "健保") AND
                (Treatment IS NOT NULL AND Treatment != "") AND
                ({apply_type_sql})
            ORDER BY PatientKey, CaseDate
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            apply_type_sql=apply_type_sql,
        )
        self.rows = self.database.select_record(sql)

    def row_count(self):
        return len(self.rows)

    def start_check(self):
        self.read_data()
        if self.row_count() <= 0:
            return

        progress_dialog = QtWidgets.QProgressDialog(
            '正在執行健保碼檢查中, 請稍後...', '取消', 0, self.row_count(), self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        self.ui.tableWidget_prescript.setRowCount(0)
        for row_no, row in zip(range(len(self.rows)), self.rows):
            error_messages = []
            error_messages += self._check_treats(row_no, row)
            self._insert_error_record(row_no, row, error_messages)

            progress_dialog.setValue(row_no)

        progress_dialog.setValue(self.row_count())

        self.ui.tableWidget_prescript.setAlternatingRowColors(True)
        if self.errors <= 0:
            self.ui.toolButton_find_error.setEnabled(False)
        else:
            self.ui.toolButton_find_error.setEnabled(True)

        self.ui.tableWidget_prescript.resizeRowsToContents()

    def _check_treats(self, row_no, row):
        error_message = []
        case_date = row['CaseDate'].date()
        case_key = string_utils.xstr(row['CaseKey'])
        patient_key = string_utils.xstr(row['PatientKey'])
        treatment = string_utils.xstr(row['Treatment'])
        treats = ','.join(self._get_ins_treat(case_key))

        try:
            last_case_date = datetime.datetime.strptime(
                self.ui.tableWidget_prescript.item(row_no-1, 1).text(), '%Y-%m-%d').date()
            last_patient_key = self.ui.tableWidget_prescript.item(row_no-1, 2).text()
            last_treats = self.ui.tableWidget_prescript.item(row_no-1, 9).text()
        except AttributeError:
            last_case_date = None
            last_patient_key = 0
            last_treats = ''

        if patient_key == last_patient_key:
            error_message += self._check_same_acupuncture(
                case_date, last_case_date, treatment,
                treats, last_treats
            )
            error_message += self._check_null_treats(treatment, treats)

        return error_message

    def _check_same_acupuncture(self, case_date, last_case_date, treatment, treats, last_treats):
        error_message = []
        if (treats == last_treats and
                case_date - datetime.timedelta(days=1) == last_case_date and
                '針' in treatment):
            error_message.append('隔日針灸, 穴位相同')
            self.errors += 1

        return error_message

    def _check_null_treats(self, treatment, treats):
        error_message = []
        if len(treats) <= 0:
            if '針' in treatment:
                error_message.append('無穴道')
            else:
                error_message.append('無處置')

            self.errors += 1

        return error_message

    def error_count(self):
        return self.errors

    def _insert_error_record(self, row_no, row, error_messages):
        row_no = self.ui.tableWidget_prescript.rowCount()
        self.ui.tableWidget_prescript.setRowCount(row_no + 1)

        case_key = string_utils.xstr(row['CaseKey'])
        treats = self._get_ins_treat(case_key)

        medical_record = [
            case_key,
            '{0}-{1:0>2}-{2:0>2}'.format(
                row['CaseDate'].year, row['CaseDate'].month, row['CaseDate'].day
            ),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Continuance']),
            string_utils.xstr(row['Treatment']),
            ','.join(treats),
            string_utils.xstr(row['Content']),
            string_utils.xstr(row['Doctor']),
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
            elif column_no in [7]:
                self.ui.tableWidget_prescript.item(
                    row_no, column_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            if len(error_messages) > 0:
                color = QtGui.QColor('red')
                self.ui.tableWidget_prescript.item(row_no, column_no).setForeground(color)

    def _get_ins_treat(self, case_key):
        treat_list = []

        sql = '''
            SELECT * FROM prescript WHERE
                CaseKey = {0} AND
                MedicineSet = 1 AND
                MedicineType IN ("穴道", "處置")
            ORDER BY MedicineName
        '''.format(case_key)
        rows = self.database.select_record(sql)

        for row in rows:
            treat_list.append(row['MedicineName'])

        return treat_list
