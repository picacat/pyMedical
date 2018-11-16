#!/usr/bin/env python3
# 掛號櫃台結帳 2018.11.15
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
import sys

from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import case_utils
from dialog import dialog_income
from classes import table_widget


# 主視窗
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

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INCOME, self)
        self.table_widget_income = table_widget.TableWidget(self.ui.tableWidget_income, self.database)
        self.table_widget_income.set_column_hidden([0])
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_income)
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_open_medical_record.triggered.connect(self.open_medical_record)
        # self.ui.action_open_record.triggered.connect(self.open_medical_record)
        # self.ui.tableWidget_patient_list.doubleClicked.connect(self.open_medical_record)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 100, 40, 120, 120, 60, 80, 80, 180, 120, 120, 120, 400]
        self.table_widget_income.set_table_heading_width(width)

    # 讀取病歷
    def _get_sql(self):
        dialog = dialog_income.DialogIncome(self.ui, self.database, self.system_settings)
        result = dialog.exec_()
        sql = dialog.get_sql()
        dialog.close_all()
        dialog.deleteLater()

        if result == 0:
            return None
        else:
            return sql

    def open_dialog(self):
        sql = self._get_sql()
        if sql is None:
            return

        self.table_widget_income.set_db_data(sql, self._set_table_data)
        self._calculate_total()

    def _set_table_data(self, rec_no, rec):
        case_key = number_utils.get_integer(rec['CaseKey'])
        pres_days = case_utils.get_pres_days(self.database, case_key)

        regist_fee = number_utils.get_integer(rec['RegistFee'])
        diag_share_fee = number_utils.get_integer(rec['SDiagShareFee'])
        drug_share_fee = number_utils.get_integer(rec['SDrugShareFee'])
        deposit_fee = number_utils.get_integer(rec['DepositFee'])
        refund = number_utils.get_integer(rec['RefundFee'])
        debt = number_utils.get_integer(rec['DebtFee'])
        pay_back = number_utils.get_integer(rec['Fee1'])
        total_fee = number_utils.get_integer(rec['TotalFee'])

        if rec['ReturnDate'] is not None and rec['ReturnDate'].date() == rec['CaseDate'].date():
            pass
        elif string_utils.xstr(rec['ReturnDate']) != '':
            regist_fee = 0
            diag_share_fee = 0
            drug_share_fee = 0
            deposit_fee = 0
            total_fee = 0
        else:
            refund = 0

        if rec['ReturnDate1'] is not None and rec['ReturnDate1'].date() == rec['CaseDate'].date():
            pass
        elif string_utils.xstr(rec['ReturnDate1']) != '':
            regist_fee = 0
            diag_share_fee = 0
            drug_share_fee = 0
            debt = 0
            total_fee = 0
        else:
            pay_back = 0

        amount = regist_fee + diag_share_fee + drug_share_fee + deposit_fee + pay_back + total_fee
        receipt_fee = amount - refund - debt

        medical_record = [
            string_utils.xstr(case_key),
            string_utils.xstr(rec['CaseDate'].date()),
            string_utils.xstr(rec['Period']),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['InsType']),
            string_utils.xstr(rec['Share']),
            string_utils.xstr(rec['Card']),
            string_utils.xstr(rec['Continuance']),
            string_utils.xstr(pres_days),
            string_utils.xstr(rec['Doctor']),
            string_utils.xstr(regist_fee),
            string_utils.xstr(diag_share_fee),
            string_utils.xstr(drug_share_fee),
            string_utils.xstr(deposit_fee),
            string_utils.xstr(refund),
            string_utils.xstr(debt),
            string_utils.xstr(pay_back),
            string_utils.xstr(total_fee),
            string_utils.xstr(receipt_fee),
            string_utils.xstr(rec['Register']),
            string_utils.xstr(rec['Cashier']),
        ]

        for column in range(len(medical_record)):
            self.ui.tableWidget_income.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(medical_record[column])
            )
            if column in [3, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19]:
                self.ui.tableWidget_income.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [5, 8]:
                self.ui.tableWidget_income.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if column in [15, 16]:
                self.ui.tableWidget_income.item(
                    rec_no, column).setForeground(
                    QtGui.QColor('red')
                )

            if column in [19] and receipt_fee < 0:
                self.ui.tableWidget_income.item(
                    rec_no, column).setForeground(
                    QtGui.QColor('red')
                )

    def _calculate_total(self):
        row_count = self.ui.tableWidget_income.rowCount()
        regist_fee, diag_share_fee, drug_share_fee = 0, 0, 0
        deposit_fee, refund, debt, pay_back = 0, 0, 0, 0
        total_fee, receipt_fee = 0, 0
        for row_no in range(row_count):
            regist_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 11).text())
            diag_share_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 12).text())
            drug_share_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 13).text())
            deposit_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 14).text())
            refund += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 15).text())
            debt += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 16).text())
            pay_back += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 17).text())
            total_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 18).text())
            receipt_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 19).text())

        total_record = [
            None,
            '合計',
            None, None, None, None, None, None, None, None, None,
            string_utils.xstr(regist_fee),
            string_utils.xstr(diag_share_fee),
            string_utils.xstr(drug_share_fee),
            string_utils.xstr(deposit_fee),
            string_utils.xstr(refund),
            string_utils.xstr(debt),
            string_utils.xstr(pay_back),
            string_utils.xstr(total_fee),
            string_utils.xstr(receipt_fee),
        ]

        self.ui.tableWidget_income.setRowCount(row_count+1)

        font = QtGui.QFont()
        font.setBold(True)
        for column in range(len(total_record)):
            self.ui.tableWidget_income.setItem(
                row_count, column,
                QtWidgets.QTableWidgetItem(total_record[column])
            )
            if column in [11, 12, 13, 14, 15, 16, 17, 18, 19]:
                self.ui.tableWidget_income.item(
                    row_count, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            self.ui.tableWidget_income.item(row_count, column).setFont(font)

    def open_medical_record(self):
        case_key = self.table_widget_income.field_value(0)
        self.parent.open_medical_record(case_key, '病歷查詢')

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_income(self):
        self.close_all()
        self.close_tab()
