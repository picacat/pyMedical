#!/usr/bin/env python3
# 掛號櫃台結帳 2018.11.15
#coding: utf-8

from PyQt5 import QtWidgets, QtPrintSupport
from PyQt5.QtWidgets import QMessageBox

from libs import system_utils
from libs import ui_utils
from libs import personnel_utils

from dialog import dialog_income
import massage_income_cash_flow
import massage_income_list

from printer import print_income


# 掛號櫃台結帳
class MassageIncome(QtWidgets.QMainWindow):
    program_name = '養生館櫃台結帳'

    # 初始化
    def __init__(self, parent=None, *args):
        super(MassageIncome, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.user_name = self.system_settings.field('使用者')
        self.tab_income_cash_flow = None
        self.tab_income_list = None
        self.tab_income_self_prescript = None

        self.income_date = None
        self.period = None
        self.dialog_setting = {
            "dialog_executed": False,
            "case_date": None,
            "period": None,
            "massager": None,
            "cashier": None,
        }

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MASSAGE_INCOME, self)
        system_utils.set_css(self, self.system_settings)

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_income)
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_export_daily_excel.triggered.connect(self._export_daily_excel)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

    # 讀取病歷
    def open_dialog(self):
        dialog = dialog_income.DialogIncome(self.ui, self.database, self.system_settings, '養生館櫃台結帳')
        if self.dialog_setting['dialog_executed']:
            dialog.ui.dateEdit_case_date.setDate(self.dialog_setting['case_date'])
            period = self.dialog_setting['period']
            if period == '早班':
                dialog.ui.radioButton_period1.setChecked(True)
            elif period == '午班':
                dialog.ui.radioButton_period2.setChecked(True)
            elif period == '晚班':
                dialog.ui.radioButton_period3.setChecked(True)
            else:
                dialog.ui.radioButton_all.setChecked(True)

            dialog.ui.comboBox_therapist.setCurrentText(self.dialog_setting['massager'])
            dialog.ui.comboBox_cashier.setCurrentText(self.dialog_setting['cashier'])

        if dialog.exec_():
            self.dialog_setting['dialog_executed'] = True
            self.dialog_setting['case_date'] = dialog.ui.dateEdit_case_date.date()

            if dialog.ui.radioButton_period1.isChecked():
                period = '早班'
            elif dialog.ui.radioButton_period2.isChecked():
                period = '午班'
            elif dialog.ui.radioButton_period3.isChecked():
                period = '晚班'
            else:
                period = '全部'

            self.dialog_setting['period'] = period
            self.dialog_setting['massager'] = dialog.comboBox_therapist.currentText()
            self.dialog_setting['cashier'] = dialog.comboBox_cashier.currentText()

            self.tab_income_cash_flow = massage_income_cash_flow.MassageIncomeCashFlow(
                self, self.database, self.system_settings,
                dialog.start_date, dialog.end_date,
                dialog.period, dialog.therapist,
                dialog.cashier,
            )
            self.tab_income_list = massage_income_list.MassageIncomeList(
                self, self.database, self.system_settings,
                dialog.start_date, dialog.end_date,
                dialog.period, dialog.therapist,
                dialog.cashier,
            )

            self.ui.tabWidget_income.clear()
            self.ui.tabWidget_income.addTab(self.tab_income_cash_flow, '收入統計')
            self.ui.tabWidget_income.addTab(self.tab_income_list, '收入一覽')

            self.income_date = dialog.start_date[:10]
            self.period = dialog.period

            self.tab_income_cash_flow.label_income_date.setText(self.income_date)
            self.tab_income_cash_flow.label_income_period.setText(self.period)
        else:
            self.income_date = None
            self.period = None

        dialog.close_all()
        dialog.deleteLater()

    def _export_daily_excel(self):
        self.tab_income_list.export_to_excel()

    def refresh_massage_case(self):
        self.tab_income_cash_flow.read_data()
        self.tab_income_list.read_massage_data()
