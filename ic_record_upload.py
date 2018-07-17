#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from dialog import dialog_ic_record_upload
from classes import table_widget


# 主視窗
class ICRecordUpload(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ICRecordUpload, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.dialog_setting = {
            "dialog_executed": False,
            "start_date": None,
            "end_date": None,
            "period": None,
            "ins_type": None,
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_IC_RECORD_UPLOAD, self)
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_ic_record, self.database)
        self.table_widget_medical_record.set_column_hidden([0])
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_close.triggered.connect(self.close_medical_record_list)
        self.ui.action_open_record.triggered.connect(self.open_medical_record)
        self.ui.tableWidget_ic_record.doubleClicked.connect(self.open_medical_record)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [70, 160, 50, 40, 50, 80, 80, 40, 120, 50, 80, 80, 70, 40, 40, 80, 200,
                 80, 80, 80, 80, 80]
        self.table_widget_medical_record.set_table_heading_width(width)

    # 讀取病歷
    def open_dialog(self):
        dialog = dialog_ic_record_upload.DialogICRecordUpload(self, self.database, self.system_settings)
        if self.dialog_setting['dialog_executed']:
            dialog.ui.dateEdit_start_date.setDate(self.dialog_setting['start_date'])
            dialog.ui.dateEdit_end_date.setDate(self.dialog_setting['end_date'])
            dialog.ui.comboBox_period.setCurrentText(self.dialog_setting['period'])
            dialog.ui.comboBox_ins_type.setCurrentText(self.dialog_setting['ins_type'])

        result = dialog.exec_()
        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['start_date'] = dialog.ui.dateEdit_start_date.date()
        self.dialog_setting['end_date'] = dialog.ui.dateEdit_end_date.date()
        self.dialog_setting['period'] = dialog.comboBox_period.currentText()

        sql = dialog.get_sql()
        dialog.close_all()
        dialog.deleteLater()

        if result == 0:
            return

        self.table_widget_medical_record.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, rec_no, rec):
        if rec['InsType'] == '健保':
            medicine_set = 1
        else:
            medicine_set = 2
        sql = '''
            SELECT * FROM dosage WHERE
            CaseKey = {0} AND MedicineSet = {1}
        '''.format(rec['CaseKey'], medicine_set)
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            pres_days = rows[0]['Days']
        else:
            pres_days = None

        medical_record = [
            string_utils.xstr(rec['CaseKey']),
            string_utils.xstr(rec['CaseDate']),
            string_utils.xstr(rec['Period']),
            string_utils.xstr(rec['Room']),
            string_utils.xstr(rec['RegistNo']),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Gender']),
            string_utils.xstr(rec['Birthday']),
            string_utils.xstr(rec['InsType']),
            string_utils.xstr(rec['Share']),
            string_utils.xstr(rec['TreatType']),
            string_utils.xstr(rec['Card']),
            string_utils.int_to_str(rec['Continuance']).strip('0'),
            string_utils.int_to_str(pres_days),
            string_utils.xstr(rec['Doctor']),
            string_utils.xstr(rec['DiseaseName1']),
            string_utils.xstr(rec['Massager']),
            string_utils.int_to_str(rec['RegistFee']),
            string_utils.int_to_str(rec['SDiagShareFee']),
            string_utils.int_to_str(rec['SDrugShareFee']),
            string_utils.int_to_str(rec['TotalFee']),
        ]

        for column in range(0, self.ui.tableWidget_ic_record.columnCount()):
            self.ui.tableWidget_ic_record.setItem(rec_no, column, QtWidgets.QTableWidgetItem(medical_record[column]))
            if column in [3, 4, 5, 13, 14, 18, 19, 20, 21]:
                self.ui.tableWidget_ic_record.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [7]:
                self.ui.tableWidget_ic_record.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

            if number_utils.get_integer(rec['TotalFee']) > 0 or rec['InsType'] == '自費':
                self.ui.tableWidget_ic_record.item(rec_no, column).setForeground(QtGui.QColor('blue'))

    def delete_medical_record(self):
        name = self.table_widget_medical_record.field_value(6)
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

        case_key = self.table_widget_medical_record.field_value(0)
        self.database.delete_record('cases', 'CaseKey', case_key)
        self.database.delete_record('wait', 'CaseKey', case_key)
        self.database.delete_record('prescript', 'CaseKey', case_key)
        self.database.delete_record('deposit', 'CaseKey', case_key)
        self.database.delete_record('debt', 'CaseKey', case_key)
        current_row = self.ui.tableWidget_ic_record.currentRow()
        self.ui.tableWidget_ic_record.removeRow(current_row)

    def open_medical_record(self):
        case_key = self.table_widget_medical_record.field_value(0)
        self.parent.open_medical_record(case_key, '病歷查詢')

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_medical_record_list(self):
        self.close_all()
        self.close_tab()
