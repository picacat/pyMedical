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
        max_progress = 38
        progress = 0
        progress_dialog = QtWidgets.QProgressDialog(
            '正在檢查資料庫中, 請稍後...', '取消', 0, max_progress, self
        )

        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('icd10', 'add', 'Groups', 'varchar(100) AFTER SpecialCode')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('patient', 'add', 'Gender', 'varchar(4) AFTER Nationality')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('patient', 'add', 'FamilyPatientKey', 'varchar(10) AFTER PrivateInsurance')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('patient', 'add', 'Description', 'text AFTER History')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('patient', 'add', 'Allergy', 'text AFTER Alergy')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'CompletionTime', 'datetime AFTER CaseDate')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'PharmacyType', 'varchar(10) AFTER ApplyType')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'TreatType', 'varchar(10) AFTER RegistType')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'DebtFee', 'int AFTER Debt')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'SDiagShareFee', 'int AFTER ReceiptShare')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'DiagShareFee', 'int AFTER TreatShare')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'DrugShareFee', 'int AFTER DrugShare')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'Cashier', 'varchar(10) AFTER Casher')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'RefundFee', 'int AFTER Refund')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'SMaterialFee', 'int AFTER SMaterial')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('cases', 'add', 'TreatType', 'varchar(10) AFTER RegistType')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('prescript', 'add', 'PrescriptNo', 'int AFTER PrescriptKey')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('prescript', 'add', 'DosageMode', 'varchar(10) AFTER MedicineName')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('medicine', 'add', 'Dosage', 'decimal(10,2) AFTER Unit')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('medicine', 'add', 'Charged', 'varchar(4) AFTER InPrice')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('reserve', 'add', 'ReserveNo', 'int AFTER Sequence')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('reserve', 'add', 'Arrival', 'enum("False", "True") not null AFTER Doctor')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('wait', 'add', 'TreatType', 'varchar(10) AFTER RegistType')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('person', 'add', 'Birthday', 'date AFTER Name')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('person', 'add', 'Gender', 'varchar(2) AFTER ID')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('person', 'add', 'Email', 'varchar(100) AFTER Address')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('person', 'add', 'FullTime', 'varchar(10) AFTER Position')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('person', 'add', 'Department', 'varchar(20) AFTER Email')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('person', 'add', 'InputDate', 'date AFTER Department')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('debt', 'add', 'Cashier1', 'varchar(10) AFTER Casher1')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('debt', 'add', 'Cashier2', 'varchar(10) AFTER Casher2')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('debt', 'add', 'Cashier3', 'varchar(10) AFTER Casher3')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('insapply', 'add', 'Visit', 'varchar(10) AFTER ShareCode')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('patient', 'change', ['EMail', 'Email'], 'varchar(100)')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('person', 'change', ['EMail', 'Email'], 'varchar(100)')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('prescript', 'change', ['price', 'Price'], 'decimal(10,2)')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('prescript', 'change', ['amount', 'Amount'], 'decimal(10,2)')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('clinic', 'change', ['groups', 'Groups'], 'varchar(40)')
        progress += 1
        progress_dialog.setValue(progress)

        self.database.check_field_exists('medicine', 'change', ['location', 'Location'], 'varchar(20)')
        progress += 1
        progress_dialog.setValue(progress)

        progress_dialog.setValue(max_progress)


