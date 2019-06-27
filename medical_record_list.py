#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import  datetime

from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import printer_utils
from libs import system_utils
from libs import personnel_utils
from libs import case_utils
from dialog import dialog_medical_record_list
from classes import table_widget
from printer import print_prescription
from printer import print_receipt

from dialog import dialog_medical_record_done


# 主視窗
class MedicalRecordList(QtWidgets.QMainWindow):
    program_name = '病歷查詢'

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

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()

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
        self._set_tool_button()

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_delete_record.triggered.connect(self.delete_medical_record)
        self.ui.action_close.triggered.connect(self.close_medical_record_list)
        self.ui.action_open_record.triggered.connect(self.open_medical_record)
        self.ui.action_print_prescript.triggered.connect(self._print_prescript)
        self.ui.action_print_receipt.triggered.connect(self._print_receipt)
        self.ui.action_print_cases.triggered.connect(self._print_cases)
        self.ui.action_export_cases_pdf.triggered.connect(self._print_cases)
        self.ui.action_print_fees.triggered.connect(self._print_fees)
        self.ui.action_export_fees_pdf.triggered.connect(self._print_fees)
        self.ui.action_set_check.triggered.connect(self._set_check)
        self.ui.action_set_uncheck.triggered.connect(self._set_check)
        self.ui.tableWidget_medical_record_list.doubleClicked.connect(self.open_medical_record)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, self.program_name, '調閱病歷', self.user_name) != 'Y':
            self.ui.action_open_record.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '病歷刪除', self.user_name) != 'Y':
            self.ui.action_delete_record.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '匯出實體病歷', self.user_name) != 'Y':
            self.ui.action_export_cases_pdf.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '匯出收費明細', self.user_name) != 'Y':
            self.ui.action_export_fees_pdf.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '列印單據', self.user_name) != 'Y':
            self.ui.action_print_prescript.setEnabled(False)
            self.ui.action_print_receipt.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '列印報表', self.user_name) != 'Y':
            self.ui.action_print_cases.setEnabled(False)
            self.ui.action_print_fees.setEnabled(False)

        # 設定欄位寬度
    def _set_table_width(self):
        width = [
            70, 10, 160, 50, 40, 40, 40, 50, 80, 80, 40, 120, 50, 80, 80, 70, 40, 40, 80, 200,
            80, 80, 80, 80, 80
        ]
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

        if sql == '':
            return

        try:
            self.table_widget_medical_record_list.set_db_data(sql, self._set_table_data)
        except:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '資料查詢錯誤',
                '<font size="4" color="red"><b>病歷資料查詢條件設定有誤, 請重新查詢.</b></font>',
                '請檢查查詢的內容是否有標點符號或其他字元.'
            )

        self._set_tool_button()

    def _set_tool_button(self):
        if self.ui.tableWidget_medical_record_list.rowCount() > 0:
            enabled = True
        else:
            enabled = False

        self.ui.action_open_record.setEnabled(enabled)
        self.ui.action_delete_record.setEnabled(enabled)
        self.ui.action_print_prescript.setEnabled(enabled)
        self.ui.action_print_receipt.setEnabled(enabled)

        self._set_permission()

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
            None,
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['Period']),
            None,
            None,
            row['Room'],
            row['RegistNo'],
            row['PatientKey'],
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            row['Continuance'],
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['DiseaseName1']),
            pres_days,
            string_utils.xstr(row['Massager']),
            number_utils.get_integer(row['RegistFee']),
            number_utils.get_integer(row['SDiagShareFee']),
            number_utils.get_integer(row['SDrugShareFee']),
            number_utils.get_integer(row['TotalFee']),
        ]

        for column in range(len(medical_record)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, medical_record[column])
            self.ui.tableWidget_medical_record_list.setItem(
                row_no, column, item,
            )
            if column in [6, 7, 8, 16, 19, 21, 22, 23, 24]:
                self.ui.tableWidget_medical_record_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [3, 10]:
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

        self._set_print_check_box(row_no)
        self._set_done_status(row, row_no)

    def _set_print_check_box(self, row_no):
        check_box_print = QtWidgets.QCheckBox()
        check_box_print.setChecked(True)
        # check_box_print.setStyleSheet('margin:auto')
        col_no = 1

        self.ui.tableWidget_medical_record_list.setCellWidget(
            row_no, col_no, check_box_print)
        self.ui.tableWidget_medical_record_list.item(
            row_no, col_no).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )

    def _set_done_status(self, row, row_no):
        gtk_apply = './icons/gtk-apply.svg'
        gtk_close = './icons/gtk-close.svg'
        if string_utils.xstr(row['DoctorDone']) == 'True' and row['DoctorDate'] is not None:
            gtk_icon_file = gtk_apply
            property_value = True
        else:
            gtk_icon_file = gtk_close
            property_value = False

        ui_utils.set_table_widget_field_icon(
            self.ui.tableWidget_medical_record_list, row_no, 4, gtk_icon_file,
            'doctor_done', property_value, self._done_button_clicked)

        if (string_utils.xstr(row['ChargeDone']) == 'True' and
                row['ChargeDate'] is not None and
                row['ChargePeriod'] is not None):
            gtk_icon_file = gtk_apply
            property_value = True
        else:
            gtk_icon_file = gtk_close
            property_value = False

        ui_utils.set_table_widget_field_icon(
            self.ui.tableWidget_medical_record_list, row_no, 5, gtk_icon_file,
            'charge_done', property_value, self._done_button_clicked)

    # 更改完診或批價狀態
    def _done_button_clicked(self):
        property_name = string_utils.get_str(self.sender().dynamicPropertyNames()[0], 'utf-8')

        row_no = self.ui.tableWidget_medical_record_list.currentRow()
        doctor_done = self.ui.tableWidget_medical_record_list.cellWidget(
            row_no, 4).property(property_name)
        if doctor_done:
            return

        dialog = dialog_medical_record_done.DialogMedicalRecordDone(
            self, self.database, self.system_settings,
            self.table_widget_medical_record_list.field_value(0),
            property_name,
        )
        if dialog.exec_():
            self.refresh_medical_record()

        dialog.deleteLater()

    def delete_medical_record(self):
        name = self.table_widget_medical_record_list.field_value(9)
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

        case_utils.backup_medical_record(
            self.database, case_key, self.system_settings.field('使用者'),
            datetime.datetime.now(),
        )  # 備份資料

        self.database.delete_record('cases', 'CaseKey', case_key)
        self.database.delete_record('wait', 'CaseKey', case_key)
        self.database.delete_record('prescript', 'CaseKey', case_key)
        self.database.delete_record('dosage', 'CaseKey', case_key)
        self.database.delete_record('deposit', 'CaseKey', case_key)
        self.database.delete_record('debt', 'CaseKey', case_key)
        current_row = self.ui.tableWidget_medical_record_list.currentRow()
        self.ui.tableWidget_medical_record_list.removeRow(current_row)

    def open_medical_record(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, self.program_name, '調閱病歷', self.user_name) != 'Y'):
            return

        case_key = self.table_widget_medical_record_list.field_value(0)
        self.parent.open_medical_record(case_key, '病歷查詢')

    # 重新顯示資料 call from pymedical (call from here is not working)
    def refresh_medical_record(self):
        case_key = self.table_widget_medical_record_list.field_value(0)
        if case_key is None:
            return

        sql = '''
            SELECT 
                CaseKey, DATE_FORMAT(CaseDate, '%Y-%m-%d %H:%i') AS CaseDate, DoctorDate, ChargeDate,
                cases.PatientKey, cases.Name, Period, ChargePeriod, cases.InsType, 
                Share, cases.RegistNo, Card, Continuance, TreatType, 
                PresDays1, PresDays2, DiseaseCode1, DiseaseName1,
                Doctor, Massager, Room, RegistFee, SDiagShareFee, SDrugShareFee,
                ChargePeriod, DoctorDone, ChargeDone,
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
            self, self.database, self.system_settings, case_key, '選擇列印')
        print_prescript.print()

        del print_prescript

    # 列印醫療收據
    def _print_receipt(self):
        case_key = self.table_widget_medical_record_list.field_value(0)
        print_charge = print_receipt.PrintReceipt(
            self, self.database, self.system_settings, case_key, '選擇列印')
        print_charge.print()

        del print_charge


    def _set_check(self):
        sender_name = self.sender().objectName()
        if sender_name == 'action_set_check':
            check = True
        else:
            check = False

        row_count = self.ui.tableWidget_medical_record_list.rowCount()
        for row_no in range(row_count):
            check_box = self.ui.tableWidget_medical_record_list.cellWidget(row_no, 1)
            check_box.setChecked(check)

    def _print_cases(self):
        row_count = self.ui.tableWidget_medical_record_list.rowCount()
        patient_key = self.ui.tableWidget_medical_record_list.item(0, 8).text()

        for row_no in range(1, row_count):  # 檢查是否同一病患
            check_box = self.ui.tableWidget_medical_record_list.cellWidget(row_no, 1)
            if not check_box.isChecked():
                continue

            next_patient_key = self.ui.tableWidget_medical_record_list.item(row_no, 8)
            if next_patient_key is None:
                break
            else:
                next_patient_key = next_patient_key.text()
                if patient_key != next_patient_key:
                    patient_key = None
                    break

        case_key_list = []
        for row_no in range(row_count):
            check_box = self.ui.tableWidget_medical_record_list.cellWidget(row_no, 1)
            if check_box.isChecked():
                case_key_list.append(self.ui.tableWidget_medical_record_list.item(row_no, 0).text())

        if len(case_key_list) <= 0:
            return

        if patient_key is not None:
            patient_key_condition = 'AND PatientKey = {0}'.format(patient_key)
        else:
            patient_key_condition = ''

        sql = '''
            SELECT * FROM cases 
            WHERE
                CaseKey IN({case_key_list})
                {patient_key_condition}
            ORDER BY CaseKey
        '''.format(
            case_key_list=','.join(case_key_list),
            patient_key_condition=patient_key_condition,
        )

        sender_name = self.sender().objectName()
        if sender_name == 'action_print_cases':
            printer_utils.print_medical_records(
                self, self.database, self.system_settings,
                patient_key, sql, None, None,
            )
        else:
            printer_utils.print_medical_records(
                self, self.database, self.system_settings,
                patient_key, sql, None, None, 'pdf_by_dialog',
            )

    def _print_fees(self):
        row_count = self.ui.tableWidget_medical_record_list.rowCount()
        patient_key = self.ui.tableWidget_medical_record_list.item(0, 8).text()

        for row_no in range(1, row_count):  # 檢查是否同一病患
            check_box = self.ui.tableWidget_medical_record_list.cellWidget(row_no, 1)
            if not check_box.isChecked():
                continue

            next_patient_key = self.ui.tableWidget_medical_record_list.item(row_no, 8)
            if next_patient_key is None:
                break
            else:
                next_patient_key = next_patient_key.text()
                if patient_key != next_patient_key:
                    patient_key = None
                    break

        case_key_list = []
        for row_no in range(row_count):
            check_box = self.ui.tableWidget_medical_record_list.cellWidget(row_no, 1)
            if check_box.isChecked():
                case_key_list.append(self.ui.tableWidget_medical_record_list.item(row_no, 0).text())

        if len(case_key_list) <= 0:
            return

        if patient_key is not None:
            patient_key_condition = 'AND PatientKey = {0}'.format(patient_key)
        else:
            patient_key_condition = ''

        sql = '''
            SELECT * FROM cases 
            WHERE
                CaseKey IN({case_key_list})
                {patient_key_condition}
            ORDER BY CaseKey
        '''.format(
            case_key_list=','.join(case_key_list),
            patient_key_condition=patient_key_condition,
        )

        sender_name = self.sender().objectName()
        if sender_name == 'action_print_fees':
            printer_utils.print_medical_fees(
                self, self.database, self.system_settings,
                patient_key, sql,
            )
        else:
            printer_utils.print_medical_fees(
                self, self.database, self.system_settings,
                patient_key, sql, 'pdf_by_dialog',
            )
