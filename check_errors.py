#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime

from classes import table_widget

from libs import ui_utils
from libs import date_utils
from libs import number_utils
from libs import string_utils
from libs import validator_utils
from libs import personnel_utils
from libs import nhi_utils
from libs import charge_utils
from libs import case_utils


# 候診名單 2018.01.31
class CheckErrors(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckErrors, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = int(args[2])
        self.apply_month = int(args[3])
        self.apply_type = args[4]
        self.ui = None
        self.doctor_list = personnel_utils.get_personnel(self.database, '醫師')

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHECK_ERRORS, self)
        self.center()
        self._set_table_widget()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def _set_table_widget(self):
        self.table_widget_errors = table_widget.TableWidget(self.ui.tableWidget_errors, self.database)
        self.table_widget_errors.set_column_hidden([0])
        width = [
            100, 120, 60, 80, 80, 120, 120, 100, 80, 100,
            80, 60, 60, 60, 60, 60, 60, 60, 280,
        ]
        self.table_widget_errors.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_errors.doubleClicked.connect(self.open_medical_record)
        self.ui.toolButton_calculate_ins_fee.clicked.connect(self._calculate_ins_fee)
        self.ui.toolButton_correct_error.clicked.connect(self._correct_errors)
        # self.ui.action_close.triggered.connect(self.close_app)

    def open_medical_record(self):
        case_key = self.table_widget_errors.field_value(0)
        self.parent.open_medical_record(case_key)

    def read_data(self):
        start_date = date_utils.get_start_date_by_year_month(
            self.apply_year, self.apply_month)
        end_date = date_utils.get_end_date_by_year_month(
            self.apply_year, self.apply_month)
        apply_type_sql = nhi_utils.get_apply_type_sql(self.apply_type)

        sql = '''
            SELECT 
                cases.*, patient.Birthday, patient.ID
            FROM cases 
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                (CaseDate BETWEEN "{start_date}" AND "{end_date}") AND
                (cases.InsType = "健保") AND
                (Card != "欠卡") AND
                ({apply_type_sql})
            ORDER BY CaseDate
        '''.format(
            start_date=start_date,
            end_date=end_date,
            apply_type_sql=apply_type_sql,
        )

        self.rows = self.database.select_record(sql)

    def row_count(self):
        return len(self.rows)

    def start_check(self):
        self.read_data()

        if self.row_count() <= 0:
            return

        progress_dialog = QtWidgets.QProgressDialog(
            '正在執行欄位錯誤檢查中, 請稍後...', '取消', 0, self.row_count(), self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        self.ui.tableWidget_errors.setRowCount(0)
        for row_no, row in zip(range(len(self.rows)), self.rows):
            error_messages = []
            error_messages += self._check_patient(row)
            error_messages += self._check_medical_record(row)
            error_messages += self._check_prescript(row)
            error_messages += self._check_charge(row)

            if len(error_messages) > 0:
                self._insert_error_record(row, error_messages)

            progress_dialog.setValue(row_no)

        progress_dialog.setValue(self.row_count())

        self.ui.tableWidget_errors.setAlternatingRowColors(True)

        if self.error_count() <= 0:
            self.ui.toolButton_calculate_ins_fee.setEnabled(False)
        else:
            self.ui.toolButton_calculate_ins_fee.setEnabled(True)

        self.ui.tableWidget_errors.resizeRowsToContents()

    def error_count(self):
        return self.ui.tableWidget_errors.rowCount()

    def _insert_error_record(self, row, error_messages):
        row_no = self.ui.tableWidget_errors.rowCount()
        self.ui.tableWidget_errors.setRowCount(row_no + 1)
        card = string_utils.xstr(row['Card']) \
            if string_utils.xstr(row['Continuance']) == '' \
            else string_utils.xstr(row['Card']) + '-' + string_utils.xstr(row['Continuance'])
        error_record = [
            string_utils.xstr(row['CaseKey']),
            '{0}-{1:0>2}-{2:0>2}'.format(
                row['CaseDate'].year, row['CaseDate'].month, row['CaseDate'].day
            ),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['ID']),
            string_utils.xstr(row['Share']),
            card,
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['DiagFee']),
            string_utils.xstr(row['InterDrugFee']),
            string_utils.xstr(row['PharmacyFee']),
            string_utils.xstr(
                number_utils.get_integer(row['AcupunctureFee']) +
                number_utils.get_integer(row['MassageFee']) +
                number_utils.get_integer(row['DislocateFee'])
            ),
            string_utils.xstr(row['DiagShareFee']),
            string_utils.xstr(row['DrugShareFee']),
            string_utils.xstr(row['InsApplyFee']),
            ', '.join(error_messages),
        ]
        for column_no in range(len(error_record)):
            self.ui.tableWidget_errors.setItem(
                row_no, column_no,
                QtWidgets.QTableWidgetItem(error_record[column_no])
            )
            if column_no in [3, 11, 12, 13, 14, 15, 16, 17]:
                self.ui.tableWidget_errors.item(
                    row_no, column_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
        color = QtGui.QColor('red')
        self.ui.tableWidget_errors.item(row_no, 18).setForeground(color)

    def _check_patient(self, row):
        error_messages = []

        if self._check_patient_error_exists(row['PatientKey']):
            return error_messages

        rows = self.database.select_record(
            'SELECT PatientKey FROM patient WHERE PatientKey = {0}'.format(row['PatientKey']))
        if len(rows) <= 0:
            error_messages.append('病患資料不存在')
            return error_messages

        if string_utils.xstr(row['Name']) == '':
            error_messages.append('姓名空白')
        try:
            if row['Birthday'] > row['CaseDate']:
                error_messages.append('生日不合理')
        except:
            if string_utils.xstr(row['Birthday']) == '':
                error_messages.append('生日空白')

        if string_utils.xstr(row['ID']) == '':
            error_messages.append('身分證空白')
        elif not validator_utils.verify_id(string_utils.xstr(row['ID'])):
            error_messages.append('身份證編碼錯誤')

        if string_utils.xstr(row['InsType']) == '':
            error_messages.append('保險類別空白')

        return error_messages

    def _check_patient_error_exists(self, patient_key):
        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            if self.ui.tableWidget_errors.item(row_no, 3).text() == string_utils.xstr(patient_key):
                return True

        return  False

    def _check_medical_record(self, row):
        error_messages = []

        if string_utils.xstr(row['Card']) == '':
            error_messages.append('卡序空白')

        if string_utils.xstr(row['Doctor']) == '':
            error_messages.append('無醫師')
        elif string_utils.xstr(row['Doctor']) not in self.doctor_list:
            error_messages.append('非醫師')

        if (string_utils.xstr(row['Treatment']) in nhi_utils.INS_TREAT and
                string_utils.xstr(row['TreatType']) in nhi_utils.INS_TREAT and
                number_utils.get_integer(row['Continuance']) < 1):
            error_messages.append('無療程序號')

        if (number_utils.get_integer(row['Continuance']) >= 1 and
                string_utils.xstr(row['Treatment']) not in nhi_utils.INS_TREAT):
            error_messages.append('療程內無處置')

        if string_utils.xstr(row['DiseaseCode1']) == '':
            error_messages.append('無主診斷碼')
        else:
            disease_code1 = string_utils.xstr(row['DiseaseCode1'])
            special_code = case_utils.get_disease_special_code(
                self.database, disease_code1,
            )
            if special_code != '' and string_utils.xstr(row['SpecialCode']).strip() == '':
                error_messages.append('{0}為慢性病但病歷無慢性病代碼'.format(disease_code1))

            for i in range(1, 4):
                disease_code = string_utils.xstr(row['DiseaseCode{0}'.format(i)])
                if disease_code != '' and disease_code[0] in [str(i) for i in range(10)]:
                    if i == 1:
                        disease_name = '主診斷碼'
                    else:
                        disease_name = '次診斷{0}'.format(i-1)

                    error_messages.append('{0}非ICD10碼'.format(disease_name))

        if string_utils.xstr(row['Treatment']) == '複雜針灸':
            complicated_acupuncture_list1 = nhi_utils.get_complicated_acupuncture_list(
                self.database, disease=1
            )
            disease_code1 = string_utils.xstr(row['DiseaseCode1'])
            if disease_code1 != '' and disease_code1 not in complicated_acupuncture_list1:
                error_messages.append('{0}非複雜性針灸適應症'.format(disease_code1))

        if string_utils.get_str(row['Symptom'], 'utf-8') == '':
            error_messages.append('無主訴')

        for i in range(1, 4):
            disease_code = string_utils.xstr(row['DiseaseCode{0}'.format(i)])
            if disease_code == '':
                continue

            if not case_utils.is_disease_code_neat(self.database, disease_code):
                error_messages.append('病名{0}非最細碼'.format(i))

        return error_messages

    def _check_prescript(self, row):
        error_messages = []

        case_key = row['CaseKey']
        sql = '''
            SELECT * FROM prescript
            WHERE
                CaseKey = {case_key} AND
                MedicineSet = 1
        '''.format(
            case_key=case_key,
        )

        prescript_rows = self.database.select_record(sql)
        pres_days = case_utils.get_pres_days(self.database, case_key)
        packages = case_utils.get_packages(self.database, case_key)
        instruction = case_utils.get_instruction(self.database, case_key)

        acupuncture_treat = 0
        massage_treat = 0

        total_ins_medicine = 0
        for prescript_row in prescript_rows:
            if string_utils.xstr(prescript_row['MedicineType']) == '穴道':
                acupuncture_treat += 1
            elif string_utils.xstr(prescript_row['MedicineType']) == '處置':
                massage_treat += 1

            if string_utils.xstr(prescript_row['InsCode']) != '':
                total_ins_medicine += 1

            if string_utils.xstr(prescript_row['MedicineType']) not in ['穴道', '處置']:
                if prescript_row['Dosage'] is None or string_utils.xstr(prescript_row['Dosage']) == '':
                    error_messages.append('{0}劑量空白'.format(
                        string_utils.xstr(prescript_row['MedicineName'])
                    ))
                if prescript_row['MedicineName'] is None or string_utils.xstr(prescript_row['MedicineName']) == '':
                    error_messages.append('處方名稱空白')

        if string_utils.xstr(row['Treatment']) in nhi_utils.ACUPUNCTURE_TREAT and acupuncture_treat <= 0:
            error_messages.append('針灸治療無穴位記錄')
        elif string_utils.xstr(row['Treatment']) in nhi_utils.MASSAGE_TREAT and massage_treat <= 0:
            error_messages.append('傷科治療無治療手法記錄')

        if pres_days > 0 and total_ins_medicine <= 0:
            error_messages.append('無健保碼藥品')

        if total_ins_medicine > 0:
            if pres_days < 3:
                error_messages.append('給藥天數不足3日')
            if packages < 2:
                error_messages.append('給藥包數不足2包')
            if instruction in [None, '']:
                error_messages.append('服藥方式空白')

        return error_messages

    def _check_charge(self, row):
        error_messages = []

        case_key = row['CaseKey']
        treat_type = string_utils.xstr(row['TreatType'])
        share = string_utils.xstr(row['Share'])
        course = number_utils.get_integer(row['Continuance'])
        pharmacy_type = string_utils.xstr(row['PharmacyType'])
        treatment = string_utils.xstr(row['Treatment'])

        diag_fee =  number_utils.get_integer(row['DiagFee'])
        inter_drug_fee =  number_utils.get_integer(row['InterDrugFee'])
        pharmacy_fee =  number_utils.get_integer(row['PharmacyFee'])
        acupuncture_fee =  number_utils.get_integer(row['AcupunctureFee'])
        massage_fee =  number_utils.get_integer(row['MassageFee'])
        dislocate_fee =  number_utils.get_integer(row['DislocateFee'])
        total_fee =  number_utils.get_integer(row['InsTotalFee'])
        apply_fee =  number_utils.get_integer(row['InsApplyFee'])
        agent_fee =  number_utils.get_integer(row['AgentFee'])
        diag_share_fee =  number_utils.get_integer(row['DiagShareFee'])
        drug_share_fee =  number_utils.get_integer(row['DrugShareFee'])

        pres_days = case_utils.get_pres_days(self.database, row['CaseKey'])
        ins_fee = charge_utils.get_ins_fee(
            self.database, self.system_settings, case_key,
            treat_type, share, course, pres_days, pharmacy_type, treatment
        )

        if diag_fee != ins_fee['diag_fee']:
            error_messages.append('診察費金額有誤')
        if inter_drug_fee != ins_fee['drug_fee']:
            error_messages.append('藥費有誤')
        if pharmacy_fee != ins_fee['pharmacy_fee']:
            error_messages.append('調劑費有誤')
        if acupuncture_fee != ins_fee['acupuncture_fee']:
            error_messages.append('針灸費有誤')
        if massage_fee != ins_fee['massage_fee']:
            error_messages.append('傷科費有誤')
        if dislocate_fee != ins_fee['dislocate_fee']:
            error_messages.append('脫臼費有誤')
        if diag_share_fee != ins_fee['diag_share_fee']:
            error_messages.append('門診負擔有誤')
        if drug_share_fee != ins_fee['drug_share_fee']:
            error_messages.append('藥品負擔有誤')
        if total_fee != ins_fee['ins_total_fee']:
            error_messages.append('合計金額有誤')
        if apply_fee != ins_fee['ins_apply_fee']:
            error_messages.append('申報金額有誤')
        if agent_fee != ins_fee['agent_fee']:
            error_messages.append('代辦費有誤')

        return error_messages

    # 重新批價
    def _calculate_ins_fee(self):
        self.ui.tableWidget_errors.setFocus(True)
        self.parent.ui.progressBar.setMaximum(self.ui.tableWidget_errors.rowCount()-1)
        self.parent.ui.progressBar.setValue(0)

        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            self.ui.tableWidget_errors.setCurrentCell(row_no, 0)
            case_key = self.ui.tableWidget_errors.item(row_no, 0).text()
            charge_utils.calculate_ins_fee(self.database, self.system_settings, case_key)

            self.parent.ui.progressBar.setValue(
                self.parent.ui.progressBar.value() + 1
            )

        self.parent._check_ins_data()

    def _correct_errors(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('自動更新錯誤')
        msg_box.setText(
            """
                <font size='4' color='red'><b>確定自動更正以下的錯誤?</b></font><br>
                1. 更正針灸傷科療程空白 (應為療程1)<br>
                2. 更正病名為慢性病但病歷無慢性病代碼<br>
            """
        )
        msg_box.setInformativeText("注意！ 其他錯誤請自行更正")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        correct_errors = msg_box.exec_()
        if not correct_errors:
            return

        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            self.ui.tableWidget_errors.setCurrentCell(row_no, 1)
            case_key = self.table_widget_errors.field_value(0)
            if case_key is None:
                continue

            sql = '''
                SELECT 
                    CaseKey, TreatType, Treatment, Continuance, DiseaseCode1, SpecialCode 
                FROM cases
                WHERE
                    CaseKey = {0}
            '''.format(case_key)
            rows = self.database.select_record(sql)
            if len(rows) <= 0:
                continue

            row = rows[0]

            fields = []
            data = []

            if (string_utils.xstr(row['Treatment']) in nhi_utils.INS_TREAT and
                    string_utils.xstr(row['TreatType']) in nhi_utils.INS_TREAT and
                    number_utils.get_integer(row['Continuance']) < 1):
                fields.append('Continuance')
                data.append(1)

            disease_code1 = string_utils.xstr(row['DiseaseCode1'])
            special_code = case_utils.get_disease_special_code(
                self.database, disease_code1,
            )
            if special_code != '' and string_utils.xstr(row['SpecialCode']).strip() == '':
                fields.append('SpecialCode')
                data.append(special_code)

            if len(fields) <= 0:
                continue

            self.database.update_record('cases', fields, 'CaseKey', case_key, data)

        self.start_check()
