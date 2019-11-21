#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets, QtCore
import os


# 系統設定 2018.03.19
class CheckDatabase(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckDatabase, self).__init__(parent)
        self.database = args[0]
        self.system_settings = args[1]
        self.parent = parent

        self._set_ui()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def _set_ui(self):
        self.center()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    # 檢查資料庫狀態
    def check_database(self):
        # self._create_table()
        self._alter_table()

    def _create_table(self):
        mysql_path = './mysql'
        mysql_files = [f for f in os.listdir(mysql_path) if os.path.isfile(os.path.join(mysql_path, f))]
        for file in mysql_files:
            table_name = file.split('.sql')[0]
            self.database.check_table_exists(table_name)

    def _alter_table(self):
        max_progress = 61
        self.progress = 0
        self.progress_dialog = QtWidgets.QProgressDialog(
            '正在檢查資料庫中, 請稍後...', '取消', 0, max_progress, self
        )
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)

        self._check_patient()
        self._check_cases()
        self._check_dosage()
        self._check_prescript()
        self._check_medicine()
        self._check_person()
        self._check_icd10()
        self._check_reserve()
        self._check_wait()
        self._check_deposit()
        self._check_debt()
        self._check_ins_apply()
        self._check_clinic()
        self._check_certificate()
        self._check_others()

        self.progress_dialog.deleteLater()

    def _exec_process(self, process_list):
        for _ in process_list:  # process execute here
            self.progress += 1
            self.progress_dialog.setValue(self.progress)

    def _check_patient(self):
        process_list = [
            self.database.check_field_exists('patient', 'add', 'Gender', 'varchar(4) AFTER Nationality'),
            self.database.check_field_exists('patient', 'add', 'FamilyPatientKey', 'varchar(10) AFTER PrivateInsurance'),
            self.database.check_field_exists('patient', 'add', 'Description', 'text AFTER History'),
            self.database.check_field_exists('patient', 'add', 'Allergy', 'text AFTER Alergy'),
            self.database.check_field_exists('patient', 'change', ['EMail', 'Email'], 'varchar(100)'),
            self.database.check_field_exists('patient', 'change', ['Name', 'Name'], 'varchar(100)'),
            self.database.check_field_exists('patient', 'change', ['RegistNo', 'ChartNo'], 'varchar(10)'),
        ]
        self._exec_process(process_list)

    def _check_cases(self):
        process_list = [
            self.database.check_field_exists('cases', 'change', ['Name', 'Name'], 'varchar(100)'),
            self.database.check_field_exists('cases', 'add', 'DoctorDate', 'datetime AFTER CaseDate'),
            self.database.check_field_exists('cases', 'add', 'PharmacyType', 'varchar(10) AFTER ApplyType'),
            self.database.check_field_exists('cases', 'add', 'TreatType', 'varchar(10) AFTER RegistType'),
            self.database.check_field_exists('cases', 'add', 'DebtFee', 'int AFTER Debt'),
            self.database.check_field_exists('cases', 'add', 'SDiagShareFee', 'int AFTER ReceiptShare'),
            self.database.check_field_exists('cases', 'add', 'DiagShareFee', 'int AFTER TreatShare'),
            self.database.check_field_exists('cases', 'add', 'DrugShareFee', 'int AFTER DrugShare'),
            self.database.check_field_exists('cases', 'add', 'Cashier', 'varchar(10) AFTER Casher'),
            self.database.check_field_exists('cases', 'add', 'RefundFee', 'int AFTER Refund'),
            self.database.check_field_exists('cases', 'add', 'SMaterialFee', 'int AFTER SMaterial'),
            self.database.check_field_exists('cases', 'add', 'TreatType', 'varchar(10) AFTER RegistType'),
            self.database.check_field_exists('cases', 'add', 'ChargePeriod', 'varchar(4) AFTER Period'),
            self.database.check_field_exists('cases', 'add', 'ChargeDate', 'datetime AFTER DoctorDate'),
            self.database.check_field_exists('cases', 'add', 'DiscountRate', 'int DEFAULT 100 AFTER DiscountFee'),
            self.database.check_field_exists('cases', 'add', 'TourArea', 'varchar(20) AFTER RegistType'),
            self.database.check_field_exists(
                'cases', 'add', 'DesignatedDoctor', 'ENUM("False", "True") NOT NULL AFTer DrugDone'
            ),  # 指定醫師
            self.database.check_field_exists(
                'cases', 'add', 'DesignatedDoctor', 'ENUM("False", "True") NOT NULL AFTer DrugDone'
            ),  # 指定醫師
            self.database.check_field_exists(
                'cases', 'add', 'DesignatedMassager', 'ENUM("False", "True") NOT NULL AFTer DesignatedDoctor'
            ),  # 指定醫師
        ]
        self._exec_process(process_list)

    def _check_dosage(self):
        process_list = [
            self.database.check_field_exists('dosage', 'add', 'SelfTotalFee', 'int AFTER Instruction'),
            self.database.check_field_exists('dosage', 'add', 'DiscountRate', 'int DEFAULT 100 AFTER SelfTotalFee'),
            self.database.check_field_exists('dosage', 'add', 'DiscountFee', 'int AFTER DiscountRate'),
            self.database.check_field_exists('dosage', 'add', 'TotalFee', 'int AFTER DiscountFee'),
        ]
        self._exec_process(process_list)

    def _check_prescript(self):
        process_list = [
            self.database.check_field_exists('prescript', 'add', 'PrescriptNo', 'int AFTER PrescriptKey'),
            self.database.check_field_exists('prescript', 'add', 'DosageMode', 'varchar(10) AFTER MedicineName'),
            self.database.check_field_exists('prescript', 'change', ['price', 'Price'], 'decimal(10,2)'),
            self.database.check_field_exists('prescript', 'change', ['amount', 'Amount'], 'decimal(10,2)'),
            self.database.check_field_exists('prescript', 'change', ['MedicineType', 'MedicineType'], 'varchar(10)'),
        ]
        self._exec_process(process_list)

    def _check_medicine(self):
        process_list = [
            self.database.check_field_exists('medicine', 'add', 'Dosage', 'decimal(10,2) AFTER Unit'),
            self.database.check_field_exists('medicine', 'add', 'Charged', 'varchar(4) AFTER InPrice'),
            self.database.check_field_exists('medicine', 'add', 'HitRate', 'int DEFAULT 0 AFTER Description'),
            self.database.check_field_exists('medicine', 'add', 'Commission', 'varchar(10) AFTER InPrice'),
            self.database.check_field_exists('medicine', 'add', 'Project', 'varchar(50) AFTER Commission'),
            self.database.check_field_exists('medicine', 'add', 'DoctorProject', 'varchar(50) AFTER Project'),
            self.database.check_field_exists('medicine', 'change', ['location', 'Location'], 'varchar(20)'),
            self.database.check_field_exists('medicine', 'change', ['MedicineType', 'MedicineType'], 'varchar(10)'),
            self.database.check_field_exists('drug', 'change', ['Supplier', 'Supplier'], 'varchar(50)'),
            self.database.check_field_exists('drug', 'add', 'MedicineType', 'varchar(10) AFTER DrugName'),
        ]
        self._exec_process(process_list)

    def _check_person(self):
        process_list = [
            self.database.check_field_exists('person', 'change', ['Name', 'Name'], 'varchar(100)'),
            self.database.check_field_exists('person', 'add', 'Birthday', 'date AFTER Name'),
            self.database.check_field_exists('person', 'add', 'Gender', 'varchar(2) AFTER ID'),
            self.database.check_field_exists('person', 'add', 'Email', 'varchar(100) AFTER Address'),
            self.database.check_field_exists('person', 'add', 'FullTime', 'varchar(10) AFTER Position'),
            self.database.check_field_exists('person', 'add', 'Department', 'varchar(20) AFTER Email'),
            self.database.check_field_exists('person', 'add', 'InputDate', 'date AFTER Department'),
            self.database.check_field_exists('person', 'add', 'CertCardNo', 'varchar(50) AFTER Certificate'),
            self.database.check_field_exists('person', 'change', ['EMail', 'Email'], 'varchar(100)'),
        ]
        self._exec_process(process_list)

    def _check_icd10(self):
        process_list = [
            self.database.check_field_exists('icd10', 'add', 'Groups', 'varchar(100) AFTER SpecialCode'),
            self.database.check_field_exists('icd10', 'add', 'HitRate', 'int DEFAULT 0 AFTER Groups'),
        ]
        self._exec_process(process_list)

    def _check_reserve(self):
        process_list = [
            self.database.check_field_exists('reserve', 'change', ['Name', 'Name'], 'varchar(100)'),
            self.database.check_field_exists('reserve', 'add', 'ReserveNo', 'int AFTER Sequence'),
            self.database.check_field_exists('reserve', 'add', 'Source', 'varchar(10) AFTER Doctor'),
            self.database.check_field_exists('reserve', 'add', 'Arrival', 'enum("False", "True") not null AFTER Doctor'),
            self.database.check_field_exists('reservation_table', 'add', 'Doctor', 'varchar(10) AFTER Period'),
        ]
        self._exec_process(process_list)

    def _check_wait(self):
        process_list = [
            self.database.check_field_exists('wait', 'change', ['Name', 'Name'], 'varchar(100)'),
            self.database.check_field_exists('wait', 'add', 'TreatType', 'varchar(10) AFTER RegistType'),
            self.database.check_field_exists('wait', 'change', ['Remark', 'Remark'], 'varchar(100)'),
            self.database.check_field_exists('wait', 'add', 'InProgress', 'varchar(10) AFTER Doctor'),
        ]
        self._exec_process(process_list)

    def _check_deposit(self):
        process_list = [
            self.database.check_field_exists('deposit', 'change', ['Name', 'Name'], 'varchar(100)'),
        ]
        self._exec_process(process_list)

    def _check_debt(self):
        process_list = [
            self.database.check_field_exists('debt', 'change', ['Name', 'Name'], 'varchar(100)'),
            self.database.check_field_exists('debt', 'add', 'DebtType', 'varchar(10) AFTER PatientKey'),
            self.database.check_field_exists('debt', 'add', 'Cashier1', 'varchar(10) AFTER Casher1'),
            self.database.check_field_exists('debt', 'add', 'Cashier2', 'varchar(10) AFTER Casher2'),
            self.database.check_field_exists('debt', 'add', 'Cashier3', 'varchar(10) AFTER Casher3'),
        ]
        self._exec_process(process_list)

    def _check_ins_apply(self):
        process_list = [
            self.database.check_field_exists('insapply', 'change', ['Name', 'Name'], 'varchar(100)'),
            self.database.check_field_exists('insapply', 'add', 'Visit', 'varchar(10) AFTER ShareCode'),
            self.database.check_field_exists('insapply', 'change', ['Card', 'Card'], 'varchar(5)'),
        ]
        self._exec_process(process_list)

    def _check_clinic(self):
        process_list = [
            self.database.check_field_exists('clinic', 'change', ['groups', 'Groups'], 'varchar(40)'),
            self.database.check_field_exists('clinic', 'change', ['position', 'Position'], 'varchar(40)'),
            self.database.check_field_exists('clinic', 'add', 'HitRate', 'int DEFAULT 0 AFTER ClinicName'),
        ]
        self._exec_process(process_list)

    def _check_certificate(self):
        process_list = [
            self.database.check_field_exists('certificate', 'add', 'Doctor', 'varchar(20) AFTER Name'),
            self.database.check_field_exists('certificate', 'add', 'TreatType', 'varchar(20) AFTER InsType'),
        ]
        self._exec_process(process_list)

    def _check_others(self):
        process_list = [
            self.database.check_field_exists('dict_groups', 'add', 'DictOrderNo', 'varchar(10) AFTER DictGroupsKey'),
            self.database.check_field_exists('person', 'add', 'Title', 'varchar(20) AFTER Code'),
            self.database.check_field_exists('reservation_table', 'add', 'Weekday', 'varchar(10) AFTER Period'),
            self.database.check_field_exists('hospid', 'change', ['HospName', 'HospName'], 'varchar(100)'),
            self.database.check_field_exists('hospid', 'change', ['Telephone', 'Telephone'], 'varchar(50)'),
            self.database.check_field_exists('hospid', 'change', ['Address', 'Address'], 'varchar(100)'),
            self.database.check_field_exists('reserve', 'add', 'Registrar', 'varchar(10) AFTER Source'),
            self.database.check_field_exists('off_day_list', 'add', 'Doctor', 'varchar(20) AFTER Period'),
        ]
        self._exec_process(process_list)


