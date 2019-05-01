#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QInputDialog

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import printer_utils
from libs import date_utils

from dialog import dialog_course_list


# 候診名單 2018.01.31
class InsApplyList(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsApplyList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = args[2]
        self.apply_month = args[3]
        self.period = args[4]
        self.apply_type = args[5]
        self.clinic_id = args[6]
        self.case_type = args[7]
        self.ui = None
        self.error_count = 0

        self.apply_date = nhi_utils.get_apply_date(self.apply_year, self.apply_month)
        self.apply_type_code = nhi_utils.APPLY_TYPE_CODE[self.apply_type]

        self._set_ui()
        self._set_signal()
        self.read_data()

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_APPLY_LIST, self)
        self.table_widget_ins_apply_list = table_widget.TableWidget(
            self.ui.tableWidget_ins_apply_list, self.database)
        self.table_widget_ins_apply_list.set_column_hidden([0])

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_ins_apply_list.doubleClicked.connect(self.open_medical_record)
        self.ui.toolButton_jump.clicked.connect(self._jump_sequence)
        self.ui.toolButton_find_error.clicked.connect(self._find_error)
        self.ui.toolButton_bookmark.clicked.connect(self._set_bookmark)
        self.ui.toolButton_open_medical_record.clicked.connect(self.open_medical_record)
        self.ui.toolButton_print_order.clicked.connect(self._print_order)
        self.ui.toolButton_print_medical_records.clicked.connect(self._print_medical_records)
        self.ui.toolButton_print_medical_chart.clicked.connect(self._print_medical_chart)

    def open_medical_record(self):
        ins_apply_key = self.table_widget_ins_apply_list.field_value(0)
        sql = '''
            SELECT CaseKey1, CaseKey2, CaseKey3, CaseKey4, CaseKey5, CaseKey6, 
                CaseType, Sequence, SpecialCode1, Name
            FROM insapply
            WHERE
                InsApplyKey = {0}
        '''.format(ins_apply_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        if string_utils.xstr(row['CaseType']) == '30':
            case_key = row['CaseKey1']
            self.parent.open_medical_record(case_key)
            return

        case_key_list = [
            row['CaseKey1'],
            row['CaseKey2'], row['CaseKey3'], row['CaseKey4'], row['CaseKey5'], row['CaseKey6'],
        ]

        available_case_key_list = []
        for case_key in case_key_list:
            if case_key != 0:
                available_case_key_list.append(case_key)

        if len(available_case_key_list) >= 2:
            case_key = self._open_medical_record_dialog(row, available_case_key_list)
        else:
            case_key = available_case_key_list[0]

        if case_key != 0:
            self.parent.open_medical_record(case_key)

    # 開啟病歷選擇視窗
    def _open_medical_record_dialog(self, row, case_key_list):
        dialog = dialog_course_list.DialogCourseList(
            self, self.database, self.system_settings,
            case_key_list
        )
        dialog.ui.label_header.setText(
            '案件分類:{0}-{1:0>4} {2}的療程病歷明細'.format(
                string_utils.xstr(row['CaseType']),
                string_utils.xstr(row['Sequence']),
                string_utils.xstr(row['Name']),
            )
        )

        dialog.exec_()
        case_key = dialog.selected_case_key
        dialog.close_all()
        dialog.deleteLater()

        return case_key

    def read_data(self):

        sql = '''
            SELECT *
            FROM insapply 
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}" AND
                CaseType = "{4}"
            ORDER BY Sequence
        '''.format(self.apply_date, self.apply_type_code, self.period, self.clinic_id, self.case_type)

        self.table_widget_ins_apply_list.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        ins_apply_row = [
            string_utils.xstr(row['InsApplyKey']),
            string_utils.xstr(row['Note']),
            string_utils.xstr(row['ClinicID']),
            string_utils.xstr(row['ApplyDate']),
            string_utils.xstr(row['ApplyPeriod']),
            string_utils.xstr(row['ApplyType']),
            string_utils.xstr(row['CaseType']),
            string_utils.xstr(row['Sequence']),
            string_utils.xstr(row['SpecialCode1']),
            string_utils.xstr(row['SpecialCode2']),
            string_utils.xstr(row['SpecialCode3']),
            string_utils.xstr(row['SpecialCode4']),
            string_utils.xstr(row['Class']),
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['StopDate']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['ID']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Injury']),
            string_utils.xstr(row['ShareCode']),
            string_utils.xstr(row['Visit']),
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseCode2']),
            string_utils.xstr(row['DiseaseCode3']),
            string_utils.xstr(row['PresDays']),
            string_utils.xstr(row['PresType']),
            string_utils.xstr(row['DoctorName']),
            string_utils.xstr(row['DoctorID']),
            string_utils.xstr(row['PharmacistID']),
            string_utils.xstr(row['DrugFee']),
            string_utils.xstr(row['TreatFee']),
            string_utils.xstr(row['DiagCode']),
            string_utils.xstr(row['DiagFee']),
            string_utils.xstr(row['PharmacyCode']),
            string_utils.xstr(row['PharmacyFee']),
            string_utils.xstr(row['InsTotalFee']),
            string_utils.xstr(row['ShareFee']),
            string_utils.xstr(row['InsApplyFee']),
            string_utils.xstr(row['AgentFee']),
            string_utils.xstr(row['Message']),
        ]

        for column in range(0, len(ins_apply_row)):
            self.ui.tableWidget_ins_apply_list.setItem(
                row_no, column, QtWidgets.QTableWidgetItem(ins_apply_row[column]))
            if column in [1]:
                self.ui.tableWidget_ins_apply_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            if row['Note'] is not None:
                self.ui.tableWidget_ins_apply_list.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
                )

        if string_utils.xstr(row['Message']) != '':
            self.error_count += 1
            self._set_row_color(row_no, 'red')

    def _set_row_color(self, row_no, color):
        for column_no in range(self.ui.tableWidget_ins_apply_list.columnCount()):
            self.ui.tableWidget_ins_apply_list.item(row_no, column_no).setForeground(QtGui.QColor(color))

    # 註記
    def _set_bookmark(self):
        if self.table_widget_ins_apply_list.field_value(1) == '*':
            bookmark = None
            color = 'black'
        else:
            bookmark = '*'
            color = 'blue'

        row_no = self.ui.tableWidget_ins_apply_list.currentRow()
        self.ui.tableWidget_ins_apply_list.setItem(
            row_no, 1,
            QtWidgets.QTableWidgetItem(bookmark)
        )
        self.ui.tableWidget_ins_apply_list.item(
            row_no, 1).setTextAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
        )

        for col_no in range(self.ui.tableWidget_ins_apply_list.columnCount()):
            self.ui.tableWidget_ins_apply_list.item(
                row_no, col_no).setForeground(
                QtGui.QColor(color)
            )

        ins_apply_key = self.table_widget_ins_apply_list.field_value(0)
        if bookmark is None:
            bookmark_str = 'NULL'
        else:
            bookmark_str = '"{0}"'.format(bookmark)

        sql = '''
            UPDATE insapply SET Note = {0} WHERE InsApplyKey = {1}
        '''.format(bookmark_str, ins_apply_key)
        self.database.exec_sql(sql)

    # 列印醫令明細
    def _print_order(self):
        ins_apply_key = self.table_widget_ins_apply_list.field_value(0)

        printer_utils.print_ins_apply_order(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.apply_type, ins_apply_key
        )

    # 列印病歷
    def _print_medical_records(self):
        patient_key = self.table_widget_ins_apply_list.field_value(15)

        start_date, end_date = date_utils.get_two_month_date(
            self.database, patient_key,
            self.apply_year, self.apply_month,
        )

        printer_utils.print_medical_records(
            self, self.database, self.system_settings,
            patient_key, None, start_date, end_date,
        )

    # 列印病歷首頁
    def _print_medical_chart(self):
        patient_key = self.table_widget_ins_apply_list.field_value(15)

        printer_utils.print_medical_chart(
            self, self.database, self.system_settings,
            patient_key, self.apply_date,
        )

    # 查詢流水號
    def _jump_sequence(self):
        input_dialog = QInputDialog()
        input_dialog.setOkButtonText('確定')
        input_dialog.setCancelButtonText('取消')

        start_no = 1
        end_no = self.ui.tableWidget_ins_apply_list.rowCount()

        sequence, ok = input_dialog.getInt(
            self, '流水號查詢', '請輸入流水號', start_no, 0, end_no, 1)
        if not ok:
            return

        self.ui.tableWidget_ins_apply_list.setCurrentCell(sequence-1, 1)
        self.ui.tableWidget_ins_apply_list.setFocus(True)

    def _find_error(self):
        self.table_widget_ins_apply_list.find_error(41)

