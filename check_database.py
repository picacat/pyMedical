#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets
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
        self.database.check_field_exists('icd10', 'add', 'Groups', 'varchar(100) AFTER SpecialCode')

        self.database.check_field_exists('patient', 'add', 'Gender', 'varchar(4) AFTER Nationality')
        self.database.check_field_exists('patient', 'add', 'FamilyPatientKey', 'varchar(10) AFTER PrivateInsurance')
        self.database.check_field_exists('patient', 'add', 'Description', 'text AFTER History')
        self.database.check_field_exists('patient', 'add', 'Allergy', 'text AFTER Alergy')

        self.database.check_field_exists('cases', 'add', 'CompletionTime', 'datetime AFTER CaseDate')
        self.database.check_field_exists('cases', 'add', 'PharmacyType', 'varchar(10) AFTER ApplyType')
        self.database.check_field_exists('cases', 'add', 'TreatType', 'varchar(10) AFTER RegistType')
        self.database.check_field_exists('cases', 'add', 'DebtFee', 'int AFTER Debt')
        self.database.check_field_exists('cases', 'add', 'SDiagShareFee', 'int AFTER ReceiptShare')
        self.database.check_field_exists('cases', 'add', 'DiagShareFee', 'int AFTER TreatShare')
        self.database.check_field_exists('cases', 'add', 'DrugShareFee', 'int AFTER DrugShare')
        self.database.check_field_exists('cases', 'add', 'Cashier', 'varchar(10) AFTER Casher')
        self.database.check_field_exists('cases', 'add', 'RefundFee', 'int AFTER Refund')
        self.database.check_field_exists('cases', 'add', 'SMaterialFee', 'int AFTER SMaterial')
        self.database.check_field_exists('cases', 'add', 'TreatType', 'varchar(10) AFTER RegistType')

        self.database.check_field_exists('prescript', 'add', 'PrescriptNo', 'int AFTER PrescriptKey')
        self.database.check_field_exists('prescript', 'add', 'DosageMode', 'varchar(10) AFTER MedicineName')

        self.database.check_field_exists('medicine', 'add', 'Dosage', 'decimal(10,2) AFTER Unit')
        self.database.check_field_exists('medicine', 'add', 'Charged', 'varchar(4) AFTER InPrice')

        self.database.check_field_exists('reserve', 'add', 'ReserveNo', 'int AFTER Sequence')
        self.database.check_field_exists('reserve', 'add', 'Arrival', 'enum("False", "True") not null AFTER Doctor')

        self.database.check_field_exists('wait', 'add', 'TreatType', 'varchar(10) AFTER RegistType')

        self.database.check_field_exists('person', 'add', 'Birthday', 'date AFTER Name')
        self.database.check_field_exists('person', 'add', 'Gender', 'varchar(2) AFTER ID')
        self.database.check_field_exists('person', 'add', 'Email', 'varchar(100) AFTER Address')
        self.database.check_field_exists('person', 'add', 'FullTime', 'varchar(10) AFTER Position')
        self.database.check_field_exists('person', 'add', 'Department', 'varchar(20) AFTER Email')
        self.database.check_field_exists('person', 'add', 'InputDate', 'date AFTER Department')

        self.database.check_field_exists('debt', 'add', 'Cashier1', 'varchar(10) AFTER Casher1')
        self.database.check_field_exists('debt', 'add', 'Cashier2', 'varchar(10) AFTER Casher2')
        self.database.check_field_exists('debt', 'add', 'Cashier3', 'varchar(10) AFTER Casher3')

        self.database.check_field_exists('insapply', 'add', 'Visit', 'varchar(10) AFTER ShareCode')

        self.database.check_field_exists('patient', 'change', ['EMail', 'Email'], 'varchar(100)')
        self.database.check_field_exists('person', 'change', ['EMail', 'Email'], 'varchar(100)')
        self.database.check_field_exists('prescript', 'change', ['price', 'Price'], 'decimal(10,2)')
        self.database.check_field_exists('prescript', 'change', ['amount', 'Amount'], 'decimal(10,2)')


