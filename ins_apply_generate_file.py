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
from libs import case_utils
from libs import personnel_utils


# 候診名單 2018.01.31
class InsApplyGenerateFile(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsApplyGenerateFile, self).__init__(parent)
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

        self.sequence = {
            '21': 0,
            '22': 0,
            '24': 0,
            '29': 0,
            '30': 0,
            'B6': 0,
        }

        self.apply_date = '{0:0>3}{1:0>2}'.format(self.apply_year-1911, self.apply_month)
        self.ui = None

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

    def generate_ins_file(self):
        self._delete_existing_data()
        rows = self._get_medical_records()
        self._create_ins_records(rows)

    def _delete_existing_data(self):
        sql = '''
            DELETE FROM insapply 
            WHERE 
                ClinicID = "{0}" AND
                ApplyDate = "{1}" AND
                ApplyPeriod = "{2}" AND
                ApplyType = "{3}"
        '''.format(self.clinic_id, self.apply_date, self.period,
                   nhi_utils.APPLY_TYPE_DICT[self.apply_type])
        self.database.exec_sql(sql)

    def _get_medical_records(self):
        start_date = self.start_date.toString("yyyy-MM-dd 00:00:00")
        end_date = self.end_date.toString("yyyy-MM-dd 23:59:59")

        sql = '''
            SELECT 
                cases.*, patient.Birthday, patient.ID
            FROM cases 
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                (CaseDate BETWEEN "{0}" AND "{1}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") AND
                (ApplyType = "{2}") 
            ORDER BY CaseDate
        '''.format(start_date, end_date, self.apply_type)
        rows = self.database.select_record(sql)

        return rows

    def _create_ins_records(self, rows):
        record_count = len(rows)
        progress_dialog = QtWidgets.QProgressDialog(
            '正在產生申報檔中, 請稍後...', '取消', 0, record_count, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for row_no, row in zip(range(record_count), rows):
            progress_dialog.setValue(row_no)
            if progress_dialog.wasCanceled():
                break

            ins_apply_row = self._need_merge_record(row)
            if ins_apply_row is None:
                self._write_ins_record(row)
            else:
                self._rewrite_ins_record(ins_apply_row, row)

        progress_dialog.setValue(record_count)

    def _need_merge_record(self, row):
        ins_apply_row = None
        course = number_utils.get_integer(row['Continuance'])
        if course <= 1:
            return ins_apply_row

        patient_key = number_utils.get_integer(row['PatientKey'])
        card = string_utils.xstr(row['Card'])
        sql = '''
            SELECT * FROM insapply
            WHERE
                ClinicID = "{0}" AND
                ApplyDate = "{1}" AND
                ApplyPeriod = "{2}" AND
                ApplyType = "{3}" AND
                PatientKey = {4} AND
                Card = "{5}"
        '''.format(
            self.clinic_id, self.apply_date, self.period,
            nhi_utils.APPLY_TYPE_DICT[self.apply_type],
            patient_key, card,
        )
        ins_apply_rows = self.database.select_record(sql)
        if len(ins_apply_rows) > 0:
            ins_apply_row = ins_apply_rows[0]

        return ins_apply_row

    def _write_ins_record(self, row):
        case_type = nhi_utils.get_case_type(self.database, self.system_settings, row)
        special_code = nhi_utils.get_special_code(self.database, row['CaseKey'])
        pres_days = case_utils.get_pres_days(self.database, row['CaseKey'])
        treat_records = nhi_utils.get_treat_records(self.database, row)

        fields = [
            'ClinicID', 'ApplyDate', 'ApplyPeriod', 'ApplyType', 'CaseType', 'Sequence',
            'SpecialCode1', 'SpecialCode2', 'SpecialCode3', 'SpecialCode4',
            'Class', 'CaseDate', 'StopDate', 'Birthday', 'ID', 'Card', 'Injury', 'ShareCode',
            'Visit', 'DiseaseCode1', 'DiseaseCode2', 'DiseaseCode3', 'PresDays', 'PresType',
            'DoctorName', 'DoctorID', 'PharmacistID',
            'DrugFee', 'TreatFee', 'DiagCode', 'DiagFee', 'PharmacyCode', 'PharmacyFee',
            'InsTotalFee', 'ShareFee', 'InsApplyFee', 'AgentFee',
            'PatientKey', 'Name',
            'CaseKey1', 'TreatCode1', 'TreatFee1', 'Percent1',
            'CaseKey2', 'TreatCode2', 'TreatFee2', 'Percent2',
            'CaseKey3', 'TreatCode3', 'TreatFee3', 'Percent3',
            'CaseKey4', 'TreatCode4', 'TreatFee4', 'Percent4',
            'CaseKey5', 'TreatCode5', 'TreatFee5', 'Percent5',
            'CaseKey6', 'TreatCode6', 'TreatFee6', 'Percent6',
        ]

        data = [
            self.clinic_id,
            self.apply_date,
            self.period,
            nhi_utils.APPLY_TYPE_DICT[self.apply_type],
            case_type,
            self._get_sequence(case_type),
            special_code[0],
            special_code[1],
            special_code[2],
            special_code[3],
            nhi_utils.INS_CLASS,
            nhi_utils.get_start_date(self.database, row),
            row['CaseDate'].date(),
            row['Birthday'],
            string_utils.xstr(row['ID']),
            string_utils.xstr(row['Card'])[:4],
            nhi_utils.INJURY_DICT[string_utils.xstr(row['Injury'])],
            nhi_utils.get_diag_share_code(
                self.database,
                string_utils.xstr(row['Share']),
                string_utils.xstr(row['Treatment']),
                number_utils.get_integer(row['Continuance'])
            ),
            nhi_utils.get_visit(row),
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseCode2']),
            string_utils.xstr(row['DiseaseCode3']),
            pres_days,
            nhi_utils.get_pres_type(pres_days),
            string_utils.xstr(row['Doctor']),
            personnel_utils.get_personnel_id(
                self.database, string_utils.xstr(row['Doctor'])
            ),
            nhi_utils.get_pharmacist_id(self.database, self.system_settings, row),
            number_utils.get_integer(row['InterDrugFee']),
            (number_utils.get_integer(row['AcupunctureFee']) +
             number_utils.get_integer(row['MassageFee']) +
             number_utils.get_integer(row['DislocateFee']) +
             number_utils.get_integer(row['ExamFee'])),
            nhi_utils.get_diag_code(
                self.system_settings,
                string_utils.xstr(row['TreatType']),
                number_utils.get_integer(row['DiagFee']),
            ),
            number_utils.get_integer(row['DiagFee']),
            nhi_utils.get_pharmacy_code(
                self.system_settings,
                row, pres_days,
            ),
            number_utils.get_integer(row['PharmacyFee']),
            number_utils.get_integer(row['InsTotalFee']),
            (number_utils.get_integer(row['DiagShareFee']) +
             number_utils.get_integer(row['DrugShareFee'])),
            number_utils.get_integer(row['InsApplyFee']),
            number_utils.get_integer(row['AgentFee']),
            number_utils.get_integer(row['PatientKey']),
            string_utils.xstr(row['Name']),
            treat_records[0]['CaseKey'],
            treat_records[0]['TreatCode'],
            treat_records[0]['TreatFee'],
            treat_records[0]['Percent'],
            treat_records[1]['CaseKey'],
            treat_records[1]['TreatCode'],
            treat_records[1]['TreatFee'],
            treat_records[1]['Percent'],
            treat_records[2]['CaseKey'],
            treat_records[2]['TreatCode'],
            treat_records[2]['TreatFee'],
            treat_records[2]['Percent'],
            treat_records[3]['CaseKey'],
            treat_records[3]['TreatCode'],
            treat_records[3]['TreatFee'],
            treat_records[3]['Percent'],
            treat_records[4]['CaseKey'],
            treat_records[4]['TreatCode'],
            treat_records[4]['TreatFee'],
            treat_records[4]['Percent'],
            treat_records[5]['CaseKey'],
            treat_records[5]['TreatCode'],
            treat_records[5]['TreatFee'],
            treat_records[5]['Percent'],
        ]

        self.database.insert_record('insapply', fields, data)

    def _rewrite_ins_record(self, ins_apply_row, row):
        ins_apply_key = number_utils.get_integer(ins_apply_row['InsApplyKey'])
        pres_days = case_utils.get_pres_days(self.database, row['CaseKey'])
        treat_records = nhi_utils.get_treat_records(self.database, row, ins_apply_row)

        fields = [
            'StopDate', 'PresDays',
            'DrugFee', 'TreatFee', 'PharmacyCode', 'PharmacyFee',
            'InsTotalFee', 'ShareFee', 'InsApplyFee', 'AgentFee',
            'CaseKey1', 'TreatCode1', 'TreatFee1', 'Percent1',
            'CaseKey2', 'TreatCode2', 'TreatFee2', 'Percent2',
            'CaseKey3', 'TreatCode3', 'TreatFee3', 'Percent3',
            'CaseKey4', 'TreatCode4', 'TreatFee4', 'Percent4',
            'CaseKey5', 'TreatCode5', 'TreatFee5', 'Percent5',
            'CaseKey6', 'TreatCode6', 'TreatFee6', 'Percent6',
        ]

        data = [
            row['CaseDate'].date(),
            (number_utils.get_integer(ins_apply_row['PresDays']) + pres_days),
            (number_utils.get_integer(ins_apply_row['DrugFee']) +
             number_utils.get_integer(row['InterDrugFee'])),
            (number_utils.get_integer(ins_apply_row['TreatFee']) +
             number_utils.get_integer(row['AcupunctureFee']) +
             number_utils.get_integer(row['MassageFee']) +
             number_utils.get_integer(row['DislocateFee']) +
             number_utils.get_integer(row['ExamFee'])),
            nhi_utils.get_pharmacy_code(
                self.system_settings,
                row, pres_days,
                string_utils.xstr(ins_apply_row['PharmacyCode'])
            ),
            (number_utils.get_integer(ins_apply_row['PharmacyFee']) +
             number_utils.get_integer(row['PharmacyFee'])),
            (number_utils.get_integer(ins_apply_row['InsTotalFee']) +
             number_utils.get_integer(row['InsTotalFee'])),
            (number_utils.get_integer(ins_apply_row['ShareFee']) +
             number_utils.get_integer(row['DiagShareFee']) +
             number_utils.get_integer(row['DrugShareFee'])),
            (number_utils.get_integer(ins_apply_row['InsApplyFee']) +
             number_utils.get_integer(row['InsApplyFee'])),
            (number_utils.get_integer(ins_apply_row['AgentFee']) +
             number_utils.get_integer(row['AgentFee'])),
            treat_records[0]['CaseKey'],
            treat_records[0]['TreatCode'],
            treat_records[0]['TreatFee'],
            treat_records[0]['Percent'],
            treat_records[1]['CaseKey'],
            treat_records[1]['TreatCode'],
            treat_records[1]['TreatFee'],
            treat_records[1]['Percent'],
            treat_records[2]['CaseKey'],
            treat_records[2]['TreatCode'],
            treat_records[2]['TreatFee'],
            treat_records[2]['Percent'],
            treat_records[3]['CaseKey'],
            treat_records[3]['TreatCode'],
            treat_records[3]['TreatFee'],
            treat_records[3]['Percent'],
            treat_records[4]['CaseKey'],
            treat_records[4]['TreatCode'],
            treat_records[4]['TreatFee'],
            treat_records[4]['Percent'],
            treat_records[5]['CaseKey'],
            treat_records[5]['TreatCode'],
            treat_records[5]['TreatFee'],
            treat_records[5]['Percent'],
        ]
        self.database.update_record('insapply', fields, 'InsApplyKey', ins_apply_key, data)

    def _get_sequence(self, case_type):
        self.sequence[case_type] += 1

        return self.sequence[case_type]

