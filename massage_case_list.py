#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton, QFileDialog
import datetime

from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import system_utils
from libs import personnel_utils
from libs import case_utils
from libs import export_utils
from libs import massage_utils

from classes import table_widget

from dialog import dialog_massage_case_list
from dialog import dialog_massage_reservation


# 主視窗
class MassageCaseList(QtWidgets.QMainWindow):
    program_name = '養生館消費查詢'

    # 初始化
    def __init__(self, parent=None, *args):
        super(MassageCaseList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.dialog_setting = {
            "dialog_executed": False,
            "start_date": None,
            "end_date": None,
            "period": None,
            "treat_type": None,
            "person": None,
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MASSAGE_CASE_LIST, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_massage_case = table_widget.TableWidget(
            self.ui.tableWidget_massage_case, self.database)
        self.table_widget_massage_case.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_delete_record.triggered.connect(self.delete_medical_record)
        self.ui.action_close.triggered.connect(self.close_massage_case_list)
        self.ui.action_open_record.triggered.connect(self.open_medical_record)
        self.ui.action_export_excel.triggered.connect(self._export_to_excel)
        self.ui.tableWidget_massage_case.doubleClicked.connect(self.open_medical_record)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        # 設定欄位寬度
    def _set_table_width(self):
        width = [
            100, 110, 50, 130, 90, 120, 90, 400, 90, 90, 120, 120, 250
        ]
        self.table_widget_massage_case.set_table_heading_width(width)

    # 讀取病歷
    def open_dialog(self):
        dialog = dialog_massage_case_list.DialogMassageCaseList(self, self.database, self.system_settings)
        if self.dialog_setting['dialog_executed']:
            dialog.ui.dateEdit_start_date.setDate(self.dialog_setting['start_date'])
            dialog.ui.dateEdit_end_date.setDate(self.dialog_setting['end_date'])
            dialog.ui.comboBox_period.setCurrentText(self.dialog_setting['period'])
            dialog.ui.comboBox_treat_type.setCurrentText(self.dialog_setting['treat_type'])
            dialog.ui.comboBox_massager.setCurrentText(self.dialog_setting['person'])

        result = dialog.exec_()
        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['start_date'] = dialog.ui.dateEdit_start_date.date()
        self.dialog_setting['end_date'] = dialog.ui.dateEdit_end_date.date()
        self.dialog_setting['period'] = dialog.comboBox_period.currentText()
        self.dialog_setting['treat_type'] = dialog.comboBox_treat_type.currentText()
        self.dialog_setting['person'] = dialog.comboBox_massager.currentText()

        sql = dialog.get_sql()
        dialog.close_all()
        dialog.deleteLater()

        if result == 0:
            return

        if sql == '':
            return

        try:
            self.table_widget_massage_case.set_db_data(sql, self._set_table_data)
        except:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '資料查詢錯誤',
                '<font size="4" color="red"><b>資料查詢條件設定有誤, 請重新查詢.</b></font>',
                '請檢查查詢的內容是否有標點符號或其他字元.'
            )

        self._set_tool_button()

    def _set_tool_button(self):
        if self.ui.tableWidget_massage_case.rowCount() > 0:
            enabled = True
        else:
            enabled = False

        self.ui.action_open_record.setEnabled(enabled)
        self.ui.action_delete_record.setEnabled(enabled)

        self._set_permission()

    def _set_table_data(self, row_no, row):
        massage_case_key = number_utils.get_integer(row['MassageCaseKey'])
        treat_type = string_utils.xstr(row['TreatType'])
        if treat_type == '養生館':
            massage_time = '{start_time} - {end_time}'.format(
                start_time= row['CaseDate'].strftime('%H:%M'),
                end_time=row['FinishDate'].strftime('%H:%M'),
            )
        else:
            massage_time = None

        massage_item = massage_utils.get_massage_prescript_item(self.database, massage_case_key)

        massage_row = [
            string_utils.xstr(massage_case_key),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['Period']),
            massage_time,
            string_utils.xstr(row['MassageCustomerKey']),
            string_utils.xstr(row['Name']),
            treat_type,
            massage_item,
            row['TotalFee'],
            row['ReceiptFee'],
            string_utils.xstr(row['Massager']),
            string_utils.xstr(row['Registrar']),
            string_utils.xstr(row['Remark']),
        ]

        for col_no in range(len(massage_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, massage_row[col_no])
            self.ui.tableWidget_massage_case.setItem(row_no, col_no, item)
            if col_no in [4, 8, 9]:
                self.ui.tableWidget_massage_case.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2]:
                self.ui.tableWidget_massage_case.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def delete_medical_record(self):
        name = self.table_widget_massage_case.field_value(5)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除病歷資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除<font color='blue'> {0} </font>的消費資料?</b></font>"
                        .format(name))
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        massage_case_key = self.table_widget_massage_case.field_value(0)

        self.database.delete_record('massage_cases', 'MassageCaseKey', massage_case_key)
        self.database.delete_record('massage_prescript', 'MassageCaseKey', massage_case_key)
        self.database.delete_record('massage_payment', 'MassageCaseKey', massage_case_key)
        current_row = self.ui.tableWidget_massage_case.currentRow()
        self.ui.tableWidget_massage_case.removeRow(current_row)

    def open_medical_record(self):
        massage_case_key = self.table_widget_massage_case.field_value(0)
        treat_type = self.table_widget_massage_case.field_value(6)

        if treat_type == '購買商品':
            self.parent.open_massage_purchase_tab('消費資料查詢', massage_case_key)
            return

        dialog = None
        if treat_type == '養生館':
            dialog = dialog_massage_reservation.DialogMassageReservation(
                self, self.database, self.system_settings,
                None, None, None, None, None,
                massage_case_key,
            )

        if dialog is None:
            return

        try:
            dialog.exec_()
        finally:
            dialog.close_all()
            dialog.deleteLater()

        self.refresh_massage_case()

    def refresh_massage_case(self):
        massage_case_key = self.table_widget_massage_case.field_value(0)
        sql = 'SELECT * FROM massage_cases where MassageCaseKey = {0}'.format(massage_case_key)
        row = self.database.select_record(sql)[0]
        current_row = self.ui.tableWidget_massage_case.currentRow()
        self._set_table_data(current_row, row)

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

    def close_massage_case_list(self):
        self.close_all()
        self.close_tab()

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

