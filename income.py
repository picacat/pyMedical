#!/usr/bin/env python3
# 掛號櫃台結帳 2018.11.15
#coding: utf-8

from PyQt5 import QtWidgets, QtPrintSupport
from PyQt5.QtWidgets import QMessageBox

from libs import system_utils
from libs import ui_utils
from libs import personnel_utils

from dialog import dialog_income
import income_cash_flow
import income_list
import income_self_prescript

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
        self.tab_income_cash_flow = None
        self.tab_income_list = None
        self.tab_income_self_prescript = None

        self.dialog_setting = {
            "dialog_executed": False,
            "case_date": None,
            "period": None,
            "therapist": None,
            "cashier": None,
        }
        self.income_date = None
        self.period = None

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
        system_utils.set_css(self, self.system_settings)

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_income)
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_print.triggered.connect(self._print_income)
        self.ui.action_print_pdf.triggered.connect(self._print_income)
        self.ui.action_export_daily_excel.triggered.connect(self._export_daily_excel)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, self.program_name, '列印日報表', self.user_name) != 'Y':
            self.ui.action_print.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '匯出日報表', self.user_name) != 'Y':
            self.ui.action_print_pdf.setEnabled(False)

    # 讀取病歷
    def open_dialog(self):
        dialog = dialog_income.DialogIncome(self.ui, self.database, self.system_settings, '掛號櫃台結帳')
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

            dialog.ui.comboBox_therapist.setCurrentText(self.dialog_setting['therapist'])
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
            self.dialog_setting['therapist'] = dialog.comboBox_therapist.currentText()
            self.dialog_setting['cashier'] = dialog.comboBox_cashier.currentText()

            if self._check_unpaid_cases(
                    dialog.start_date, dialog.end_date, dialog.period, dialog.therapist, dialog.cashier):
                return

            self.tab_income_cash_flow = income_cash_flow.IncomeCashFlow(
                self, self.database, self.system_settings,
                dialog.start_date, dialog.end_date,
                dialog.period, dialog.therapist,
                dialog.cashier,
            )
            self.tab_income_list = income_list.IncomeList(
                self, self.database, self.system_settings,
                dialog.start_date, dialog.end_date,
                dialog.period, dialog.therapist,
                self.tab_income_cash_flow.ui.tableWidget_registration,
                self.tab_income_cash_flow.ui.tableWidget_charge,
            )
            self.tab_income_self_prescript = income_self_prescript.IncomeSelfPrescript(
                self, self.database, self.system_settings,
                dialog.start_date, dialog.end_date,
                dialog.period, dialog.therapist,
                dialog.cashier,
            )

            self._check_unpaid_record(dialog.start_date, dialog.end_date)

            self.ui.tabWidget_income.clear()
            self.ui.tabWidget_income.addTab(self.tab_income_cash_flow, '現金收入分析')
            self.ui.tabWidget_income.addTab(self.tab_income_list, '交帳明細一覽')
            self.ui.tabWidget_income.addTab(self.tab_income_self_prescript, '自費明細表')

            self.income_date = dialog.start_date[:10]
            self.period = dialog.period

            self.tab_income_cash_flow.label_income_date.setText(self.income_date)
            self.tab_income_cash_flow.label_income_period.setText(self.period)
        else:
            self.income_date = None
            self.period = None

        dialog.close_all()
        dialog.deleteLater()

    def _check_unpaid_cases(self, start_date, end_date, period, doctor, cashier):
        if self.system_settings.field('櫃台結帳班別') == '掛號班別':
            return False

        sql = '''
            SELECT 
                Name, Period 
            FROM cases
            WHERE 
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND 
                (ChargeDate IS NULL OR ChargePeriod IS NULL) AND
                ChargeDone = "True"
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )
        if period != '全部':
            sql += ' AND Period = "{0}"'.format(period)
        if doctor != '全部':
            sql += ' AND Doctor = "{0}"'.format(doctor)
        if cashier != '全部':
            sql += ' AND Cashier = "{0}"'.format(cashier)

        rows = self.database.select_record(sql)
        if len(rows) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '尚有未批價名單',
                '<font color="red"><h3>尚有未批價名單, 請至病歷查詢檢視並批價!</h3></font>',
                '請確認所有病歷均已完成批價.'
            )
            return True

        return False

    def _check_unpaid_record(self, start_date, end_date):
        sql = '''
            SELECT CaseKey FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" and "{end_date}" AND
                DoctorDone = "True" AND
                ChargeDone = "False"
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            system_utils.show_message_box(
                QMessageBox.Warning,
                '批價檢查',
                '<font size="4" color="red"><b>今日門診資料尚有未批價名單, 請檢查是否已經全部批價.</b></font>',
                '請確定所有病歷均已批價, 否則櫃台結帳會無法統計尚未批價的資料.'
            )

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
            self.tab_income_cash_flow.label_income_date.text(),
            self.tab_income_cash_flow.label_income_period.text(),
            self.tab_income_list.ui.tableWidget_income,
            self.tab_income_cash_flow.ui.tableWidget_total,
        )

        if print_type == 'print':
            dialog.print()
        elif print_type == 'preview':
            dialog.preview()
        elif print_type == 'pdf':
            dialog.save_to_pdf()

        del dialog

    def _export_daily_excel(self):
        if self.ui.tabWidget_income.currentIndex() == 1:
            self.tab_income_list.export_to_excel()
        elif self.ui.tabWidget_income.currentIndex() == 2:
            self.tab_income_self_prescript.export_to_excel()

