#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from classes import udp_socket_client
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import date_utils
from libs import cshis_utils
from libs import nhi_utils
from libs import case_utils
from libs import system_utils
import ins_prescript_record
import self_prescript_record
import medical_record_recently_history
import medical_record_fees
import medical_record_registration
from dialog import dialog_inquiry
from dialog import dialog_diagnosis
from dialog import dialog_disease
from dialog import dialog_medicine
from dialog import dialog_medical_record_past_history


# 病歷資料 2018.01.31
class MedicalRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MedicalRecord, self).__init__(parent)
        self.parent = parent
        self.database = args[0][0]
        self.system_settings = args[0][1]
        self.case_key = args[0][2]
        self.call_from = args[0][3]
        self.medical_record = None
        self.patient_data = None
        self.record_saved = False
        self.first_record = None
        self.last_record = None
        self.ui = None
        self._init_tab()

        if not self._read_data():
            return

        self._set_ui()
        self._set_signal()
        self._set_data()
        self._read_prescript()

        if self.call_from == '醫師看診作業':
            self._read_recently_history()
            self._read_fees()
        else:
            self._read_fees()
            self._read_recently_history()

    def _init_tab(self):
        self.tab_ins_prescript = None
        self.tab_self_prescript1 = None
        self.tab_self_prescript2 = None
        self.tab_self_prescript3 = None
        self.tab_self_prescript4 = None
        self.tab_self_prescript5 = None
        self.tab_self_prescript6 = None
        self.tab_self_prescript7 = None
        self.tab_self_prescript8 = None
        self.tab_self_prescript9 = None
        self.tab_self_prescript10 = None
        self.tab_list = [
            self.tab_ins_prescript,
            self.tab_self_prescript1,
            self.tab_self_prescript2,
            self.tab_self_prescript3,
            self.tab_self_prescript4,
            self.tab_self_prescript5,
            self.tab_self_prescript6,
            self.tab_self_prescript7,
            self.tab_self_prescript8,
            self.tab_self_prescript9,
            self.tab_self_prescript10,
        ]
        self.max_tab = len(self.tab_list)

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MEDICAL_RECORD, self)

        self.add_tab_button = QtWidgets.QToolButton()
        self.add_tab_button.setIcon(QtGui.QIcon('./icons/document-new.svg'))
        self.ui.tabWidget_prescript.setCornerWidget(self.add_tab_button, QtCore.Qt.TopLeftCorner)
        self.ui.tabWidget_prescript.tabCloseRequested.connect(self.close_prescript_tab)
        self.tab_registration = medical_record_registration.MedicalRecordRegistration(
            self, self.database, self.system_settings, self.case_key, self.call_from)
        self.ui.tabWidget_medical.addTab(self.tab_registration, '門診資料')
        self.disease_code_changed()

    # 設定信號
    def _set_signal(self):
        self.ui.action_past_history.triggered.connect(self._open_past_history)
        self.ui.action_save.triggered.connect(self.save_medical_record)
        self.ui.action_dictionary.triggered.connect(self.open_dictionary)
        self.ui.action_close.triggered.connect(self.close_medical_record)
        self.ui.action_patient.triggered.connect(self.modify_patient)

        self.ui.lineEdit_disease_code1.textChanged.connect(self.disease_code_changed)
        self.ui.lineEdit_disease_code1.returnPressed.connect(self.disease_code_return_pressed)
        self.ui.lineEdit_disease_code1.editingFinished.connect(self.disease_code_editing_finished)

        self.ui.lineEdit_disease_code2.textChanged.connect(self.disease_code_changed)
        self.ui.lineEdit_disease_code2.editingFinished.connect(self.disease_code_editing_finished)
        self.ui.lineEdit_disease_code2.returnPressed.connect(self.disease_code_return_pressed)

        self.ui.lineEdit_disease_code3.textChanged.connect(self.disease_code_changed)
        self.ui.lineEdit_disease_code3.returnPressed.connect(self.disease_code_return_pressed)
        self.ui.lineEdit_disease_code3.editingFinished.connect(self.disease_code_editing_finished)
        self.add_tab_button.clicked.connect(self.add_prescript_tab)

    def close_prescript_tab(self, current_index):
        current_tab = self.ui.tabWidget_prescript.widget(current_index)
        tab_name = self.ui.tabWidget_prescript.tabText(current_index)
        if tab_name == '健保':
            return

        current_tab.close_all()
        current_tab.deleteLater()

    def close_medical_record(self):
        self.close_all()
        self.close_tab()

    def modify_patient(self):
        patient_key = self.patient_data['PatientKey']
        self.parent.open_patient_record(patient_key, '門診掛號')

    def disease_code_return_pressed(self):
        pass

    def disease_code_editing_finished(self):
        disease_list = [
            [self.ui.lineEdit_disease_code1, self.ui.lineEdit_disease_name1],
            [self.ui.lineEdit_disease_code2, self.ui.lineEdit_disease_name2],
            [self.ui.lineEdit_disease_code3, self.ui.lineEdit_disease_name3],
        ]

        for i in range(len(disease_list)):
            if disease_list[i][1].text() == '':
                disease_list[i][0].setText('')

    # 設定診斷碼輸入狀態
    def disease_code_changed(self):
        disease_list = [
            [self.ui.lineEdit_disease_code1, self.ui.lineEdit_disease_name1],
            [self.ui.lineEdit_disease_code2, self.ui.lineEdit_disease_name2],
            [self.ui.lineEdit_disease_code3, self.ui.lineEdit_disease_name3],
        ]

        for row_no in reversed(range(len(disease_list))):
            icd_code = str(disease_list[row_no][0].text()).strip()
            if icd_code == '':
                disease_list[row_no][1].setText(None)
                if row_no > 0:
                    if disease_list[row_no-1][0].text() == '':
                        disease_list[row_no][0].setEnabled(False)
                    else:
                        disease_list[row_no][0].setEnabled(True)

            for i in range(len(disease_list)):
                if i == len(disease_list) - 1:
                    break

                if disease_list[i][0].text() == '' and disease_list[i+1][0].text() != '':
                    disease_list[i][0].setText(disease_list[i+1][0].text())
                    disease_list[i][1].setText(disease_list[i+1][1].text())
                    disease_list[i+1][0].setText(None)

    def _read_data(self):
        read_success = True

        try:
            sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(self.case_key)
            self.medical_record = self.database.select_record(sql)[0]
        except IndexError:
            system_utils.show_message_box(
                QtWidgets.QMessageBox.Critical,
                '資料遺失',
                '<font size="4" color="red"><b>找不到病歷資料, 請重新掛號.</b></font>',
                '資料不明原因遺失.'
            )
            read_success = False
        try:
            sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(self.medical_record['PatientKey'])
            self.patient_data = self.database.select_record(sql)[0]
        except IndexError:
            system_utils.show_message_box(
                QtWidgets.QMessageBox.Critical,
                '資料遺失',
                '<font size="4" color="red"><b>找不到病患資料, 請新掛號.</b></font>',
                '資料不明原因遺失.'
            )
            read_success = False

        return read_success

    def _set_data(self):
        self._set_patient_data()
        self._set_medical_record()

    def _set_patient_data(self):
        name = self.patient_data['Name']
        age_year, age_month = date_utils.get_age(
            self.patient_data['Birthday'], self.medical_record['CaseDate'])
        if age_year is None:
            age = ''
        else:
            age = '{0}歲'.format(age_year)

        gender = self.patient_data['Gender']
        if gender in ['男', '女']:
            gender = '({0})'.format(gender)
        else:
            gender = ''

        name += ' {0} {1}'.format(gender, age)

        card = string_utils.xstr(self.medical_record['Card'])
        if number_utils.get_integer(self.medical_record['Continuance']) >= 1:
            card += '-' + string_utils.xstr(self.medical_record['Continuance'])

        self.ui.label_case_date.setText(string_utils.xstr(self.medical_record['CaseDate']))
        self.ui.label_ins_type.setText(string_utils.xstr(self.medical_record['InsType']))
        self.ui.label_patient_name.setText(string_utils.xstr(name))
        self.ui.label_regist_no.setText(string_utils.xstr(self.medical_record['RegistNo']))
        self.ui.label_share_type.setText(string_utils.xstr(self.medical_record['Share']))
        self.ui.label_card.setText(string_utils.xstr(card))

    # 顯示病歷
    def _set_medical_record(self):
        self.ui.textEdit_symptom.setText(string_utils.get_str(self.medical_record['Symptom'], 'utf8'))
        self.ui.textEdit_tongue.setText(string_utils.get_str(self.medical_record['Tongue'], 'utf8'))
        self.ui.textEdit_pulse.setText(string_utils.get_str(self.medical_record['Pulse'], 'utf8'))
        self.ui.textEdit_remark.setText(string_utils.get_str(self.medical_record['Remark'], 'utf8'))
        self.ui.lineEdit_disease_code1.setText(string_utils.get_str(self.medical_record['DiseaseCode1'], 'utf8'))
        self.ui.lineEdit_disease_name1.setText(string_utils.get_str(self.medical_record['DiseaseName1'], 'utf8'))
        self.ui.lineEdit_disease_code2.setText(string_utils.get_str(self.medical_record['DiseaseCode2'], 'utf8'))
        self.ui.lineEdit_disease_name2.setText(string_utils.get_str(self.medical_record['DiseaseName2'], 'utf8'))
        self.ui.lineEdit_disease_code3.setText(string_utils.get_str(self.medical_record['DiseaseCode3'], 'utf8'))
        self.ui.lineEdit_disease_name3.setText(string_utils.get_str(self.medical_record['DiseaseName3'], 'utf8'))
        self.ui.lineEdit_distinguish.setText(string_utils.get_str(self.medical_record['Distincts'], 'utf8'))
        self.ui.lineEdit_cure.setText(string_utils.get_str(self.medical_record['Cure'], 'utf8'))

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def record_modified(self):
        modified = False
        if self.ui.textEdit_symptom.document().isModified() or \
                self.ui.textEdit_tongue.document().isModified() or \
                self.ui.textEdit_pulse.document().isModified() or \
                self.ui.textEdit_remark.document().isModified() or \
                self.ui.lineEdit_disease_code1.isModified() or \
                self.ui.lineEdit_disease_code2.isModified() or \
                self.ui.lineEdit_disease_code3.isModified() or \
                self.ui.lineEdit_distinguish.isModified() or \
                self.ui.lineEdit_cure.isModified():
            modified = True

        return modified

    def open_dictionary(self):
        dialog_type = None
        if self.ui.textEdit_symptom.hasFocus():
            dialog_type = '主訴'
        elif self.ui.textEdit_tongue.hasFocus():
            dialog_type = '舌診'
        elif self.ui.textEdit_pulse.hasFocus():
            dialog_type = '脈象'
        elif self.ui.textEdit_remark.hasFocus():
            dialog_type = '備註'
        elif self.ui.lineEdit_distinguish.hasFocus():
            dialog_type = '辨證'
        elif self.ui.lineEdit_cure.hasFocus():
            dialog_type = '治則'
        elif self.ui.lineEdit_disease_code1.hasFocus():
            dialog_type = '病名1'
        elif self.ui.lineEdit_disease_code2.hasFocus():
            dialog_type = '病名2'
        elif self.ui.lineEdit_disease_code3.hasFocus():
            dialog_type = '病名3'
        elif self.tab_list[0].ui.tableWidget_prescript.hasFocus():
            dialog_type = '健保處方'

        if dialog_type is None:
            return

        text_edit = {
            '主訴': self.ui.textEdit_symptom,
            '舌診': self.ui.textEdit_tongue,
            '脈象': self.ui.textEdit_pulse,
            '備註': self.ui.textEdit_remark,
            '辨證': self.ui.lineEdit_distinguish,
            '治則': self.ui.lineEdit_cure,
            '病名1': self.ui.lineEdit_disease_code1,
            '病名2': self.ui.lineEdit_disease_code2,
            '病名3': self.ui.lineEdit_disease_code3,
        }
        dialog = None
        if dialog_type in ['主訴', '舌診', '脈象', '備註']:
            dialog = dialog_inquiry.DialogInquiry(
                self, self.database, self.system_settings, dialog_type, text_edit[dialog_type])
        elif dialog_type in ['辨證', '治則']:
            dialog = dialog_diagnosis.DialogDiagnosis(
                self, self.database, self.system_settings, dialog_type, text_edit[dialog_type])
        elif dialog_type in ['病名1', '病名2', '病名3']:
            line_edit = self.ui.lineEdit_disease_name1

            if dialog_type == '病名1':
                line_edit = self.ui.lineEdit_disease_name1
            elif dialog_type == '病名2':
                line_edit = self.ui.lineEdit_disease_name2
            elif dialog_type == '病名3':
                line_edit = self.ui.lineEdit_disease_name3

            dialog = dialog_disease.DialogDisease(
                self, self.database, self.system_settings, text_edit[dialog_type], line_edit)
        elif dialog_type in ['健保處方']:
            medicine_set = '1'
            dialog = dialog_medicine.DialogMedicine(
                self, self.database, self.system_settings,
                self.tab_list[0].tableWidget_prescript, medicine_set)

        if dialog is None:
            return

        dialog.exec_()
        dialog.deleteLater()

    def _read_prescript(self):
        if self.medical_record['InsType'] == '健保':  # 健保無論如何一定要開啟
            self.add_prescript_tab(1)

        # 讀取自費資料
        sql = '''
            SELECT MedicineSet FROM prescript WHERE
            CaseKey = {0} AND MedicineSet >= 2
            GROUP BY MedicineSet ORDER BY MedicineSet
        '''.format(self.case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        for row in rows:
                self.add_prescript_tab(row['MedicineSet'])

    def _get_new_tab(self, max_medicine_set):
        tab_name = None
        medicine_set = 2
        for i in range(2, max_medicine_set + 1):  # MedicineSet2 ~ MedicineSet7  最多六帖藥
            tab_name = '自費{0}'.format(medicine_set-1)
            if self._tab_exists(tab_name):
                medicine_set += 1
                if medicine_set > max_medicine_set:
                    return False, None
                else:
                    continue
            else:
                break

        return tab_name, medicine_set

    # 新增自費處方
    def add_prescript_tab(self, medicine_set=None):
        if medicine_set == 1:  # 健保處方頁
            self.tab_list[0] = ins_prescript_record.InsPrescriptRecord(
                self, self.database, self.system_settings, self.case_key, 1)
            self.ui.tabWidget_prescript.addTab(self.tab_list[medicine_set-1], '健保')
            return

        set_current_tab = False

        if not medicine_set:  # 新增自費處方按鈕
            medicine_set = 2
            set_current_tab = True

        tab_name = '自費{0}'.format(medicine_set-1)
        if self._tab_exists(tab_name):
            tab_name, medicine_set = self._get_new_tab(self.max_tab)

        if not tab_name:
            return

        current_tab = None
        new_tab = self_prescript_record.SelfPrescriptRecord(
            self, self.database, self.system_settings, self.case_key, medicine_set)

        for i in range(1, self.max_tab):
            if tab_name == '自費{0}'.format(i):
                self.tab_list[i] = new_tab
                current_tab = self.tab_list[i]

        if current_tab is None:
            return

        self.ui.tabWidget_prescript.addTab(current_tab, tab_name)
        if set_current_tab:
            self.ui.tabWidget_prescript.setCurrentWidget(current_tab)

    # 檢查是否開啟tab
    def _tab_exists(self, tab_text):
        if self.ui.tabWidget_prescript.count() <= 0:
            return False

        for i in range(self.ui.tabWidget_prescript.count()):
            if self.ui.tabWidget_prescript.tabText(i) == tab_text:
                return True

        return False

    def _read_recently_history(self):
        self.tab_medical_record_recently_history = \
            medical_record_recently_history.MedicalRecordRecentlyHistory(
                self, self.database, self.system_settings, self.case_key, self.call_from)
        self.ui.tabWidget_past_record.addTab(self.tab_medical_record_recently_history, '最近病歷')

    def _read_fees(self):
        self.tab_medical_record_fees = medical_record_fees.MedicalRecordFees(
            self, self.database, self.system_settings, self.case_key, self.call_from)
        self.ui.tabWidget_past_record.addTab(self.tab_medical_record_fees, '批價明細')

    # 病歷存檔
    def save_medical_record(self):
        self.record_saved = True
        self._set_necessary_fields()

        doctor_done = False
        if self.call_from == '醫師看診作業':
            doctor_done = True

        self.update_medical_record(doctor_done)

        card = string_utils.xstr(self.medical_record['Card'])
        if ((self.medical_record['InsType'] == '健保') and
                (self.call_from == '醫師看診作業') and
                (self.system_settings.field('產生醫令簽章位置') == '診療') and
                (self.system_settings.field('使用讀卡機') == 'Y') and
                (card not in nhi_utils.ABNORMAL_CARD) and
                (card != '欠卡')):
            self._write_ic_treatments(cshis_utils.NORMAL_CARD)
            self._write_prescript_signature()
            self._update_prescript_sign_time()

        self.close_all()
        self.close_tab()

    # 設定必要欄位
    def _set_necessary_fields(self):
        if (self.medical_record['InsType'] != '健保'):
            return

        if (self.call_from != '醫師看診作業'):
            return

        self._set_doctor()
        self._set_treatment_and_course()

    # 設定主治醫師姓名
    def _set_doctor(self):
        self.tab_registration.ui.comboBox_doctor.setCurrentText(self.system_settings.field('使用者'))

    # 設定就醫類別及療程
    def _set_treatment_and_course(self):
        treatment = string_utils.xstr(self.tab_list[0].combo_box_treatment.currentText())
        course = number_utils.get_integer(self.tab_registration.ui.comboBox_course.currentText())
        if treatment in nhi_utils.INS_TREAT:
            self.tab_registration.ui.comboBox_treat_type.setCurrentText(treatment)
            if course <= 0:
                self.tab_registration.ui.comboBox_course.setCurrentText('1')
        elif treatment == '':
            self.tab_registration.ui.comboBox_treat_type.setCurrentText('內科')
            if course >= 1:
                self.tab_registration.ui.comboBox_course.setCurrentText(None)

    # 寫入病名, 費用
    def _write_ic_treatments(self, treat_after_check):
        cshis_utils.write_ic_treatment(
            self.database, self.system_settings, self.case_key, treat_after_check)

    # 寫入醫令簽章
    def _write_prescript_signature(self):
        cshis_utils.write_prescript_signature(
            self.database, self.system_settings, self.case_key)

    # 病歷存檔
    def update_medical_record(self, doctor_done=False):
        self.update_diagnosis_data()
        self.update_treat_data()
        self.update_ins_fees_data()
        self.update_cash_fees_data()
        self.tab_registration.save_record()
        self.save_prescript()

        if doctor_done:
            self._set_doctor_done()
            self._set_wait_done()
            socket_client = udp_socket_client.UDPSocketClient()
            socket_client.send_data('醫師看診作業完成')

    def _set_doctor_done(self):
        self.database.exec_sql(
            'UPDATE cases SET DoctorDone = "True", CompletionTime = "{0}" WHERE CaseKey = {1}'.format(
                date_utils.now_to_str(), self.case_key))

    def _set_wait_done(self):
        self.database.exec_sql(
            'UPDATE wait SET DoctorDone = "True" WHERE CaseKey = {0}'.format(self.case_key))

    # 診斷資料存檔
    def update_diagnosis_data(self):
        fields = [
            'Symptom', 'Tongue', 'Pulse', 'Remark',
            'DiseaseCode1', 'DiseaseCode2', 'DiseaseCode3',
            'DiseaseName1', 'DiseaseName2', 'DiseaseName3',
            'Distincts', 'Cure',
            'Treatment',
        ]

        treatment = None
        if self.medical_record['InsType'] == '健保':
            treatment = string_utils.xstr(self.tab_list[0].combo_box_treatment.currentText())

        data = [
            self.ui.textEdit_symptom.toPlainText(),
            self.ui.textEdit_tongue.toPlainText(),
            self.ui.textEdit_pulse.toPlainText(),
            self.ui.textEdit_remark.toPlainText(),
            self.ui.lineEdit_disease_code1.text(),
            self.ui.lineEdit_disease_code2.text(),
            self.ui.lineEdit_disease_code3.text(),
            self.ui.lineEdit_disease_name1.text(),
            self.ui.lineEdit_disease_name2.text(),
            self.ui.lineEdit_disease_name3.text(),
            self.ui.lineEdit_distinguish.text(),
            self.ui.lineEdit_cure.text(),
            treatment,
        ]

        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

    # 處置資料存檔
    def update_treat_data(self):
        fields = [
            'Package1', 'PresDays1', 'Instruction1',
            'Treatment',
        ]

        package1, pres_days1, instruction1 = None, None, None
        treatment = None
        if self.medical_record['InsType'] == '健保':
            package1 = string_utils.xstr(self.tab_list[0].ui.comboBox_package.currentText())
            pres_days1 = string_utils.xstr(self.tab_list[0].ui.comboBox_pres_days.currentText())
            instruction1 = string_utils.xstr(self.tab_list[0].ui.comboBox_instruction.currentText())
            treatment = string_utils.xstr(self.tab_list[0].combo_box_treatment.currentText())

        data = [
            package1, pres_days1, instruction1,
            treatment,
        ]

        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

    # 健保批價資料存檔
    def update_ins_fees_data(self):
        fields = [
            'DiagFee', 'InterDrugFee', 'PharmacyFee',
            'AcupunctureFee', 'MassageFee', 'DislocateFee', 'ExamFee',
            'InsTotalFee', 'DiagShareFee', 'DrugShareFee', 'InsApplyFee', 'AgentFee',
        ]

        self.calculate_ins_fees()
        data = [
            self.tab_medical_record_fees.ui.tableWidget_ins_fees.item(i, 0).text()
            for i in range(len(fields))
        ]

        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

    # 自費批價資料存檔
    def update_cash_fees_data(self):
        fields = [
            'RegistFee', 'SDiagShareFee', 'SDrugShareFee', 'DepositFee', 'RefundFee',
            'SDiagFee', 'SDrugFee', 'SHerbFee', 'SExpensiveFee',
            'SAcupunctureFee', 'SMassageFee', 'SMaterialFee',
            'SelfTotalFee', 'DiscountFee', 'TotalFee', 'ReceiptFee',
        ]

        data = [
            self.tab_medical_record_fees.ui.tableWidget_cash_fees.item(i, 0).text()
            for i in range(len(fields))
        ]

        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

    # 更新健保寫卡資料
    def _update_prescript_sign_time(self):
        case_utils.update_xml(
            self.database, 'cases', 'Security', 'prescript_sign_time',
            date_utils.now_to_str(), 'CaseKey', self.case_key
        )

    def save_prescript(self):
        for medicine_set, tab_prescript in zip(range(1, self.max_tab+1), self.tab_list):
            if tab_prescript is not None:
                try:
                    tab_prescript.save_prescript()
                except RuntimeError:  # 關閉處方頁, 刪除整個處方
                    self.remove_prescript(medicine_set)
            else:
                self.remove_prescript(medicine_set)

    def remove_prescript(self, medicine_set):
        sql = '''
            DELETE FROM prescript WHERE 
            (CaseKey = {0}) AND (MedicineSet = {1})
        '''.format(self.case_key, medicine_set)
        self.database.exec_sql(sql)
        sql = '''
            DELETE FROM dosage WHERE 
            (CaseKey = {0}) AND (MedicineSet = {1})
        '''.format(self.case_key, medicine_set)
        self.database.exec_sql(sql)

    # 健保重新批價
    def calculate_ins_fees(self):
        try:
            self.tab_medical_record_fees.calculate_ins_fees()
        except AttributeError:
            pass

    # 顯示拷貝過去病歷視窗
    def _open_past_history(self):
        patient_key = self.patient_data['PatientKey']
        dialog = dialog_medical_record_past_history.DialogMedicalRecordPastHistory(
            self, self.database, self.system_settings,
            patient_key,
        )

        dialog.exec_()
        dialog.deleteLater()

