#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton, QFileDialog
import datetime

from libs import ui_utils
from libs import date_utils
from libs import db_utils
from libs import string_utils
from libs import number_utils
from libs import printer_utils
from libs import system_utils
from libs import personnel_utils
from libs import case_utils
from libs import export_utils
from libs import log_utils

from dialog import dialog_medical_record_list
from classes import table_widget
from printer import print_prescription
from printer import print_receipt
from printer import print_misc
from printer import print_registration

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
        system_utils.set_css(self, self.system_settings)
        self.table_widget_medical_record_list = table_widget.TableWidget(
            self.ui.tableWidget_medical_record_list, self.database)
        self.table_widget_medical_record_list.set_column_hidden([0])
        # database._set_table_width()
        self._set_tool_button()

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_delete_record.triggered.connect(self.delete_medical_record)
        self.ui.action_close.triggered.connect(self.close_medical_record_list)
        self.ui.action_open_record.triggered.connect(self.open_medical_record)
        self.ui.action_print_prescript.triggered.connect(self._print_prescript)
        self.ui.action_print_receipt.triggered.connect(self._print_receipt)
        self.ui.action_print_misc.triggered.connect(self._print_misc)
        self.ui.action_print_cases.triggered.connect(self._print_cases)
        self.ui.action_export_cases_pdf.triggered.connect(self._print_cases)
        self.ui.action_print_fees.triggered.connect(self._print_fees)
        self.ui.action_export_fees_pdf.triggered.connect(self._print_fees)
        self.ui.action_set_check.triggered.connect(self._set_check)
        self.ui.action_set_uncheck.triggered.connect(self._set_check)
        self.ui.action_export_excel.triggered.connect(self._export_to_excel)
        self.ui.action_export_medical_record_excel.triggered.connect(self._export_medical_record_to_excel)
        self.ui.action_export_json.triggered.connect(self._export_to_json)
        self.ui.action_print_registration.triggered.connect(self._print_registration)
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
        self.ui.action_print_registration.setEnabled(enabled)
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
            if string_utils.xstr(row['InProgress']) == 'Y':
                self.ui.tableWidget_medical_record_list.item(
                    row_no, column).setForeground(
                    QtGui.QColor('red')
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
        in_progress = string_utils.xstr(row['InProgress'])
        if in_progress == 'Y':
            case_utils.set_in_progress_icon(
                self.ui.tableWidget_medical_record_list, row_no, 4, in_progress
            )
            return

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

        card = self.table_widget_medical_record_list.field_value(15)
        course = self.table_widget_medical_record_list.field_value(16)
        log = '{patient_name}於{now}執行病歷刪除, 卡序:{card}, 主治醫師: {room}診{doctor}醫師'.format(
            patient_name=name,
            now=date_utils.now_to_str(),
            ins_type=self.table_widget_medical_record_list.field_value(5),
            card=card + '-{0}'.format(course) if number_utils.get_integer(course) >= 1 else card,
            room=self.table_widget_medical_record_list.field_value(6),
            doctor=self.table_widget_medical_record_list.field_value(17),
        )
        self._write_event_log('資料刪除', log)

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
                cases.CaseKey, DATE_FORMAT(cases.CaseDate, '%Y-%m-%d %H:%i') AS CaseDate, 
                cases.DoctorDate, cases.ChargeDate,
                cases.PatientKey, cases.Name, cases.Period, cases.ChargePeriod, cases.InsType, 
                cases.Share, cases.RegistNo, cases.Card, cases.Continuance, cases.TreatType, 
                PresDays1, PresDays2, DiseaseCode1, DiseaseName1,
                cases.Doctor, cases.Massager, cases.Room, RegistFee, SDiagShareFee, SDrugShareFee,
                cases.ChargePeriod, cases.DoctorDone, cases.ChargeDone,
                TotalFee, patient.Gender, patient.Birthday, wait.InProgress
            FROM cases
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
                LEFT JOIN wait ON wait.CaseKey = cases.CaseKey
            WHERE 
                cases.CaseKey = {0}
        '''.format(case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
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

    # 列印其他收據
    def _print_misc(self):
        case_key = self.table_widget_medical_record_list.field_value(0)
        print_other = print_misc.PrintMisc(
            self, self.database, self.system_settings, case_key, '選擇列印')
        print_other.print()

        del print_other

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

    # 匯出病歷資料 2019.10.14
    def _export_medical_record_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出病歷資料",
            '{0}至{1}{2}病歷資料.xlsx'.format(
                self.dialog_setting['start_date'].toString('yyyy-MM-dd'),
                self.dialog_setting['end_date'].toString('yyyy-MM-dd'),
                self.dialog_setting['person'],
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_medical_record_list,
            [0, 1, 4, 5], [6, 7, 8, 16, 19, 21, 22, 23, 24],
            '{0}至{1}{2}病歷資料'.format(
                self.dialog_setting['start_date'].toString('yyyy-MM-dd'),
                self.dialog_setting['end_date'].toString('yyyy-MM-dd'),
                self.dialog_setting['person'],
            )
        )
        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>病歷資料{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    # 匯出日報表 2019.07.01
    def _export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出日報表",
            '{0}至{1}{2}門診日報表.xlsx'.format(
                self.dialog_setting['start_date'].toString('yyyy-MM-dd'),
                self.dialog_setting['end_date'].toString('yyyy-MM-dd'),
                self.dialog_setting['person'],
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_daily_medical_records_to_excel(
            self.database, self.system_settings, excel_file_name, self.ui.tableWidget_medical_record_list,
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>門診日報表{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    # 匯出JSON 2019.09.26
    def _export_to_json(self):
        options = QFileDialog.Options()
        json_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出JSON檔案",
            '{start_date}至{end_date}病歷資料.json'.format(
                start_date=self.dialog_setting['start_date'].toString("yyyy-MM-dd"),
                end_date=self.dialog_setting['end_date'].toString("yyyy-MM-dd"),
            ),
            "json檔案 (*.json)",
            options=options
        )
        if not json_file_name:
            return

        row_count = self.ui.tableWidget_medical_record_list.rowCount()
        case_key_list = []
        for row_no in range(row_count):
            check_box = self.ui.tableWidget_medical_record_list.cellWidget(row_no, 1)
            if not check_box.isChecked():
                continue

            case_key = self.ui.tableWidget_medical_record_list.item(row_no, 0).text()
            case_key_list.append(case_key)

        if len(case_key_list) <= 0:
            return

        sql = '''
            SELECT * FROM cases
            WHERE
                CaseKey in ({case_key_list})
        '''.format(
            case_key_list=str(case_key_list)[1:-1]
        )
        rows = self.database.select_record(sql)

        for row in rows:
            case_key = row['CaseKey']
            patient_key = row['PatientKey']

            row['PatientJSON'] = self._get_patient_row(patient_key)
            row['TreatJSON'] = self._get_pres_extend_treat_row(case_key)
            row['DosageJSON'] = self._get_dosage_row(case_key)
            row['PrescriptJSON'] = self._get_prescript_row(case_key)

        json_data = db_utils.mysql_to_json(rows)
        text_file = open(json_file_name, "w", encoding='utf8')
        text_file.write(str(json_data))
        text_file.close()

        system_utils.show_message_box(
            QMessageBox.Information,
            'JSON資料匯出完成',
            '<h3>病歷資料 {0}匯出完成.</h3>'.format(json_file_name),
            'JSON 檔案格式.'
        )

        log = '{now}匯出JSON檔案, 檔案名稱: {json_file_name}'.format(
            now=date_utils.now_to_str(),
            json_file_name=json_file_name,
        )
        self._write_event_log('資料匯出', log)

    def _get_patient_row(self, patient_key):
        sql = '''
            SELECT * FROM patient
            WHERE
                PatientKey = {patient_key}
        '''.format(
            patient_key=patient_key,
        )
        rows = self.database.select_record(sql)

        return rows

    def _get_dosage_row(self, case_key):
        sql = '''
            SELECT * FROM dosage
            WHERE
                CaseKey = {case_key}
            ORDER BY MedicineSet
        '''.format(
            case_key=case_key,
        )
        rows = self.database.select_record(sql)

        return rows

    def _get_prescript_row(self, case_key):
        sql = '''
            SELECT * FROM prescript
            WHERE
                CaseKey = {case_key}
            ORDER BY PrescriptKey
        '''.format(
            case_key=case_key,
        )
        rows = self.database.select_record(sql)

        for row in rows:
            prescript_key = row['PrescriptKey']
            pres_extend_row = self._get_pres_extend_row(prescript_key)
            row['PresExtendJSON'] = pres_extend_row

        return rows

    def _get_pres_extend_treat_row(self, case_key):
        sql = '''
            SELECT * FROM presextend
            WHERE
                PrescriptKey = {case_key} AND
                ExtendType = "處置簽章"
            ORDER BY PresExtendKey LIMIT 1
        '''.format(
            case_key=case_key,
        )
        rows = self.database.select_record(sql)

        return rows

    def _get_pres_extend_row(self, prescript_key):
        sql = '''
            SELECT * FROM presextend
            WHERE
                PrescriptKey = {prescript_key} AND
                ExtendType = "處方簽章"
            ORDER BY PresExtendKey
        '''.format(
            prescript_key=prescript_key,
        )
        rows = self.database.select_record(sql)

        return rows

    # 列印掛號收據
    def _print_registration(self):
        case_key = self.table_widget_medical_record_list.field_value(0)
        self.print_registration_form('直接列印', case_key)

    # 列印掛號收據
    def print_registration_form(self, printable, case_key=False):
        if not case_key:
            case_key = self.table_widget_medical_record_list.field_value(0)

        print_regist = print_registration.PrintRegistration(
            self, self.database, self.system_settings, case_key, printable
        )
        print_regist.print()
        del print_regist

    def _write_event_log(self, log_type, log):
        log_utils.write_event_log(
            self.database, self.system_settings.field('使用者'),
            log_type, self.program_name, log
        )
