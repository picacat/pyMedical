#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore

from libs import string_utils
from libs import nhi_utils
from libs import charge_utils
from libs import number_utils


# 候診名單 2018.01.31
class InsApplyAdjustFee(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsApplyAdjustFee, self).__init__(parent)
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
        self.ins_calculated_table = args[9]
        self.ui = None

        self.apply_date = nhi_utils.get_apply_date(self.apply_year, self.apply_month)
        self.apply_type_code = nhi_utils.APPLY_TYPE_CODE[self.apply_type]

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

    def adjust_ins_fee(self):
        progress_dialog = QtWidgets.QProgressDialog(
            '正在調整申報檔各項費用中, 請稍後...', '取消', 0, 7, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        self._adjust_diag_fee()
        progress_dialog.setValue(1)

        self._adjust_nurse_diag_fee()
        progress_dialog.setValue(2)

        self._adjust_child_diag_fee()
        progress_dialog.setValue(3)

        self._adjust_treat_fee()
        progress_dialog.setValue(4)

        self._adjust_treat_drug_fee()
        progress_dialog.setValue(5)

        self._adjust_first_visit_fee()
        progress_dialog.setValue(6)

        self._adjust_care_fee()
        progress_dialog.setValue(7)

    # 診察費調整, 特定照護不列入計算
    def _adjust_diag_fee(self):
        for row in self.ins_calculated_table:
            diag_section1 = row['diag_section1']
            diag_section2 = (
                    row['diag_section1'] +
                    row['diag_section2']
            )
            diag_section3 = (
                    row['diag_section1'] +
                    row['diag_section2'] +
                    row['diag_section3']
            )
            diag_section4 = (
                    row['diag_section1'] +
                    row['diag_section2'] +
                    row['diag_section3'] +
                    row['diag_section4']
            )
            diag_section5 = (
                    row['diag_section1'] +
                    row['diag_section2'] +
                    row['diag_section3'] +
                    row['diag_section4'] +
                    row['diag_section5']
            )

            ins_apply_rows = self._get_ins_apply_rows(row['doctor_id'])  # 不含照護及職業傷害, 三歲兒童放在最前面
            for ins_row_no, ins_row in zip(range(1, len(ins_apply_rows)+1), ins_apply_rows):
                if ins_row_no <= diag_section1:  # 第一段不調整
                    pass
                elif ins_row_no <= diag_section2:
                    self._adjust_diag_section2(ins_row)
                elif ins_row_no <= diag_section3:
                    self._adjust_diag_section3(ins_row)
                elif ins_row_no <= diag_section4:
                    self._adjust_diag_section4(ins_row)
                elif ins_row_no <= diag_section5:
                    self._adjust_diag_section5(ins_row)

    def _adjust_diag_section1(self, row):
        diag_code = row['DiagCode']
        charge_utils.update_ins_apply_diag_fee(
            self.database, self.system_settings,
            row['InsApplyKey'], diag_code
        )

    def _adjust_diag_section2(self, row):
        diag_code = row['DiagCode']
        if diag_code == 'A01':
            diag_code = 'A03'
        elif diag_code == 'A02':
            diag_code = 'A04'

        charge_utils.update_ins_apply_diag_fee(
            self.database, self.system_settings,
            row['InsApplyKey'], diag_code
        )

    def _adjust_diag_section3(self, row):
        diag_code = row['DiagCode']
        if diag_code == 'A01':
            diag_code = 'A05'
        elif diag_code == 'A02':
            diag_code = 'A06'

        charge_utils.update_ins_apply_diag_fee(
            self.database, self.system_settings,
            row['InsApplyKey'], diag_code
        )

    def _adjust_diag_section4(self, row):
        diag_code = 'A07'
        charge_utils.update_ins_apply_diag_fee(
            self.database, self.system_settings,
            row['InsApplyKey'], diag_code
        )

    def _adjust_diag_section5(self, row):
        diag_code = 'A08'
        charge_utils.update_ins_apply_diag_fee(
            self.database, self.system_settings,
            row['InsApplyKey'], diag_code
        )

    # 不含加強照護類及職業傷害
    def _get_ins_apply_rows(self, doctor_id):
        sql = '''
            SELECT InsApplyKey, Sequence, DoctorName, DiagCode, DiagFee, InsTotalFee, InsApplyFee
            FROM insapply
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}" AND
                DoctorID = "{4}" AND
                DiagFee > 0 AND
                CaseType NOT IN {5}
                ORDER BY CaseType, Field(ShareCode, '902', 'S10', 'S20', '003', '004'), Sequence
        '''.format(
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
            doctor_id, tuple(nhi_utils.EXCLUDE_DIAG_ADJUST)
        )
        rows = self.database.select_record(sql)

        return rows

    def _adjust_nurse_diag_fee(self):
        if number_utils.get_integer(self.system_settings.field('護士人數')) <= 0:  # 無護士, 不需調整
            return

        sql = '''
            SELECT 
                InsApplyKey, Sequence, CaseKey1, DoctorName, DiagCode, DiagFee, InsTotalFee, InsApplyFee
            FROM insapply
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}" AND
                DiagFee > 0 AND
                CaseType NOT IN {4}
                ORDER BY CaseType, Sequence
        '''.format(
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
            tuple(nhi_utils.EXCLUDE_DIAG_ADJUST)
        )
        rows = self.database.select_record(sql)

        for row in rows:
            case_key = row['CaseKey1']
            doctor_name = string_utils.xstr(row['DoctorName'])
            diag_code = row['DiagCode']
            if not nhi_utils.nurse_schedule_on_duty(self.database, case_key, doctor_name):
                if diag_code in ['A01', 'A03', 'A05']:
                    if diag_code == 'A01':
                        diag_code = 'A02'
                    elif diag_code == 'A03':
                        diag_code = 'A04'
                    elif diag_code == 'A05':
                        diag_code = 'A06'

                charge_utils.update_ins_apply_diag_fee(
                    self.database, self.system_settings,
                    row['InsApplyKey'], diag_code
                )

    def _adjust_child_diag_fee(self):
        sql = '''
                SELECT *
                FROM insapply
                WHERE
                    ApplyDate = "{0}" AND
                    ApplyType = "{1}" AND
                    ApplyPeriod = "{2}" AND
                    ClinicID = "{3}" AND
                    ShareCode = "902" AND
                    DiagFee > 0
                    ORDER BY Sequence
            '''.format(
            self.apply_date, self.apply_type_code,
            self.period, self.clinic_id,
        )
        rows = self.database.select_record(sql)

        for row in rows:
            ins_apply_key = row['InsApplyKey']

            extra_diag_fee = int(row['DiagFee'] * 20 / 100)
            diag_fee = row['DiagFee'] + extra_diag_fee
            ins_total_fee = row['InsTotalFee'] + extra_diag_fee
            ins_apply_fee = row['InsApplyFee'] + extra_diag_fee

            fields = ['DiagFee', 'InsTotalFee', 'InsApplyFee']
            data = [diag_fee, ins_total_fee, ins_apply_fee]

            self.database.update_record('insapply', fields, 'InsApplyKey', ins_apply_key, data)

    def _adjust_treat_fee(self):
        for ins_calculated_row in self.ins_calculated_table:
            doctor_name = ins_calculated_row['doctor_name']
            sql = '''
                SELECT *
                FROM insapply
                WHERE
                    ApplyDate = "{0}" AND
                    ApplyType = "{1}" AND
                    ApplyPeriod = "{2}" AND
                    ClinicID = "{3}" AND
                    DoctorName = "{4}" AND
                    CaseType = "29"
                    ORDER BY Sequence
            '''.format(
                self.apply_date, self.apply_type_code,
                self.period, self.clinic_id, doctor_name,
            )
            rows = self.database.select_record(sql)

            treat_section1 = ins_calculated_row['treat_section1']
            treat_section2 = (
                    ins_calculated_row['treat_section1'] +
                    ins_calculated_row['treat_section2']
            )
            treat_section3 = (
                    ins_calculated_row['treat_section1'] +
                    ins_calculated_row['treat_section2'] +
                    ins_calculated_row['treat_section3']
            )

            treat_count = 0
            complicated_massage_count = 0
            for row in rows:
                for course in range(1, nhi_utils.MAX_COURSE+1):
                    treat_code = string_utils.xstr(row['TreatCode{0}'.format(course)])
                    treat_fee = number_utils.get_integer(row['TreatFee{0}'.format(course)])
                    if treat_code == '' or treat_fee <= 0:
                        continue

                    treat_count += 1
                    if treat_code in nhi_utils.COMPLICATED_TREAT_CODE:
                        complicated_massage_count += 1

                    ins_apply_key = row['InsApplyKey']
                    if treat_count <= treat_section1:
                        pass
                    elif treat_count <= treat_section2:
                        if (treat_code in nhi_utils.TREAT_CODE or   # 針傷未開藥才調整
                                (treat_code in nhi_utils.COMPLICATED_TREAT_CODE and
                                 complicated_massage_count > nhi_utils.MAX_COMPLICATED_TREAT)):  # 複雜性傷科超過限量, 也要參與分配
                            treat_percent = 90
                            charge_utils.update_treat_fee(
                                self.database, ins_apply_key, course, treat_percent
                            )
                    elif treat_count <= treat_section3:
                        treat_percent = 0
                        charge_utils.update_treat_fee(
                            self.database, ins_apply_key, course, treat_percent
                        )

    # 計算針灸傷科給藥上限 (每位醫師平均 專任醫師數 * 120)
    def _adjust_treat_drug_fee(self):
        max_full_time_doctor = 0
        for ins_calculated_row in self.ins_calculated_table:  # 取得專任醫師數
            if ins_calculated_row['doctor_type'] == '醫師':
                max_full_time_doctor += 1

        max_treat_drug = max_full_time_doctor * nhi_utils.MAX_TREAT_DRUG

        sql = '''
            SELECT *
            FROM insapply
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}" AND
                CaseType = "29"
                ORDER BY Sequence
        '''.format(
            self.apply_date, self.apply_type_code,
            self.period, self.clinic_id,
        )
        rows = self.database.select_record(sql)

        treat_drug_count = 0
        for row in rows:
            for course in range(1, nhi_utils.MAX_COURSE+1):
                treat_code = string_utils.xstr(row['TreatCode{0}'.format(course)])
                if treat_code not in nhi_utils.TREAT_DRUG_CODE:  # 無開藥不調整
                    continue

                treat_drug_count += 1

                ins_apply_key = row['InsApplyKey']
                if treat_drug_count > max_treat_drug:
                    treat_percent = 50
                    charge_utils.update_treat_fee(
                        self.database, ins_apply_key, course, treat_percent
                    )

    def _adjust_first_visit_fee(self):
        if self.system_settings.field('申報初診照護') == 'N':
            return

        sql = '''
                SELECT *
                FROM insapply
                WHERE
                    ApplyDate = "{0}" AND
                    ApplyType = "{1}" AND
                    ApplyPeriod = "{2}" AND
                    ClinicID = "{3}" AND
                    DiagFee > 0
                    GROUP BY ID
            '''.format(
            self.apply_date, self.apply_type_code,
            self.period, self.clinic_id,
        )
        rows = self.database.select_record(sql)
        first_visit_limit = int(len(rows) * 10 / 100)  # 初診照護為總歸戶人數的10%

        sql = '''
                SELECT *
                FROM insapply
                WHERE
                    ApplyDate = "{0}" AND
                    ApplyType = "{1}" AND
                    ApplyPeriod = "{2}" AND
                    ClinicID = "{3}" AND
                    Visit = "初診照護"
                    GROUP BY CaseType, Sequence
            '''.format(
            self.apply_date, self.apply_type_code,
            self.period, self.clinic_id,
        )
        rows = self.database.select_record(sql)
        first_visit_fee = charge_utils.get_ins_fee_from_ins_code(self.database, 'A90')

        for row_no, row in zip(range(1, len(rows)+1), rows):
            ins_apply_key = row['InsApplyKey']
            if row_no <= first_visit_limit:
                fields = ['TreatFee', 'InsTotalFee', 'InsApplyFee']
                data = [
                    number_utils.get_integer(row['TreatFee']) + first_visit_fee,
                    number_utils.get_integer(row['InsTotalFee']) + first_visit_fee,
                    number_utils.get_integer(row['InsApplyFee']) + first_visit_fee,
                ]
            else:
                fields = ['Visit']
                data = [None]

            self.database.update_record('insapply', fields, 'InsApplyKey', ins_apply_key, data)

    def _adjust_care_fee(self):
        pass
