#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
import datetime
from libs import ui_utils
from libs import string_utils
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
        self.ui.tableWidget_return_card.doubleClicked.connect(self.return_card)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 80, 80, 80, 120, 130, 150, 180, 180, 60, 80, 40, 100, 100, 80]
        self.table_widget_return_card.set_table_heading_width(width)

    # 讀取欠卡資料
    def read_return_card(self, return_date=None):
        if return_date is None:
            since_date = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
            return_date = since_date.strftime('%Y-%m-01')

        sql = '''
            SELECT deposit.*, cases.Card, cases.Continuance, patient.Birthday, patient.ID, patient.CardNo 
            FROM deposit 
            LEFT JOIN cases ON cases.CaseKey = deposit.CaseKey
            LEFT JOIN patient ON patient.PatientKey = deposit.PatientKey
            WHERE DepositDate >= "{0}"
            ORDER BY DepositDate DESC
        '''.format(return_date)
        self.table_widget_return_card.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row_data):
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
        ]

        for column in range(0, self.ui.tableWidget_return_card.columnCount()):
            self.ui.tableWidget_return_card.setItem(row_no,
                                                    column,
                                                    QtWidgets.QTableWidgetItem(return_card_data[column]))
            if column in [2, 14]:
                self.ui.tableWidget_return_card.item(row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [8]:
                self.ui.tableWidget_return_card.item(row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

    def refresh_record(self):
        sql = '''
            SELECT deposit.*, cases.Card, cases.Continuance, patient.Birthday, patient.ID, patient.CardNo 
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
