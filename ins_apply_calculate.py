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

        self.apply_date = nhi_utils.get_apply_date(self.apply_year, self.apply_month)
        self.apply_type_code = nhi_utils.APPLY_TYPE_CODE[self.apply_type]
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
        self._set_part_time_doctor()

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
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
            self.start_date, self.end_date
        )
        rows = self.database.select_record(sql)

        for row in rows:
            self._init_doctor_data(row)
            position = personnel_utils.get_personnel_position(self.database, row['DoctorName'])
            if position == '醫師':
                self._calculate_diag_section()
                self._calculate_treat_section()

    def _init_doctor_data(self, row):
        doctor_data = {
            'doctor_type': None,
            'doctor_name': None,
            'doctor_id': None,
            'diag_days': 0,
            'total_count': 0,
            'diag_count': 0,
            'treat_count': 0,
            'treat_drug': 0,
            'complicated_massage': 0,
            'diag_section1': 0,
            'diag_section2': 0,
            'diag_section3': 0,
            'diag_section4': 0,
            'diag_section5': 0,
            'treat_section1': 0,
            'treat_section2': 0,
            'treat_section3': 0,
        }
        doctor_data['doctor_name'] = row['DoctorName']
        doctor_data['doctor_id'] = row['DoctorID']
        doctor_data['doctor_type'] = personnel_utils.get_personnel_position(
            self.database, doctor_data['doctor_name']
        )

        max_progress = 6

        progress_dialog = QtWidgets.QProgressDialog(
            '正在統計{0}醫師的資料中, 請稍後...'.format(
                doctor_data['doctor_name']
            ), '取消', 0, max_progress, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        doctor_data['diag_days'] = self._get_diag_days(
            doctor_data['doctor_id']
        )
        progress_dialog.setValue(1)

        doctor_data['total_count'] = self._get_total_count(
            doctor_data['doctor_name']
        )
        progress_dialog.setValue(2)

        doctor_data['diag_count'] = self._get_diag_count(
            doctor_data['doctor_id']
        )
        progress_dialog.setValue(3)

        doctor_data['treat_count'] = self._get_treat_count(
            doctor_data['doctor_name']
        )
        progress_dialog.setValue(4)

        doctor_data['treat_drug'] = self._get_treat_drug(
            doctor_data['doctor_name']
        )
        progress_dialog.setValue(5)

        doctor_data['complicated_massage'] = self._get_complicated_massage(
            doctor_data['doctor_name']
        )
        progress_dialog.setValue(6)

        self.ins_calculated_table.append(doctor_data)

    # 取得醫師總看診日數
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
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
            self.start_date, self.end_date, doctor_id,
        )
        rows = self.database.select_record(sql)
        diag_days = len(rows)

        if diag_days > nhi_utils.MAX_DIAG_DAYS:
            diag_days = nhi_utils.MAX_DIAG_DAYS

        return diag_days

    # 取得醫師總看診人次
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
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
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

    # 取得醫師針傷總人次
    def _get_treat_count(self, doctor_name):
        treat_count = 0
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
                CaseType IN ("29")
        '''.format(
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
        )
        rows = self.database.select_record(sql)
        for row in rows:
            for i in range(1, 7):
                treat_code = string_utils.xstr(row['TreatCode{0}'.format(i)])
                if treat_code not in nhi_utils.TREAT_ALL_CODE:
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
                    treat_count += 1

        return treat_count

    # 取得醫師針傷給藥總人次
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
                CaseType IN ("29")
        '''.format(
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
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

    # 取得醫師複雜性傷科總人次
    def _get_complicated_massage(self, doctor_name):
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
                CaseType IN ("29")
        '''.format(
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
        )
        rows = self.database.select_record(sql)
        for row in rows:
            for i in range(1, 7):
                treat_code = string_utils.xstr(row['TreatCode{0}'.format(i)])
                if treat_code not in nhi_utils.COMPLICATED_TREAT_CODE:
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

    # 計算診察費人次, 特定照護-30不列入計算
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
                DiagFee > 0 AND
                CaseType NOT IN {5}
        '''.format(
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
            doctor_id, tuple(nhi_utils.EXCLUDE_DIAG_ADJUST)
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

    def _calculate_treat_section(self):
        for row in self.ins_calculated_table:
            row['treat_section1'] = self._get_treat_section1(
                row['diag_days'],
                row['treat_count'],
            )
            row['treat_section2'] = self._get_treat_section2(
                row['diag_days'],
                row['treat_count'],
                row['treat_section1'],
            )
            row['treat_section3'] = self._get_treat_section3(
                row['treat_count'],
                row['treat_section1'],
                row['treat_section2'],
            )

    def _get_treat_section1(self, diag_days, treat_count):
        treat_section1 = treat_count
        treat_section1_limit = diag_days * nhi_utils.TREAT_SECTION1

        if treat_section1 > treat_section1_limit:
            treat_section1 = treat_section1_limit

        return treat_section1

    def _get_treat_section2(self, diag_days, treat_count, treat_section1):
        treat_section2 = treat_count - treat_section1
        treat_section2_limit = diag_days * (nhi_utils.TREAT_SECTION2 - nhi_utils.TREAT_SECTION1)

        if treat_section2 > treat_section2_limit:
            treat_section2 = treat_section2_limit

        return treat_section2

    def _get_treat_section3(self, treat_count, treat_section1, treat_section2):
        treat_section3 = treat_count - treat_section1 - treat_section2

        return treat_section3

    def _set_part_time_doctor(self):
        self._set_part_time_doctor_diag_balance()
        self._set_part_time_doctor_treat_balance()

    # 支援醫師診察人次分配
    def _set_part_time_doctor_diag_balance(self):
        (section1_balance,
         section2_balance,
         section3_balance,
         section4_balance) = self._get_full_time_doctor_diag_balance()

        for ins_calculated_row in self.ins_calculated_table:
            if ins_calculated_row['doctor_type'] == '醫師':  # 只計算支援醫師
                continue

            diag_count = ins_calculated_row['diag_count']
            if diag_count < section1_balance:
                ins_calculated_row['diag_section1'] = diag_count
                diag_count = 0
            else:
                ins_calculated_row['diag_section1'] = section1_balance
                diag_count -= section1_balance

            section1_balance -= ins_calculated_row['diag_section1']

            if diag_count <= 0:
                continue

            if diag_count < section2_balance:
                ins_calculated_row['diag_section2'] = diag_count
                diag_count = 0
            else:
                ins_calculated_row['diag_section2'] = section2_balance
                diag_count -= section2_balance

            section2_balance -= ins_calculated_row['diag_section2']

            if diag_count <= 0:
                continue

            if diag_count < section3_balance:
                ins_calculated_row['diag_section3'] = diag_count
                diag_count = 0
            else:
                ins_calculated_row['diag_section3'] = section3_balance
                diag_count -= section3_balance

            section3_balance -= ins_calculated_row['diag_section3']

            if diag_count <= 0:
                continue

            if diag_count < section4_balance:
                ins_calculated_row['diag_section4'] = diag_count
                diag_count = 0
            else:
                ins_calculated_row['diag_section4'] = section4_balance
                diag_count -= section4_balance

            section4_balance -= ins_calculated_row['diag_section4']

            if diag_count <= 0:
                continue

            ins_calculated_row['diag_section5'] = diag_count

    def _get_full_time_doctor_diag_balance(self):
        section1_balance = 0
        section2_balance = 0
        section3_balance = 0
        section4_balance = 0

        for ins_calculated_row in self.ins_calculated_table:
            if ins_calculated_row['doctor_type'] == '支援醫師':  # 只計算專任醫師的各段限量
                continue

            diag_days = ins_calculated_row['diag_days']
            diag_section1_limit = diag_days * nhi_utils.DIAG_SECTION1
            diag_section2_limit = diag_days * (nhi_utils.DIAG_SECTION2 - nhi_utils.DIAG_SECTION1)
            diag_section3_limit = diag_days * (nhi_utils.DIAG_SECTION3 - nhi_utils.DIAG_SECTION2)
            diag_section4_limit = diag_days * (nhi_utils.DIAG_SECTION4 - nhi_utils.DIAG_SECTION3)

            if ins_calculated_row['diag_section1'] < diag_section1_limit:
                section1_balance += diag_section1_limit - ins_calculated_row['diag_section1']
            if ins_calculated_row['diag_section2'] < diag_section2_limit:
                section2_balance += diag_section2_limit - ins_calculated_row['diag_section2']
            if ins_calculated_row['diag_section3'] < diag_section3_limit:
                section3_balance += diag_section3_limit - ins_calculated_row['diag_section3']
            if ins_calculated_row['diag_section4'] < diag_section4_limit:
                section4_balance += diag_section4_limit - ins_calculated_row['diag_section4']

        return section1_balance, section2_balance, section3_balance, section4_balance

    def _set_part_time_doctor_treat_balance(self):
        (section1_balance,
         section2_balance) = self._get_full_time_doctor_treat_balance()

        for ins_calculated_row in self.ins_calculated_table:
            if ins_calculated_row['doctor_type'] == '醫師':
                continue

            treat_count = ins_calculated_row['treat_count']
            if treat_count < section1_balance:
                ins_calculated_row['treat_section1'] = treat_count
                treat_count = 0
            else:
                ins_calculated_row['treat_section1'] = section1_balance
                treat_count -= section1_balance

            section1_balance -= ins_calculated_row['treat_section1']

            if treat_count <= 0:
                continue

            if treat_count < section2_balance:
                ins_calculated_row['treat_section2'] = treat_count
                treat_count = 0
            else:
                ins_calculated_row['treat_section2'] = section2_balance
                treat_count -= section2_balance

            section2_balance -= ins_calculated_row['treat_section2']

            if treat_count <= 0:
                continue

            ins_calculated_row['treat_section3'] = treat_count

    def _get_full_time_doctor_treat_balance(self):
        section1_balance = 0
        section2_balance = 0

        for ins_calculated_row in self.ins_calculated_table:
            if ins_calculated_row['doctor_type'] == '支援醫師':
                continue

            diag_days = ins_calculated_row['diag_days']
            treat_section1_limit = diag_days * nhi_utils.TREAT_SECTION1
            treat_section2_limit = diag_days * (nhi_utils.TREAT_SECTION2 - nhi_utils.TREAT_SECTION1)

            if ins_calculated_row['treat_section1'] < treat_section1_limit:
                section1_balance += treat_section1_limit - ins_calculated_row['treat_section1']
            if ins_calculated_row['treat_section2'] < treat_section2_limit:
                section2_balance += treat_section2_limit - ins_calculated_row['treat_section2']

        return section1_balance, section2_balance
