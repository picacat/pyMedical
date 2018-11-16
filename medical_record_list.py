#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from dialog import dialog_medical_record_list
from classes import table_widget
from printer import print_prescription
from printer import print_receipt


# 主視窗
class MedicalRecordList(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MedicalRecordList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.dialog_setting = {
            "dialog_executed": False,
            "start_date": None,
            "end_date": None,
            "period": None,
            "ins_type": None,
            "treat_type": None,
            "share_type": None,
            "apply_type": None,
            "person": None,
            "room": None,
        }
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MEDICAL_RECORD_LIST, self)
        self.table_widget_medical_record_list = table_widget.TableWidget(
            self.ui.tableWidget_medical_record_list, self.database)
        self.table_widget_medical_record_list.set_column_hidden([0])
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_delete_record.triggered.connect(self.delete_medical_record)
        self.ui.action_close.triggered.connect(self.close_medical_record_list)
        self.ui.action_open_record.triggered.connect(self.open_medical_record)
        self.ui.action_print_prescript.triggered.connect(self._print_prescript)
        self.ui.action_print_receipt.triggered.connect(self._print_receipt)
        self.ui.tableWidget_medical_record_list.doubleClicked.connect(self.open_medical_record)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [70, 160, 50, 40, 50, 80, 80, 40, 120, 50, 80, 80, 70, 40, 40, 80, 200,
                 80, 80, 80, 80, 80]
        self.table_widget_medical_record_list.set_table_heading_width(width)

    # 讀取病歷
    def open_dialog(self):
        dialog = dialog_medical_record_list.DialogMedicalRecordList(self, self.database, self.system_settings)
        if self.dialog_setting['dialog_executed']:
            dialog.ui.dateEdit_start_date.setDate(self.dialog_setting['start_date'])
            dialog.ui.dateEdit_end_date.setDate(self.dialog_setting['end_date'])
            dialog.ui.comboBox_period.setCurrentText(self.dialog_setting['period'])
            dialog.ui.comboBox_ins_type.setCurrentText(self.dialog_setting['ins_type'])
            dialog.ui.comboBox_treat_type.setCurrentText(self.dialog_setting['treat_type'])
            dialog.ui.comboBox_share_type.setCurrentText(self.dialog_setting['share_type'])
            dialog.ui.comboBox_apply_type.setCurrentText(self.dialog_setting['apply_type'])
            dialog.ui.comboBox_doctor.setCurrentText(self.dialog_setting['person'])
            dialog.ui.comboBox_room.setCurrentText(self.dialog_setting['room'])

        result = dialog.exec_()
        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['start_date'] = dialog.ui.dateEdit_start_date.date()
        self.dialog_setting['end_date'] = dialog.ui.dateEdit_end_date.date()
        self.dialog_setting['period'] = dialog.comboBox_period.currentText()
        self.dialog_setting['ins_type'] = dialog.comboBox_ins_type.currentText()
        self.dialog_setting['treat_type'] = dialog.comboBox_treat_type.currentText()
        self.dialog_setting['share_type'] = dialog.comboBox_share_type.currentText()
        self.dialog_setting['apply_type'] = dialog.comboBox_apply_type.currentText()
        self.dialog_setting['person'] = dialog.comboBox_doctor.currentText()
        self.dialog_setting['room'] = dialog.comboBox_room.currentText()

        sql = dialog.get_sql()
        dialog.close_all()
        dialog.deleteLater()

        if result == 0:
            return

        self.table_widget_medical_record_list.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        if row['InsType'] == '健保':
            medicine_set = 1
        else:
            medicine_set = 2
        sql = '''
            SELECT * FROM dosage WHERE
            CaseKey = {0} AND MedicineSet = {1}
        '''.format(row['CaseKey'], medicine_set)
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            pres_days = rows[0]['Days']
        else:
            pres_days = None

        medical_record = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['Room']),
            string_utils.xstr(row['RegistNo']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            string_utils.int_to_str(row['Continuance']).strip('0'),
            string_utils.int_to_str(pres_days),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['Massager']),
            string_utils.int_to_str(row['RegistFee']),
            string_utils.int_to_str(row['SDiagShareFee']),
            string_utils.int_to_str(row['SDrugShareFee']),
            string_utils.int_to_str(row['TotalFee']),
        ]

        for column in range(len(medical_record)):
            self.ui.tableWidget_medical_record_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record[column])
            )
            if column in [3, 4, 5, 13, 14, 18, 19, 20, 21]:
                self.ui.tableWidget_medical_record_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [7]:
                self.ui.tableWidget_medical_record_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if number_utils.get_integer(row['TotalFee']) > 0:
                self.ui.tableWidget_medical_record_list.item(
                    row_no, column).setForeground(QtGui.QColor('blue')
                                                  )
            if string_utils.xstr(row['InsType']) == '自費':
                self.ui.tableWidget_medical_record_list.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
                )
            if string_utils.xstr(row['TreatType']) == '自購':
                self.ui.tableWidget_medical_record_list.item(
                    row_no, column).setForeground(
                    QtGui.QColor('darkgreen')
                )

    def delete_medical_record(self):
        name = self.table_widget_medical_record_list.field_value(6)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除病歷資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除<font color='blue'> {0} </font>的病歷資料?</b></font>"
                        .format(name))
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        case_key = self.table_widget_medical_record_list.field_value(0)
        self.database.delete_record('cases', 'CaseKey', case_key)
        self.database.delete_record('wait', 'CaseKey', case_key)
        self.database.delete_record('prescript', 'CaseKey', case_key)
        self.database.delete_record('deposit', 'CaseKey', case_key)
        self.database.delete_record('debt', 'CaseKey', case_key)
        current_row = self.ui.tableWidget_medical_record_list.currentRow()
        self.ui.tableWidget_medical_record_list.removeRow(current_row)

    def open_medical_record(self):
        case_key = self.table_widget_medical_record_list.field_value(0)
        self.parent.open_medical_record(case_key, '病歷查詢')

    # 重新顯示資料 call from pymedical (call from here is not working)
    def refresh_medical_record(self):
        case_key = self.table_widget_medical_record_list.field_value(0)
        sql = '''
            SELECT 
                CaseKey, DATE_FORMAT(CaseDate, '%Y-%m-%d %H:%i') AS CaseDate, 
                cases.PatientKey, cases.Name, Period, cases.InsType, 
                Share, cases.RegistNo, Card, Continuance, TreatType, 
                PresDays1, PresDays2, DiseaseCode1, DiseaseName1,
                Doctor, Massager, Room, RegistFee, SDiagShareFee, SDrugShareFee,
                TotalFee, patient.Gender, patient.Birthday
            FROM cases
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE 
                CaseKey = {0}
        '''.format(case_key)
        row = self.database.select_record(sql)[0]
        current_row = self.ui.tableWidget_medical_record_list.currentRow()
        self._set_table_data(current_row, row)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_medical_record_list(self):
        self.close_all()
        self.close_tab()

    # 列印處方箋
    def _print_prescript(self):
        case_key = self.table_widget_medical_record_list.field_value(0)
        print_prescript = print_prescription.PrintPrescription(
            self, self.database, self.system_settings, case_key, '列印')
        print_prescript.print()

        del print_prescript

    # 列印醫療收據
    def _print_receipt(self):
        case_key = self.table_widget_medical_record_list.field_value(0)
        print_charge = print_receipt.PrintReceipt(
            self, self.database, self.system_settings, case_key, '列印')
        print_charge.print()

        del print_charge
