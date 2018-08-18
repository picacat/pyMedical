#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime

from classes import table_widget
from libs import ui_utils
from libs import date_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from dialog import dialog_ins_apply


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
        pass

    def open_medical_record(self):
        case_key = 0
        self.parent.open_medical_record(case_key, '健保申報')

    def read_data(self):
        apply_date = '{0:0>3}{1:0>2}'.format(self.apply_year-1911, self.apply_month)
        if self.apply_type == '申報':
            apply_type = '1'
        else:
            apply_type = '2'

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
        '''.format(apply_date, apply_type, self.period, self.clinic_id, self.case_type)

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

