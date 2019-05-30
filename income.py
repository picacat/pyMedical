#!/usr/bin/env python3
# 掛號櫃台結帳 2018.11.15
#coding: utf-8

from PyQt5 import QtWidgets, QtPrintSupport

from libs import ui_utils
from libs import personnel_utils

from dialog import dialog_income
import income_cash_flow
import income_list

from printer import print_income


# 掛號櫃台結帳
class Income(QtWidgets.QMainWindow):
    program_name = '掛號櫃台結帳'

    # 初始化
    def __init__(self, parent=None, *args):
        super(Income, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
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

    def open_medical_record(self, case_key, call_from):
        self.parent.open_medical_record(case_key, call_from)

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
        self.ui.action_print.triggered.connect(self._print_income)
        self.ui.action_print_pdf.triggered.connect(self._print_income)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, self.program_name, '列印日報表', self.user_name) != 'Y':
            self.ui.action_print.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '匯出日報表', self.user_name) != 'Y':
            self.ui.action_print_pdf.setEnabled(False)

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

            self.income_date = dialog.start_date[:10]
            self.period = dialog.period

            self.tab_incom_cash_flow.label_income_date.setText(self.income_date)
            self.tab_incom_cash_flow.label_income_period.setText(self.period)
        else:
            self.income_date = None
            self.period = None

        dialog.close_all()
        dialog.deleteLater()

    def _print_income(self):
        sender_name = self.sender().objectName()
        print_type = None

        if self.system_settings.field('列印報表') == '不印':
            return
        elif self.system_settings.field('列印報表') == '詢問':
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec() == QtWidgets.QDialog.Rejected:
                return
        elif self.system_settings.field('列印報表') == '預覽':
            print_type = 'preview'
        elif self.system_settings.field('列印報表') == '列印':
            print_type = 'print'

        if sender_name == 'action_print_pdf':
            print_type = 'pdf'

        dialog = print_income.PrintIncome(
            self, self.database, self.system_settings,
            self.tab_incom_cash_flow.label_income_date.text(),
            self.tab_incom_cash_flow.label_income_period.text(),
            self.tab_incom_list.ui.tableWidget_income,
            self.tab_incom_cash_flow.ui.tableWidget_total,
        )

        if print_type == 'print':
            dialog.print()
        elif print_type == 'preview':
            dialog.preview()
        elif print_type == 'pdf':
            dialog.save_to_pdf()

        del dialog


