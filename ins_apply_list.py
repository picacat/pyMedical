#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
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
        self.ui.toolButton_open_medical_record.clicked.connect(self.open_medical_record)

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
        if string_utils.xstr(row['SpecialCode1']) == nhi_utils.SPECIAL_CODE_DICT['腦血管疾病']:
            case_key = row['CaseKey1']
            print(case_key)
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

    def _set_table_data(self, rec_no, rec):
        ins_apply_row = [
            string_utils.xstr(rec['InsApplyKey']),
            string_utils.xstr(rec['ClinicID']),
            string_utils.xstr(rec['ApplyDate']),
            string_utils.xstr(rec['ApplyPeriod']),
            string_utils.xstr(rec['ApplyType']),
            string_utils.xstr(rec['CaseType']),
            string_utils.xstr(rec['Sequence']),
            string_utils.xstr(rec['SpecialCode1']),
            string_utils.xstr(rec['SpecialCode2']),
            string_utils.xstr(rec['SpecialCode3']),
            string_utils.xstr(rec['SpecialCode4']),
            string_utils.xstr(rec['Class']),
            string_utils.xstr(rec['CaseDate']),
            string_utils.xstr(rec['StopDate']),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Birthday']),
            string_utils.xstr(rec['ID']),
            string_utils.xstr(rec['Card']),
            string_utils.xstr(rec['Injury']),
            string_utils.xstr(rec['ShareCode']),
            string_utils.xstr(rec['Visit']),
            string_utils.xstr(rec['DiseaseCode1']),
            string_utils.xstr(rec['DiseaseCode2']),
            string_utils.xstr(rec['DiseaseCode3']),
            string_utils.xstr(rec['PresDays']),
            string_utils.xstr(rec['PresType']),
            string_utils.xstr(rec['DoctorName']),
            string_utils.xstr(rec['DoctorID']),
            string_utils.xstr(rec['PharmacistID']),
            string_utils.xstr(rec['DrugFee']),
            string_utils.xstr(rec['TreatFee']),
            string_utils.xstr(rec['DiagCode']),
            string_utils.xstr(rec['DiagFee']),
            string_utils.xstr(rec['PharmacyCode']),
            string_utils.xstr(rec['PharmacyFee']),
            string_utils.xstr(rec['InsTotalFee']),
            string_utils.xstr(rec['ShareFee']),
            string_utils.xstr(rec['InsApplyFee']),
            string_utils.xstr(rec['AgentFee']),
            string_utils.xstr(rec['Message']),
        ]

        for column in range(0, len(ins_apply_row)):
            self.ui.tableWidget_ins_apply_list.setItem(
                rec_no, column, QtWidgets.QTableWidgetItem(ins_apply_row[column]))

