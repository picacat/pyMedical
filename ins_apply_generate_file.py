#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore

from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import case_utils
from libs import personnel_utils
from libs import charge_utils


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
            '25': 0,
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
                (ClinicID = "{clinic_id}") AND
                (ApplyDate = "{apply_date}") AND
                (ApplyPeriod = "{apply_period}") AND
                (ApplyType = "{apply_type}")
        '''.format(
            clinic_id=self.clinic_id,
            apply_date=self.apply_date,
            apply_period=self.period,
            apply_type=nhi_utils.APPLY_TYPE_DICT[self.apply_type],
        )
        self.database.exec_sql(sql)

    def _get_medical_records(self):
        start_date = self.start_date.toString("yyyy-MM-dd 00:00:00")
        end_date = self.end_date.toString("yyyy-MM-dd 23:59:59")
        apply_type_sql = nhi_utils.get_apply_type_sql(self.apply_type)  # 只取得申報類別為申報或補報的資料,不申報不讀取

        sql = '''
            SELECT 
                cases.*, patient.Birthday, patient.ID
            FROM cases 
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                (CaseDate BETWEEN "{start_date}" AND "{end_date}") AND
                (cases.InsType = "健保") AND
                ({apply_type_sql}) 
            ORDER BY CaseDate
        '''.format(
            start_date=start_date,
            end_date=end_date,
            apply_type_sql=apply_type_sql,
        )
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

            if string_utils.xstr(row['Card']) == '欠卡':  # 欠卡不報
                continue

            if string_utils.xstr(row['TreatType']) == '腦血管疾病':
                ins_apply_row = self._need_merge_brain_record(row)
            else:
                ins_apply_row = self._need_merge_record(row)

            if ins_apply_row is None:
                self._write_ins_record(row)
            else:
                self._rewrite_ins_record(ins_apply_row, row)

        progress_dialog.setValue(record_count)

    # 檢查是否需要合併病歷 (腦血管疾病案件)
    def _need_merge_brain_record(self, row):
        ins_apply_row = None

        patient_key = number_utils.get_integer(row['PatientKey'])

        sql = '''
            SELECT * FROM insapply
            WHERE
                ClinicID = "{clinic_id}" AND
                ApplyDate = "{apply_date}" AND
                ApplyPeriod = "{apply_period}" AND
                ApplyType = "{apply_type}" AND
                PatientKey = {patient_key} AND
                CaseType = "30"
        '''.format(
            clinic_id=self.clinic_id,
            apply_date=self.apply_date,
            apply_period=self.period,
            apply_type=nhi_utils.APPLY_TYPE_DICT[self.apply_type],
            patient_key=patient_key,
        )
        ins_apply_rows = self.database.select_record(sql)
        if len(ins_apply_rows) > 0:
            ins_apply_row = ins_apply_rows[0]

        return ins_apply_row

    # 檢查是否需要合併病歷 (一般或療程案件)
    def _need_merge_record(self, row):
        ins_apply_row = None

        course = number_utils.get_integer(row['Continuance'])
        if course <= 1:
            return ins_apply_row

        patient_key = number_utils.get_integer(row['PatientKey'])
        card = string_utils.xstr(row['Card'])

        # 找出同卡序且有執行療程首次的病歷
        sql = '''
            SELECT * FROM insapply
            WHERE
                ClinicID = "{clinic_id}" AND
                ApplyDate = "{apply_date}" AND
                ApplyPeriod = "{apply_period}" AND
                ApplyType = "{apply_type}" AND
                PatientKey = {patient_key} AND
                Card = "{card}" AND
                TreatCode1 IS NOT NULL AND
                TreatCode{course} IS NULL
        '''.format(
            clinic_id=self.clinic_id,
            apply_date=self.apply_date,
            apply_period=self.period,
            apply_type=nhi_utils.APPLY_TYPE_DICT[self.apply_type],
            patient_key=patient_key,
            card=card,
            course=string_utils.xstr(course),
        )

        ins_apply_rows = self.database.select_record(sql)

        if len(ins_apply_rows) <= 0:  # 首次不在本月
            sql = '''
            SELECT * FROM insapply
            WHERE
                ClinicID = "{clinic_id}" AND
                ApplyDate = "{apply_date}" AND
                ApplyPeriod = "{apply_period}" AND
                ApplyType = "{apply_type}" AND
                PatientKey = {patient_key} AND
                Card = "{card}" AND
                TreatCode{course} IS NULL
            '''.format(
                    clinic_id=self.clinic_id,
                    apply_date=self.apply_date,
                    apply_period=self.period,
                    apply_type=nhi_utils.APPLY_TYPE_DICT[self.apply_type],
                    patient_key=patient_key,
                    card=card,
                    course=string_utils.xstr(course),
                )

            ins_apply_rows = self.database.select_record(sql)

        if len(ins_apply_rows) > 0:
            ins_apply_row = ins_apply_rows[0]

        return ins_apply_row

    def _check_error(self, row):
        message = []
        doctor_name = string_utils.xstr(row['Doctor']).replace(',', '')
        doctor_id = personnel_utils.get_personnel_field_value(self.database, doctor_name, 'ID')

        if row['Birthday'] is None:
            message.append('病患生日空白')
        if row['ID'] is None:
            message.append('病患身份證空白')
        if row['Card'] is None:
            message.append('卡序空白')
        if string_utils.xstr(row['Card']) == '欠卡':
            message.append('欠卡')
        if row['DiseaseCode1'] is None:
            message.append('主診斷碼空白')
        if doctor_name == '':
            message.append('醫師姓名空白')
        if doctor_id in ['', None]:
            message.append('醫師身份證空白')
        if number_utils.get_integer(row['InsApplyFee']) <= 0:
            message.append('申報金額<=0')
        if row['Name'] is None:
            message.append('病患空白')

        return message

    def _write_ins_record(self, row):
        case_type = nhi_utils.get_case_type(self.database, self.system_settings, row)

        special_code = nhi_utils.get_special_code(self.database, self.system_settings, row['CaseKey'])
        pres_days = case_utils.get_pres_days(self.database, row['CaseKey'])
        treat_records = nhi_utils.get_treat_records(self.database, row)
        drug_fee = number_utils.get_integer(row['InterDrugFee'])
        doctor_name = string_utils.xstr(row['Doctor']).replace(',', '')

        if string_utils.xstr(row['TreatType']) in ['腦血管疾病']:
            treat_fee = treat_records[0]['TreatFee']
        else:
            treat_fee = (
                    number_utils.get_integer(row['AcupunctureFee']) +
                    number_utils.get_integer(row['MassageFee']) +
                    number_utils.get_integer(row['DislocateFee']) +
                    number_utils.get_integer(row['ExamFee'])
            )

        diag_code = nhi_utils.get_diag_code(
            self.database,
            self.system_settings,
            doctor_name,
            string_utils.xstr(row['RegistType']),
            string_utils.xstr(row['TreatType']),
            number_utils.get_integer(row['DiagFee']),
        )
        diag_fee = charge_utils.get_ins_fee_from_ins_code(self.database, diag_code)
        pharmacy_code = nhi_utils.get_pharmacy_code(
            self.system_settings, row, pres_days,
        )
        pharmacy_fee = number_utils.get_integer(row['PharmacyFee'])
        ins_total_fee = drug_fee + treat_fee + diag_fee + pharmacy_fee
        share_fee = (
            number_utils.get_integer(row['DiagShareFee']) +
            number_utils.get_integer(row['DrugShareFee'])
        )
        ins_apply_fee = ins_total_fee - share_fee

        if self.system_settings.field('申報初診照護') == 'Y':
            first_visit = nhi_utils.get_visit(self.database, row)
        else:
            first_visit = None

        card = string_utils.xstr(row['Card'])
        # if case_type == 'B6':  # 2019.08.08 void, 改以xml控制 4 bytes
        #     card = nhi_utils.OCCUPATIONAL_INJURY_CARD

        message = self._check_error(row)

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
            'Message'
        ]

        data = [
            self.clinic_id, self.apply_date, self.period, nhi_utils.APPLY_TYPE_DICT[self.apply_type],
            case_type, self._get_sequence(case_type),
            special_code[0], special_code[1], special_code[2], special_code[3],
            nhi_utils.INS_CLASS, nhi_utils.get_start_date(self.database, row), row['CaseDate'].date(),
            row['Birthday'], string_utils.xstr(row['ID']), card,
            nhi_utils.INJURY_DICT[string_utils.xstr(row['Injury'])],
            nhi_utils.get_diag_share_code(
                self.database,
                string_utils.xstr(row['Share']),
                string_utils.xstr(row['Treatment']),
                number_utils.get_integer(row['Continuance']),
                row,
            ),
            first_visit,
            string_utils.xstr(row['DiseaseCode1']), string_utils.xstr(row['DiseaseCode2']),
            string_utils.xstr(row['DiseaseCode3']),
            pres_days, nhi_utils.get_pres_type(pres_days),
            doctor_name,
            personnel_utils.get_personnel_field_value(
                self.database, doctor_name, 'ID'
            ),
            nhi_utils.get_pharmacist_id(self.database, self.system_settings, row),
            drug_fee, treat_fee, diag_code, diag_fee,
            pharmacy_code,
            pharmacy_fee, ins_total_fee, share_fee, ins_apply_fee,
            number_utils.get_integer(row['AgentFee']),
            number_utils.get_integer(row['PatientKey']),
            string_utils.xstr(row['Name']),
            treat_records[0]['CaseKey'], treat_records[0]['TreatCode'], treat_records[0]['TreatFee'],
            treat_records[0]['Percent'],
            treat_records[1]['CaseKey'], treat_records[1]['TreatCode'], treat_records[1]['TreatFee'],
            treat_records[1]['Percent'],
            treat_records[2]['CaseKey'], treat_records[2]['TreatCode'], treat_records[2]['TreatFee'],
            treat_records[2]['Percent'],
            treat_records[3]['CaseKey'], treat_records[3]['TreatCode'], treat_records[3]['TreatFee'],
            treat_records[3]['Percent'],
            treat_records[4]['CaseKey'], treat_records[4]['TreatCode'], treat_records[4]['TreatFee'],
            treat_records[4]['Percent'],
            treat_records[5]['CaseKey'], treat_records[5]['TreatCode'], treat_records[5]['TreatFee'],
            treat_records[5]['Percent'],
            ', '.join(message),
        ]

        self.database.insert_record('insapply', fields, data)

    def _rewrite_ins_record(self, ins_apply_row, case_row):
        ins_apply_key = number_utils.get_integer(ins_apply_row['InsApplyKey'])
        pres_days = case_utils.get_pres_days(self.database, case_row['CaseKey'])

        pres_type = string_utils.xstr(ins_apply_row['PresType'])
        if pres_type == '2' and pres_days > 0:  # 首次未開處方, 但療程有開處方
            pres_type = nhi_utils.get_pres_type(pres_days)

        treat_records = nhi_utils.get_treat_records(self.database, case_row, ins_apply_row)

        if string_utils.xstr(case_row['TreatType']) in ['腦血管疾病']:
            treat_fee = treat_records[0]['TreatFee']
            ins_total_fee = (  # 重新計算申報總金額, 須扣除病歷內的處置費及原本申報金額的處置費, 再加上新的處置費
                    number_utils.get_integer(ins_apply_row['InsTotalFee']) +
                    number_utils.get_integer(case_row['InterDrugFee']) +
                    number_utils.get_integer(case_row['PharmacyFee']) +
                    treat_fee -
                    number_utils.get_integer(ins_apply_row['TreatFee'])
            )
        else:
            treat_fee = (
                    number_utils.get_integer(ins_apply_row['TreatFee']) +
                    number_utils.get_integer(case_row['AcupunctureFee']) +
                    number_utils.get_integer(case_row['MassageFee']) +
                    number_utils.get_integer(case_row['DislocateFee']) +
                    number_utils.get_integer(case_row['ExamFee'])
            )
            ins_total_fee = (
                    number_utils.get_integer(ins_apply_row['InsTotalFee']) +
                    number_utils.get_integer(case_row['InsTotalFee'])
            )

        share_fee = (
                number_utils.get_integer(ins_apply_row['ShareFee']) +
                number_utils.get_integer(case_row['DiagShareFee']) +
                number_utils.get_integer(case_row['DrugShareFee'])
        )

        doctor_name = string_utils.xstr(case_row['Doctor']).replace(',', '')
        doctor_id = personnel_utils.get_personnel_field_value(
            self.database, doctor_name, 'ID'
        )

        drug_fee = (number_utils.get_integer(ins_apply_row['DrugFee']) +
                    number_utils.get_integer(case_row['InterDrugFee']))
        pharmacy_code = nhi_utils.get_pharmacy_code(
            self.system_settings,
            case_row, pres_days,
            string_utils.xstr(ins_apply_row['PharmacyCode'])
        )
        pharmacy_fee = (number_utils.get_integer(ins_apply_row['PharmacyFee']) +
                        number_utils.get_integer(case_row['PharmacyFee']))

        pharmacist_id = string_utils.xstr(ins_apply_row['PharmacistID'])
        if pharmacy_fee > 0 and pharmacist_id == '':
            pharmacist_id = nhi_utils.get_pharmacist_id(self.database, self.system_settings, case_row)

        ins_apply_fee = ins_total_fee - share_fee
        share_code = string_utils.xstr(ins_apply_row['ShareCode'])
        if share_code == '009' and share_fee > 0:  # 療程中開藥
            share_code = 'S20'

        fields = [
            'DoctorName', 'DoctorID',
            'StopDate', 'PresDays', 'PresType',
            'DrugFee', 'TreatFee', 'PharmacyCode', 'PharmacyFee', 'PharmacistID',
            'ShareCode',
            'InsTotalFee', 'ShareFee', 'InsApplyFee', 'AgentFee',
            'CaseKey1', 'TreatCode1', 'TreatFee1', 'Percent1',
            'CaseKey2', 'TreatCode2', 'TreatFee2', 'Percent2',
            'CaseKey3', 'TreatCode3', 'TreatFee3', 'Percent3',
            'CaseKey4', 'TreatCode4', 'TreatFee4', 'Percent4',
            'CaseKey5', 'TreatCode5', 'TreatFee5', 'Percent5',
            'CaseKey6', 'TreatCode6', 'TreatFee6', 'Percent6',
        ]

        data = [
            doctor_name, doctor_id,
            case_row['CaseDate'].date(),
            (number_utils.get_integer(ins_apply_row['PresDays']) + pres_days),
            pres_type,
            drug_fee,
            treat_fee,
            pharmacy_code,
            pharmacy_fee,
            pharmacist_id,
            share_code,
            ins_total_fee,
            share_fee,
            ins_apply_fee,
            (number_utils.get_integer(ins_apply_row['AgentFee']) +
             number_utils.get_integer(case_row['AgentFee'])),
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

