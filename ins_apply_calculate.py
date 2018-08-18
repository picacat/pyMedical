#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import datetime

from libs import ui_utils
from libs import date_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import case_utils
from libs import personnel_utils


# 候診名單 2018.01.31
class InsApplyCalculate(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsApplyCalculate, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = args[2]
        self.apply_month = args[3]
        self.start_date = args[4]
        self.end_date = args[5]
        self.period = args[6]
        self.apply_type = args[7]
        self.clinic_id = args[8]
        self.ins_calculated_table = []

        self.ui = None
        self.apply_date = '{0:0>3}{1:0>2}'.format(self.apply_year-1911, self.apply_month)
        if self.apply_type == '申報':
            self.apply_type = '1'
        else:
            self.apply_type = '2'

        self.start_date = self.start_date.toString("yyyy-MM-dd 00:00:00")
        self.end_date = self.end_date.toString("yyyy-MM-dd 23:59:59")
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
        pass

    # 設定信號
    def _set_signal(self):
        pass

    def calculate_ins_data(self):
        self._set_doctor_table()

    def _set_doctor_table(self):
        sql = '''
            SELECT DoctorName, DoctorID
            FROM insapply 
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}" AND
                CaseDate BETWEEN "{4}" AND "{5}"
            GROUP BY DoctorID
        '''.format(
            self.apply_date, self.apply_type, self.period, self.clinic_id,
            self.start_date, self.end_date
        )
        rows = self.database.select_record(sql)

        for row in rows:
            self._init_doctor_data(row)
            self._calculate_diag_section()

        print(self.ins_calculated_table)

    def _init_doctor_data(self, row):
        doctor_data = {
            'doctor_type': None,
            'doctor_name': None,
            'doctor_id': None,
            'diag_days': 0,
            'total_count': 0,
            'treat_drug': 0,
            'diag_count': 0,
            'diag_section1': 0,
            'diag_section2': 0,
            'diag_section3': 0,
            'diag_section4': 0,
            'diag_section5': 0,
        }
        doctor_data['doctor_name'] = row['DoctorName']
        doctor_data['doctor_id'] = row['DoctorID']
        doctor_data['doctor_type'] = personnel_utils.get_personnel_position(
            self.database, doctor_data['doctor_name']
        )
        doctor_data['diag_days'] = self._get_diag_days(
            doctor_data['doctor_id']
        )
        doctor_data['total_count'] = self._get_total_count(
            doctor_data['doctor_name']
        )
        doctor_data['treat_drug'] = self._get_treat_drug(
            doctor_data['doctor_name']
        )
        doctor_data['diag_count'] = self._get_diag_count(
            doctor_data['doctor_id']
        )

        self.ins_calculated_table.append(doctor_data)

    def _get_diag_days(self, doctor_id):
        sql = '''
            SELECT InsApplyKey
            FROM insapply 
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}" AND
                CaseDate BETWEEN "{4}" AND "{5}" AND
                DoctorID = "{6}"
            GROUP BY DATE(CaseDate)
        '''.format(
            self.apply_date, self.apply_type, self.period, self.clinic_id,
            self.start_date, self.end_date, doctor_id,
        )
        rows = self.database.select_record(sql)
        diag_days = len(rows)

        if diag_days > nhi_utils.MAX_DIAG_DAYS:
            diag_days = nhi_utils.MAX_DIAG_DAYS

        return diag_days

    def _get_total_count(self, doctor_name):
        total_count = 0
        sql = '''
            SELECT CaseKey1, CaseKey2, CaseKey3, CaseKey4, CaseKey5, CaseKey6
            FROM insapply 
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}"
        '''.format(
            self.apply_date, self.apply_type, self.period, self.clinic_id,
        )
        rows = self.database.select_record(sql)
        for row in rows:
            for i in range(1, 7):
                case_key = number_utils.get_integer(row['CaseKey{0}'.format(i)])
                if case_key <= 0:
                    continue

                sql = '''
                    SELECT Doctor FROM cases 
                    WHERE
                        CaseKey = {0}
                '''.format(case_key)
                doctor_rows = self.database.select_record(sql)
                if len(doctor_rows) <= 0:
                    continue

                if string_utils.xstr(doctor_rows[0]['Doctor']) == doctor_name:
                    total_count += 1

        return total_count

    def _get_treat_drug(self, doctor_name):
        treat_drug = 0
        sql = '''
            SELECT 
                CaseKey1, CaseKey2, CaseKey3, CaseKey4, CaseKey5, CaseKey6,
                TreatCode1, TreatCode2, TreatCode3, TreatCode4, TreatCode5, TreatCode6
            FROM insapply 
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}" AND
                CaseType NOT IN ("21", "24")
        '''.format(
            self.apply_date, self.apply_type, self.period, self.clinic_id,
        )
        rows = self.database.select_record(sql)
        for row in rows:
            for i in range(1, 7):
                treat_code = string_utils.xstr(row['TreatCode{0}'.format(i)])
                if treat_code not in nhi_utils.TREAT_DRUG_CODE:
                    continue

                case_key = number_utils.get_integer(row['CaseKey{0}'.format(i)])
                if case_key <= 0:
                    continue

                sql = '''
                    SELECT Doctor FROM cases 
                    WHERE
                        CaseKey = {0}
                '''.format(case_key)
                doctor_rows = self.database.select_record(sql)
                if len(doctor_rows) <= 0:
                    continue

                if string_utils.xstr(doctor_rows[0]['Doctor']) == doctor_name:
                    treat_drug += 1

        return treat_drug

    def _get_diag_count(self, doctor_id):
        sql = '''
            SELECT CaseKey1, CaseKey2, CaseKey3, CaseKey4, CaseKey5, CaseKey6
            FROM insapply 
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}" AND
                DoctorID = "{4}" AND
                DiagFee > 0
        '''.format(
            self.apply_date, self.apply_type, self.period, self.clinic_id,
            doctor_id,
        )
        rows = self.database.select_record(sql)
        diag_count = len(rows)

        return diag_count

    def _calculate_diag_section(self):
        for row in self.ins_calculated_table:
            row['diag_section1'] = self._get_diag_section1(
                row['diag_days'],
                row['diag_count'],
            )
            row['diag_section2'] = self._get_diag_section2(
                row['diag_days'],
                row['diag_count'],
                row['diag_section1'],
            )
            row['diag_section3'] = self._get_diag_section3(
                row['diag_days'],
                row['diag_count'],
                row['diag_section1'],
                row['diag_section2'],
            )
            row['diag_section4'] = self._get_diag_section4(
                row['diag_days'],
                row['diag_count'],
                row['diag_section1'],
                row['diag_section2'],
                row['diag_section3'],
            )
            row['diag_section5'] = self._get_diag_section5(
                row['diag_count'],
                row['diag_section1'],
                row['diag_section2'],
                row['diag_section3'],
                row['diag_section4'],
            )

    def _get_diag_section1(self, diag_days, diag_count):
        diag_section1 = diag_count
        diag_section1_limit = diag_days * nhi_utils.DIAG_SECTION1

        if diag_section1 > diag_section1_limit:
            diag_section1 = diag_section1_limit

        return diag_section1

    def _get_diag_section2(self, diag_days, diag_count, diag_section1):
        diag_section2 = diag_count - diag_section1
        diag_section2_limit = diag_days * (nhi_utils.DIAG_SECTION2 - nhi_utils.DIAG_SECTION1)

        if diag_section2 > diag_section2_limit:
            diag_section2 = diag_section2_limit

        return diag_section2

    def _get_diag_section3(self, diag_days, diag_count, diag_section1, diag_section2):
        diag_section3 = diag_count - diag_section1 - diag_section2
        diag_section3_limit = diag_days * (nhi_utils.DIAG_SECTION3 - nhi_utils.DIAG_SECTION2)

        if diag_section3 > diag_section3_limit:
            diag_section3 = diag_section3_limit

        return diag_section3

    def _get_diag_section4(self, diag_days, diag_count, diag_section1, diag_section2, diag_section3):
        diag_section4 = diag_count - diag_section1 - diag_section2 - diag_section3
        diag_section4_limit = diag_days * (nhi_utils.DIAG_SECTION4 - nhi_utils.DIAG_SECTION3)

        if diag_section4 > diag_section4_limit:
            diag_section4 = diag_section4_limit

        return diag_section4

    def _get_diag_section5(self, diag_count, diag_section1, diag_section2,
                           diag_section3, diag_section4):
        diag_section5 = diag_count - diag_section1 - diag_section2 - diag_section3 - diag_section4

        return diag_section5
