#!/usr/bin/env python3
# 掛號櫃台結帳 2018.11.15
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import case_utils
from libs import nhi_utils

from dialog import dialog_income
import income_cash_flow
import income_list


# 掛號櫃台結帳
class Income(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Income, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def open_medical_record(self):
        if self.ui.tableWidget_registration.hasFocused():
            case_key = self.table_widget_registration.field_value(0)
        elif self.ui.tableWidget_charge.hasFocused():
            case_key = self.table_widget_charge.field_value(0)
        else:
            return

        self.parent.open_medical_record(case_key, '病歷查詢')

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_income(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INCOME, self)

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_income)
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_open_medical_record.triggered.connect(self.open_medical_record)

    # 讀取病歷
    def open_dialog(self):
        dialog = dialog_income.DialogIncome(self.ui, self.database, self.system_settings)
        if dialog.exec_():
            self.tab_incom_cash_flow = income_cash_flow.IncomeCashFlow(
                self, self.database, self.system_settings,
                dialog.start_date, dialog.end_date,
                dialog.period, dialog.room,
                dialog.cashier,
            )
            self.tab_incom_list = income_list.IncomeList(
                self, self.database, self.system_settings,
                self.tab_incom_cash_flow.ui.tableWidget_registration,
                self.tab_incom_cash_flow.ui.tableWidget_charge,
            )
            self.ui.tabWidget_income.clear()
            self.ui.tabWidget_income.addTab(self.tab_incom_cash_flow, '現金收入分析')
            self.ui.tabWidget_income.addTab(self.tab_incom_list, '交帳明細一覽')

        dialog.close_all()
        dialog.deleteLater()

