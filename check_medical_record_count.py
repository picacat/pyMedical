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
from libs import system_utils
from libs import nhi_utils
from libs import case_utils


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
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self._set_table_widget()
        self.ui.label_treat_limit.setText(
            '針傷次數限制: {0}次'.format(self.treat_limit)
        )
        self.ui.label_diag_limit.setText(
            '首次次數限制: {0}次'.format(self.diag_limit)
        )
        start_date = date_utils.str_to_date(self.start_date)
        last_month = (start_date - datetime.timedelta(days=1)).replace(day=1)  # 上個月1日
        self.ui.dateEdit_start_date.setDate(last_month)
        self.ui.dateEdit_end_date.setDate(date_utils.str_to_date(self.end_date))

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

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
        self.ui.dateEdit_start_date.dateChanged.connect(self._read_medical_record_treat_by_patient)
        self.ui.dateEdit_end_date.dateChanged.connect(self._read_medical_record_treat_by_patient)

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
        progress_dialog = QtWidgets.QProgressDialog(
            '正在執行門診次數檢查中, 請稍後...', '取消', 0, 2, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        self._check_medical_record_treat()
        progress_dialog.setValue(1)
        self._check_medical_record_diag()
        progress_dialog.setValue(2)

    def error_count(self):
        return (self.ui.tableWidget_patient_treat.rowCount() +
                self.ui.tableWidget_patient_diag.rowCount())

    def _check_medical_record_treat(self):
        self._read_medical_record_treat(self.start_date, self.end_date, self.treat_limit)

    def _read_medical_record_treat(self, start_date, end_date, treat_limit):
        apply_type_sql = nhi_utils.get_apply_type_sql(self.apply_type)

        sql = '''
            SELECT 
               PatientKey, Name, Count(PatientKey) AS Count 
            FROM cases 
            WHERE
                (CaseDate BETWEEN "{start_date}" AND "{end_date}") AND
                (cases.InsType = "健保") AND
                (cases.Card IS NOT NULL) AND (LENGTH(cases.Card) > 0) AND (cases.Card != "欠卡") AND
                (Treatment IS NOT NULL) AND
                ({apply_type_sql})
            GROUP BY PatientKey
            HAVING COUNT(PatientKey) > {treat_limit}
        '''.format(
            start_date=start_date,
            end_date=end_date,
            apply_type_sql=apply_type_sql,
            treat_limit=treat_limit,
        )

        self.table_widget_patient_treat.set_db_data(sql, self._set_patient_treat_data)

    def _set_patient_treat_data(self, row_no, row):
        exceed_count = number_utils.get_integer(row['Count']) - self.treat_limit
        patient_row = [
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Count']),
            str(exceed_count)
        ]

        for column in range(len(patient_row)):
            self.ui.tableWidget_patient_treat.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(patient_row[column])
            )
            if column in [0, 2, 3]:
                self.ui.tableWidget_patient_treat.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _check_medical_record_diag(self):
        apply_type_sql = nhi_utils.get_apply_type_sql(self.apply_type)

        sql = '''
            SELECT 
               PatientKey, Name, Count(PatientKey) AS Count 
            FROM cases 
            WHERE
                (CaseDate BETWEEN "{start_date}" AND "{end_date}") AND
                (cases.InsType = "健保") AND
                (cases.Card IS NOT NULL) AND (LENGTH(cases.Card) > 0) AND (cases.Card != "欠卡") AND 
                ((Continuance IS NULL) OR (Continuance <= 1)) AND
                ({apply_type_sql})
            GROUP BY PatientKey
            HAVING COUNT(PatientKey) > {diag_limit}
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            apply_type_sql=apply_type_sql,
            diag_limit=self.diag_limit,
        )

        self.table_widget_patient_diag.set_db_data(sql, self._set_patient_diag_data)

    def _set_patient_diag_data(self, rec_no, rec):
        exceed_count = number_utils.get_integer(rec['Count']) - self.diag_limit
        patient_row = [
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Count']),
            str(exceed_count)
        ]

        for column in range(len(patient_row)):
            self.ui.tableWidget_patient_diag.setItem(
                rec_no, column, QtWidgets.
                    QTableWidgetItem(patient_row[column])
            )
            if column in [0, 2, 3]:
                self.ui.tableWidget_patient_diag.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _patient_treat_changed(self):
        self._read_medical_record_treat_by_patient()

    def _read_medical_record_treat_by_patient(self):
        patient_key = self.table_widget_patient_treat.field_value(0)
        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')

        sql = '''
            SELECT * FROM cases 
            WHERE
                (PatientKey = {0}) AND
                (CaseDate BETWEEN "{1}" AND "{2}") AND
                (cases.InsType = "健保") AND
                (cases.Card IS NOT NULL) AND (LENGTH(cases.Card) > 0) AND (cases.Card != "欠卡") AND 
                (Treatment IS NOT NULL) AND (LENGTH(Treatment) > 0)
            ORDER BY CaseDate
        '''.format(patient_key, start_date, end_date)

        self.table_widget_medical_record_treat.set_db_data(
            sql, self._set_medical_record_treat_data)

        self._set_medical_record_treat_color()
        self.ui.tableWidget_medical_record_treat.setCurrentCell(0, 1)
        self.ui.tableWidget_patient_treat.setFocus(True)

    def _set_medical_record_treat_data(self, row_no, row):
        case_key = row['CaseKey']

        medical_record_treat = [
            string_utils.xstr(case_key),
            string_utils.xstr(row['ApplyType']),
            '{0}-{1:0>2}-{2:0>2}'.format(
                row['CaseDate'].year, row['CaseDate'].month, row['CaseDate'].day
            ),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Continuance']),
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['Treatment']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['DiagFee']),
            string_utils.xstr(
                number_utils.get_integer(row['AcupunctureFee']) +
                number_utils.get_integer(row['MassageFee']) +
                number_utils.get_integer(row['DislocateFee'])
            ),
        ]

        for column in range(len(medical_record_treat)):
            self.ui.tableWidget_medical_record_treat.setItem(
                row_no, column, QtWidgets.QTableWidgetItem(medical_record_treat[column]))
            if column in [3, 12, 13]:
                self.ui.tableWidget_medical_record_treat.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [7]:
                self.ui.tableWidget_medical_record_treat.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _patient_diag_changed(self):
        patient_key = self.table_widget_patient_diag.field_value(0)

        sql = '''
            SELECT * FROM cases 
            WHERE
                (PatientKey = {0}) AND
                (CaseDate BETWEEN "{1}" AND "{2}") AND
                (cases.InsType = "健保") AND
                (cases.Card IS NOT NULL) AND (LENGTH(cases.Card) > 0) AND (cases.Card != "欠卡") AND
                ((Continuance IS NULL) OR (Continuance <= 1))
            ORDER BY CaseDate
        '''.format(patient_key, self.start_date, self.end_date)

        self.table_widget_medical_record_diag.set_db_data(
            sql, self._set_medical_record_diag_data)
        self._set_medical_record_diag_color()
        self.ui.tableWidget_medical_record_diag.setCurrentCell(0, 1)
        self.ui.tableWidget_patient_diag.setFocus(True)

    def _set_medical_record_diag_data(self, row_no, row):
        case_key = row['CaseKey']
        pres_days = case_utils.get_pres_days(self.database, case_key)
        if pres_days <= 0:
            pres_days = ''

        medical_record_diag = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['ApplyType']),
            '{0}-{1:0>2}-{2:0>2}'.format(
                row['CaseDate'].year, row['CaseDate'].month, row['CaseDate'].day
            ),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Continuance']),
            string_utils.xstr(pres_days),
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['Treatment']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['DiagFee']),
            string_utils.xstr(
                number_utils.get_integer(row['AcupunctureFee']) +
                number_utils.get_integer(row['MassageFee']) +
                number_utils.get_integer(row['DislocateFee'])
            ),
        ]

        for column in range(len(medical_record_diag)):
            self.ui.tableWidget_medical_record_diag.setItem(
                row_no, column, QtWidgets.QTableWidgetItem(medical_record_diag[column]))
            if column in [3, 8, 13, 14]:
                self.ui.tableWidget_medical_record_diag.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [7]:
                self.ui.tableWidget_medical_record_diag.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _set_medical_record_treat_color(self):
        record_count = 0
        for row_no in range(self.ui.tableWidget_medical_record_treat.rowCount()):
            case_date = self.ui.tableWidget_medical_record_treat.item(row_no, 2).text()
            if (datetime.datetime.strptime(case_date, '%Y-%m-%d') <
                    datetime.datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S')):
                self.table_widget_medical_record_treat.set_row_color(row_no, QtGui.QColor('darkGray'))
            else:
                record_count += 1

            if record_count > self.treat_limit:
                self.table_widget_medical_record_treat.set_row_color(row_no, QtGui.QColor('red'))
            apply_type = self.ui.tableWidget_medical_record_treat.item(row_no, 1).text()
            if apply_type == '不申報':
                self.table_widget_medical_record_treat.set_row_color(row_no, QtGui.QColor('darkGray'))

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
