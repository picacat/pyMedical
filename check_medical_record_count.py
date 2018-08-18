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
class CheckMedicalRecordCount(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckMedicalRecordCount, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = int(args[2])
        self.apply_month = int(args[3])
        self.apply_type = args[4]
        self.treat_limit = args[5]
        self.diag_limit = args[6]
        self.ui = None

        self.start_date = date_utils.get_start_date_by_year_month(
            self.apply_year, self.apply_month)
        self.end_date = date_utils.get_end_date_by_year_month(
            self.apply_year, self.apply_month)

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHECK_MEDICAL_RECORD_COUNT, self)
        self._set_table_widget()
        self.ui.label_treat_limit.setText(
            '針傷次數限制: {0}次'.format(self.treat_limit)
        )
        self.ui.label_diag_limit.setText(
            '首次次數限制: {0}次'.format(self.diag_limit)
        )

    def _set_table_widget(self):
        self.table_widget_patient_treat = table_widget.TableWidget(
            self.ui.tableWidget_patient_treat, self.database)
        self.table_widget_medical_record_treat = table_widget.TableWidget(
            self.ui.tableWidget_medical_record_treat, self.database)

        self.table_widget_patient_diag = table_widget.TableWidget(
            self.ui.tableWidget_patient_diag, self.database)
        self.table_widget_medical_record_diag = table_widget.TableWidget(
            self.ui.tableWidget_medical_record_diag, self.database)

        self.table_widget_medical_record_treat.set_column_hidden([0])
        self.table_widget_medical_record_diag.set_column_hidden([0])

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_medical_record_treat.doubleClicked.connect(self.open_medical_record)
        self.ui.tableWidget_medical_record_diag.doubleClicked.connect(self.open_medical_record)
        self.ui.tableWidget_patient_treat.itemSelectionChanged.connect(self._patient_treat_changed)
        self.ui.tableWidget_patient_diag.itemSelectionChanged.connect(self._patient_diag_changed)
        self.ui.toolButton_treat_unapply.clicked.connect(self._set_treat_apply)
        self.ui.toolButton_treat_apply.clicked.connect(self._set_treat_apply)
        self.ui.toolButton_diag_unapply.clicked.connect(self._set_diag_apply)
        self.ui.toolButton_diag_apply.clicked.connect(self._set_diag_apply)


    def _get_case_key(self, table_widget_name):
        if table_widget_name == 'tableWidget_medical_record_treat':
            case_key = self.table_widget_medical_record_treat.field_value(0)
        else:
            case_key = self.table_widget_medical_record_diag.field_value(0)

        return case_key

    def open_medical_record(self):
        case_key = self._get_case_key(self.sender().objectName())
        self.parent.open_medical_record(case_key)

    def start_check(self):
        self._check_medical_record_treat()
        self._check_medical_record_diag()

    def error_count(self):
        return (self.ui.tableWidget_patient_treat.rowCount() +
                self.ui.tableWidget_patient_diag.rowCount())

    def _check_medical_record_treat(self):
        sql = '''
            SELECT 
               PatientKey, Name, Count(PatientKey) AS Count 
            FROM cases 
            WHERE
                (CaseDate BETWEEN "{0}" AND "{1}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") AND 
                (Treatment IS NOT NULL)
            GROUP BY PatientKey
            HAVING COUNT(PatientKey) > {2}
        '''.format(self.start_date, self.end_date, self.treat_limit)

        self.table_widget_patient_treat.set_db_data(sql, self._set_patient_treat_data)

    def _set_patient_treat_data(self, rec_no, rec):
        exceed_count = number_utils.get_integer(rec['Count']) - self.treat_limit
        patient_row = [
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Count']),
            str(exceed_count)
        ]

        for column in range(0, self.ui.tableWidget_patient_treat.columnCount()):
            self.ui.tableWidget_patient_treat.setItem(
                rec_no, column, QtWidgets.QTableWidgetItem(patient_row[column]))
            if column in [0, 2, 3]:
                self.ui.tableWidget_patient_treat.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _check_medical_record_diag(self):
        sql = '''
            SELECT 
               PatientKey, Name, Count(PatientKey) AS Count 
            FROM cases 
            WHERE
                (CaseDate BETWEEN "{0}" AND "{1}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") AND 
                ((Continuance IS NULL) OR (Continuance <= 1))
            GROUP BY PatientKey
            HAVING COUNT(PatientKey) > {2}
        '''.format(self.start_date, self.end_date, self.diag_limit)

        self.table_widget_patient_diag.set_db_data(sql, self._set_patient_diag_data)

    def _set_patient_diag_data(self, rec_no, rec):
        exceed_count = number_utils.get_integer(rec['Count']) - self.diag_limit
        patient_row = [
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Count']),
            str(exceed_count)
        ]

        for column in range(0, self.ui.tableWidget_patient_diag.columnCount()):
            self.ui.tableWidget_patient_diag.setItem(
                rec_no, column, QtWidgets.QTableWidgetItem(patient_row[column]))
            if column in [0, 2, 3]:
                self.ui.tableWidget_patient_diag.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _patient_treat_changed(self):
        patient_key = self.table_widget_patient_treat.field_value(0)

        sql = '''
            SELECT 
               *
            FROM cases 
            WHERE
                (PatientKey = {0}) AND
                (CaseDate BETWEEN "{1}" AND "{2}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") AND 
                (Treatment IS NOT NULL)
            ORDER BY CaseDate
        '''.format(patient_key, self.start_date, self.end_date)

        self.table_widget_medical_record_treat.set_db_data(
            sql, self._set_medical_record_treat_data)
        self._set_medical_record_treat_color()
        self.ui.tableWidget_medical_record_treat.setCurrentCell(0, 1)
        self.ui.tableWidget_patient_treat.setFocus(True)

    def _set_medical_record_treat_data(self, rec_no, rec):
        medical_record_treat = [
            string_utils.xstr(rec['CaseKey']),
            string_utils.xstr(rec['ApplyType']),
            '{0}-{1:0>2}-{2:0>2}'.format(
                rec['CaseDate'].year, rec['CaseDate'].month, rec['CaseDate'].day
            ),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Share']),
            string_utils.xstr(rec['Card']),
            string_utils.xstr(rec['Continuance']),
            string_utils.xstr(rec['DiseaseCode1']),
            string_utils.xstr(rec['DiseaseName1']),
            string_utils.xstr(rec['Treatment']),
            string_utils.xstr(rec['Doctor']),
            string_utils.xstr(rec['DiagFee']),
            string_utils.xstr(
                number_utils.get_integer(rec['AcupunctureFee']) +
                number_utils.get_integer(rec['MassageFee']) +
                number_utils.get_integer(rec['DislocateFee'])
            ),
        ]

        for column in range(len(medical_record_treat)):
            self.ui.tableWidget_medical_record_treat.setItem(
                rec_no, column, QtWidgets.QTableWidgetItem(medical_record_treat[column]))
            if column in [3, 12, 13]:
                self.ui.tableWidget_medical_record_treat.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [7]:
                self.ui.tableWidget_medical_record_treat.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
    def _patient_diag_changed(self):
        patient_key = self.table_widget_patient_diag.field_value(0)

        sql = '''
            SELECT 
               *
            FROM cases 
            WHERE
                (PatientKey = {0}) AND
                (CaseDate BETWEEN "{1}" AND "{2}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") AND 
                ((Continuance IS NULL) OR (Continuance <= 1))
            ORDER BY CaseDate
        '''.format(patient_key, self.start_date, self.end_date)

        self.table_widget_medical_record_diag.set_db_data(
            sql, self._set_medical_record_diag_data)
        self._set_medical_record_diag_color()
        self.ui.tableWidget_medical_record_diag.setCurrentCell(0, 1)
        self.ui.tableWidget_patient_diag.setFocus(True)

    def _set_medical_record_diag_data(self, rec_no, rec):
        medical_record_diag = [
            string_utils.xstr(rec['CaseKey']),
            string_utils.xstr(rec['ApplyType']),
            '{0}-{1:0>2}-{2:0>2}'.format(
                rec['CaseDate'].year, rec['CaseDate'].month, rec['CaseDate'].day
            ),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Share']),
            string_utils.xstr(rec['Card']),
            string_utils.xstr(rec['Continuance']),
            string_utils.xstr(rec['DiseaseCode1']),
            string_utils.xstr(rec['DiseaseName1']),
            string_utils.xstr(rec['Treatment']),
            string_utils.xstr(rec['Doctor']),
            string_utils.xstr(rec['DiagFee']),
            string_utils.xstr(
                number_utils.get_integer(rec['AcupunctureFee']) +
                number_utils.get_integer(rec['MassageFee']) +
                number_utils.get_integer(rec['DislocateFee'])
            ),
        ]

        for column in range(len(medical_record_diag)):
            self.ui.tableWidget_medical_record_diag.setItem(
                rec_no, column, QtWidgets.QTableWidgetItem(medical_record_diag[column]))
            if column in [3, 12, 13]:
                self.ui.tableWidget_medical_record_diag.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [7]:
                self.ui.tableWidget_medical_record_diag.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _set_medical_record_treat_color(self):
        for row in range(self.treat_limit, self.ui.tableWidget_medical_record_treat.rowCount()):
            self.ui.tableWidget_medical_record_treat.setCurrentCell(row, 1)
            self.table_widget_medical_record_treat.set_row_color(row, QtGui.QColor('red'))
            if self.table_widget_medical_record_treat.field_value(1) == '不申報':
                self.table_widget_medical_record_treat.set_row_color(row, QtGui.QColor('darkGray'))

    def _set_medical_record_diag_color(self):
        for row in range(self.diag_limit, self.ui.tableWidget_medical_record_diag.rowCount()):
            self.ui.tableWidget_medical_record_diag.setCurrentCell(row, 1)
            self.table_widget_medical_record_diag.set_row_color(row, QtGui.QColor('red'))
            if self.table_widget_medical_record_diag.field_value(1) == '不申報':
                self.table_widget_medical_record_diag.set_row_color(row, QtGui.QColor('darkGray'))

    def _set_treat_apply(self):
        table_widget_name = 'tableWidget_medical_record_treat'
        row_no = self.ui.tableWidget_medical_record_treat.currentRow()
        if self.sender().objectName() == 'toolButton_treat_unapply':
            apply_type  = '不申報'
        else:
            apply_type  = '申報'

        case_key = self._get_case_key(table_widget_name)
        self.database.exec_sql(
            'UPDATE cases SET ApplyType = "{0}" WHERE CaseKey = {1}'.format(
                apply_type, case_key))
        self.ui.tableWidget_medical_record_treat.setItem(
            self.ui.tableWidget_medical_record_treat.currentRow(), 1,
            QtWidgets.QTableWidgetItem(apply_type)
        )

        self._set_medical_record_treat_color()
        self.ui.tableWidget_medical_record_treat.setCurrentCell(row_no, 1)

    def _set_diag_apply(self):
        table_widget_name = 'tableWidget_medical_record_diag'
        row_no = self.ui.tableWidget_medical_record_diag.currentRow()
        if self.sender().objectName() == 'toolButton_diag_unapply':
            apply_type  = '不申報'
        else:
            apply_type  = '申報'

        case_key = self._get_case_key(table_widget_name)
        self.database.exec_sql(
            'UPDATE cases SET ApplyType = "{0}" WHERE CaseKey = {1}'.format(
                apply_type, case_key))
        self.ui.tableWidget_medical_record_diag.setItem(
            self.ui.tableWidget_medical_record_diag.currentRow(), 1,
            QtWidgets.QTableWidgetItem(apply_type)
        )

        self._set_medical_record_diag_color()
        self.ui.tableWidget_medical_record_diag.setCurrentCell(row_no, 1)
