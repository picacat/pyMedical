#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox

import datetime
from libs import ui_utils
from libs import string_utils
from libs import system_utils
from classes import table_widget
from dialog import dialog_return_card


# 樣板 2018.01.31
class ReturnCard(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ReturnCard, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        # self.read_return_card()   # activate by pymedical.py->tab_changed

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_return_card(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_RETURN_CARD, self)
        self.table_widget_return_card = table_widget.TableWidget(self.ui.tableWidget_return_card, self.database)
        self.table_widget_return_card.set_column_hidden([0, 1])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_return_card)
        self.ui.action_return_card.triggered.connect(self.return_card)
        self.ui.action_open_medical_record.triggered.connect(self.open_medical_record)
        self.ui.tableWidget_return_card.doubleClicked.connect(self.open_medical_record)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 80, 80, 80, 120, 130, 150, 180, 180, 60, 80, 40, 100, 100, 80, 70]
        self.table_widget_return_card.set_table_heading_width(width)

    # 讀取欠卡資料
    def read_return_card(self, return_date=None):
        if return_date is None:
            since_date = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
            return_date = since_date.strftime('%Y-%m-01')

        sql = '''
            SELECT 
                deposit.*, 
                cases.Card, cases.Continuance, cases.DoctorDone, 
                patient.Birthday, patient.ID, patient.CardNo 
            FROM deposit 
                LEFT JOIN cases ON cases.CaseKey = deposit.CaseKey
                LEFT JOIN patient ON patient.PatientKey = deposit.PatientKey
            WHERE DepositDate >= "{0}"
            ORDER BY DepositDate DESC
        '''.format(return_date)
        self.table_widget_return_card.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row_data):
        if string_utils.xstr(row_data['DoctorDone']) == 'True':
            doctor_done = '是'
        else:
            doctor_done = '否'

        return_card_data = [
            string_utils.xstr(row_data['DepositKey']),
            string_utils.xstr(row_data['CaseKey']),
            string_utils.xstr(row_data['PatientKey']),
            string_utils.xstr(row_data['Name']),
            string_utils.xstr(row_data['Birthday']),
            string_utils.xstr(row_data['ID']),
            string_utils.xstr(row_data['CardNo']),
            string_utils.xstr(row_data['DepositDate']),
            string_utils.xstr(row_data['ReturnDate']),
            string_utils.xstr(row_data['Period']),
            string_utils.xstr(row_data['Card']),
            string_utils.xstr(row_data['Continuance']),
            string_utils.xstr(row_data['Register']),
            string_utils.xstr(row_data['Refunder']),
            string_utils.xstr(row_data['Fee']),
            doctor_done,
        ]

        for column in range(len(return_card_data)):
            self.ui.tableWidget_return_card.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(return_card_data[column])
            )
            if column in [2, 14]:
                self.ui.tableWidget_return_card.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [9, 15]:
                self.ui.tableWidget_return_card.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def refresh_record(self):
        sql = '''
            SELECT 
                deposit.*, 
                cases.Card, cases.Continuance, cases.DoctorDone, 
                patient.Birthday, patient.ID, patient.CardNo 
            FROM deposit 
                LEFT JOIN cases ON cases.CaseKey = deposit.CaseKey
                LEFT JOIN patient ON patient.PatientKey = deposit.PatientKey
            WHERE DepositKey = {0}
        '''.format(self.table_widget_return_card.field_value(0))
        row = self.database.select_record(sql)
        if len(row) > 0:
            self._set_table_data(self.ui.tableWidget_return_card.currentRow(), row[0])

    # 還卡
    def return_card(self):
        if self.table_widget_return_card.field_value(10) != '欠卡':
            system_utils.show_message_box(
                QMessageBox.Critical,
                '不需還卡',
                '<font size="4" color="red"><b>此筆病歷的卡序不是"欠卡", 不需執行還卡作業.</b></font>',
                '請確定此人是否已經還卡.'
            )
            return

        if self.table_widget_return_card.field_value(15) != '是':
            system_utils.show_message_box(
                QMessageBox.Critical,
                '暫時無法還卡',
                '<font size="4" color="red"><b>此筆病歷尚未看診完畢, 暫時不需執行還卡作業.</b></font>',
                '請確定此人看診完畢後, 再執行還卡作業, 已利系統進行健保卡病歷及處方寫入的程序.'
            )
            return

        dialog = dialog_return_card.DialogReturnCard(
            self, self.database, self.system_settings,
            self.table_widget_return_card.field_value(0),
            self.table_widget_return_card.field_value(1),
            self.table_widget_return_card.field_value(2),
        )
        if dialog.exec_():
            self.refresh_record()

        dialog.deleteLater()

    def open_medical_record(self):
        case_key = self.table_widget_return_card.field_value(1)
        self.parent.open_medical_record(case_key, '欠還卡作業')
