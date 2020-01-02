#!/usr/bin/env python3
# 掛號櫃台結帳 2018.11.15
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
import datetime

from classes import table_widget
from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import massage_utils
from libs import nhi_utils
from dialog import dialog_massage_reservation


# 養生館櫃台結帳
class MassageIncomeCashFlow(QtWidgets.QMainWindow):
    program_name = '養生館櫃台結帳'

    # 初始化
    def __init__(self, parent=None, *args):
        super(MassageIncomeCashFlow, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.period = args[4]
        self.massager = args[5]
        self.cashier = args[6]
        self.ui = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()

        self.read_data()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_income(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MASSAGE_INCOME_CASH_FLOW, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_massage = table_widget.TableWidget(self.ui.tableWidget_massage, self.database)
        self.table_widget_massage.set_column_hidden([0])
        self.table_widget_purchase = table_widget.TableWidget(self.ui.tableWidget_purchase, self.database)
        self.table_widget_purchase.set_column_hidden([0])
        self.table_widget_total = table_widget.TableWidget(self.ui.tableWidget_total, self.database)
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_massage.doubleClicked.connect(self.open_massage_record)
        self.ui.tableWidget_purchase.doubleClicked.connect(self.open_massage_record)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

    # 設定欄位寬度
    def _set_table_width(self):
        width = [
            100,
            110, 50, 130, 80, 100, 300, 90, 90, 100, 100, 180,
        ]
        self.table_widget_massage.set_table_heading_width(width)

        width = [
            100,
            110, 50, 80, 100, 430, 90, 90, 100, 100, 180,
        ]
        self.table_widget_purchase.set_table_heading_width(width)
        self.table_widget_total.set_table_heading_width([160, 100])

    def open_massage_record(self):
        sender_name = self.sender().objectName()

        if sender_name == 'tableWidget_massage':
            massage_case_key = self.table_widget_massage.field_value(0)
        elif sender_name == 'tableWidget_purchase':
            massage_case_key = self.table_widget_purchase.field_value(0)
        else:
            return

        if massage_case_key in ['', None]:
            return

        if sender_name == 'tableWidget_purchase':
            self.parent.parent.open_massage_purchase_tab('養生館櫃台結帳', massage_case_key)
            return

        dialog = dialog_massage_reservation.DialogMassageReservation(
            self, self.database, self.system_settings,
            None, None, None, None, None,
            massage_case_key,
        )

        try:
            dialog.exec_()
        finally:
            dialog.close_all()
            dialog.deleteLater()

        self.parent.refresh_massage_case()

    # 開始統計現金交帳
    def read_data(self):
        self._read_massage_data()
        self._read_purchase_data()
        self._calculate_total()

    # 計算掛號收費
    def _read_massage_data(self):
        self._set_massage_data()
        self._calculate_massage_total()

    def _set_massage_data(self):
        sql = '''
            SELECT * FROM massage_cases
            WHERE 
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                (InsType = "自費") AND
                (TreatType = "養生館")
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
        )

        if self.period != '全部':
            sql += ' AND Period = "{0}"'.format(self.period)
        if self.massager != '全部':
            sql += ' AND Massager = "{0}"'.format(self.massager)
        if self.cashier != '全部':
            sql += ' AND Registrar = "{0}"'.format(self.cashier)

        sql += ' ORDER BY CaseDate, FIELD(Period, {0})'.format(
            string_utils.xstr(nhi_utils.PERIOD)[1:-1])

        self.table_widget_massage.set_db_data(sql, self._set_massage_table_data)

    def _set_massage_table_data(self, row_no, row):
        massage_case_key = number_utils.get_integer(row['MassageCaseKey'])
        massage_time = '{start_time} - {end_time}'.format(
            start_time= row['CaseDate'].strftime('%H:%M'),
            end_time=row['FinishDate'].strftime('%H:%M'),
        )
        massage_item = massage_utils.get_massage_prescript_item(self.database, massage_case_key)

        massage_row = [
            string_utils.xstr(massage_case_key),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['Period']),
            massage_time,
            string_utils.xstr(row['MassageCustomerKey']),
            string_utils.xstr(row['Name']),
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
            self.ui.tableWidget_massage.setItem(row_no, col_no, item)
            if col_no in [4, 7, 8]:
                self.ui.tableWidget_massage.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2]:
                self.ui.tableWidget_massage.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _calculate_massage_total(self):
        row_count = self.ui.tableWidget_massage.rowCount()

        total_fee, receipt_fee = 0, 0
        for row_no in range(row_count):
            total_fee += number_utils.get_integer(self.ui.tableWidget_massage.item(row_no, 7).text())
            receipt_fee += number_utils.get_integer(self.ui.tableWidget_massage.item(row_no, 8).text())

        total_row = [
            None, None, None, None, None,
            '合計',
            None,
            total_fee,
            receipt_fee,
        ]

        self.ui.tableWidget_massage.setRowCount(row_count+1)

        font = QtGui.QFont()
        font.setBold(True)
        for col_no in range(len(total_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, total_row[col_no])
            self.ui.tableWidget_massage.setItem(row_count, col_no, item)
            if col_no in [7, 8]:
                self.ui.tableWidget_massage.item(
                    row_count, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            self.ui.tableWidget_massage.item(row_count, col_no).setFont(font)

    # 計算批價收費
    def _read_purchase_data(self):
        self._set_purchase_data()
        self._calculate_purchase_total()

    def _set_purchase_data(self):
        sql = '''
            SELECT * FROM massage_cases
            WHERE 
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                (InsType = "自費") AND
                (TreatType = "購買商品")
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
        )

        if self.period != '全部':
            sql += ' AND Period = "{0}"'.format(self.period)
        if self.massager != '全部':
            sql += ' AND Massager = "{0}"'.format(self.massager)
        if self.cashier != '全部':
            sql += ' AND Cashier = "{0}"'.format(self.cashier)

        sql += ' ORDER BY CaseDate, FIELD(Period, {0})'.format(
            string_utils.xstr(nhi_utils.PERIOD)[1:-1])

        self.table_widget_purchase.set_db_data(sql, self._set_purchase_table_data)

    def _set_purchase_table_data(self, row_no, row):
        massage_case_key = number_utils.get_integer(row['MassageCaseKey'])
        massage_item = massage_utils.get_massage_prescript_item(self.database, massage_case_key)

        massage_row = [
            string_utils.xstr(massage_case_key),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['MassageCustomerKey']),
            string_utils.xstr(row['Name']),
            massage_item,
            row['TotalFee'],
            row['ReceiptFee'],
            string_utils.xstr(row['Massager']),
            string_utils.xstr(row['Cashier']),
            string_utils.xstr(row['Remark']),
        ]

        for col_no in range(len(massage_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, massage_row[col_no])
            self.ui.tableWidget_purchase.setItem(row_no, col_no, item)
            if col_no in [3, 6, 7]:
                self.ui.tableWidget_purchase.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2]:
                self.ui.tableWidget_purchase.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _calculate_purchase_total(self):
        row_count = self.ui.tableWidget_purchase.rowCount()
        total_fee, receipt_fee = 0, 0
        for row_no in range(row_count):
            total_fee += number_utils.get_integer(self.ui.tableWidget_purchase.item(row_no, 6).text())
            receipt_fee += number_utils.get_integer(self.ui.tableWidget_purchase.item(row_no, 7).text())

        total_row = [
            None, None, None, None,
            '合計',
            None,
            total_fee,
            receipt_fee,
        ]

        self.ui.tableWidget_purchase.setRowCount(row_count+1)

        font = QtGui.QFont()
        font.setBold(True)
        for col_no in range(len(total_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, total_row[col_no])
            self.ui.tableWidget_purchase.setItem(row_count, col_no, item)
            if col_no in [6, 7]:
                self.ui.tableWidget_purchase.item(
                    row_count, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            self.ui.tableWidget_purchase.item(row_count, col_no).setFont(font)

    def _get_payment(self, payment_item):
        sql = '''
            SELECT Amount FROM massage_payment
                LEFT JOIN massage_cases ON massage_cases.MassageCaseKey = massage_payment.MassageCaseKey
            WHERE 
                massage_cases.CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                massage_cases.InsType = "自費" AND
                PaymentType = "{payment_item}"
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            payment_item=payment_item,
        )

        if self.period != '全部':
            sql += ' AND Period = "{0}"'.format(self.period)
        if self.massager != '全部':
            sql += ' AND Massager = "{0}"'.format(self.massager)
        if self.cashier != '全部':
            sql += ' AND Registrar = "{0}"'.format(self.cashier)

        sql += ' ORDER BY CaseDate, FIELD(Period, {0})'.format(
            string_utils.xstr(nhi_utils.PERIOD)[1:-1])

        rows = self.database.select_record(sql)

        amount = 0
        for row in rows:
            amount += number_utils.get_integer(row['Amount'])

        return amount

    def _calculate_total(self):
        self.ui.tableWidget_total.setRowCount(0)

        total_fee = (
                number_utils.get_integer(self.ui.tableWidget_massage.item(
                    self.ui.tableWidget_massage.rowCount()-1, 7).text()) +
                number_utils.get_integer(self.ui.tableWidget_purchase.item(
                    self.ui.tableWidget_purchase.rowCount()-1, 6).text())
        )

        total_row = [
            ['應收金額', total_fee],
        ]
        receipt_fee = 0
        for payment_item in massage_utils.PAYMENT_ITEMS:
            amount = self._get_payment(payment_item)
            receipt_fee += amount
            total_row.append([payment_item, amount])

        total_row.append(['實收金額', receipt_fee])

        font = QtGui.QFont()
        font.setBold(True)
        for row_no, row in zip(range(len(total_row)), total_row):
            self.ui.tableWidget_total.setRowCount(row_no+1)
            for col_no in range(len(row)):
                item = QtWidgets.QTableWidgetItem()
                item.setData(QtCore.Qt.EditRole, row[col_no])
                self.ui.tableWidget_total.setItem(row_no, col_no, item)
                if col_no in [1]:
                    self.ui.tableWidget_total.item(
                        row_no, col_no).setTextAlignment(
                        QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                    )

        for row_no in range(self.ui.tableWidget_total.rowCount()):
            payment_item = self.ui.tableWidget_total.item(row_no, 0).text()
            if payment_item in ['應收金額', '實收金額']:
                self.ui.tableWidget_total.item(row_no, 0).setFont(font)
                self.ui.tableWidget_total.item(row_no, 1).setFont(font)

