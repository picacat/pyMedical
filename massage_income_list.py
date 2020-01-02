#!/usr/bin/env python3
# 掛號櫃台結帳 2018.11.15
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import nhi_utils
from libs import system_utils
from libs import export_utils
from libs import massage_utils


def _get_payment(payment_rows, payment_item):
    amount = 0
    for row in payment_rows:
        if payment_item == string_utils.xstr(row['PaymentType']):
            amount = number_utils.get_integer(row['Amount'])
            break

    return amount


# 養生館櫃台結帳 - 收費一覽表
class MassageIncomeList(QtWidgets.QMainWindow):
    program_name = '養生館櫃台結帳'

    # 初始化
    def __init__(self, parent=None, *args):
        super(MassageIncomeList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.period = args[4]
        self.massager = args[5]
        self.cashier = args[5]
        self.ui = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()
        self.read_massage_data()

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MASSAGE_INCOME_LIST, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_income = table_widget.TableWidget(self.ui.tableWidget_income, self.database)
        self.table_widget_income.set_column_hidden([0])
        self._set_payment_columns()
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_income.doubleClicked.connect(self.open_medical_record)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

    def _set_payment_columns(self):
        header_item = [
            'massage_case_key',
            '消費日期', '班別', '顧客編號', '姓名', '消費類別', '應收金額', '實收金額',
        ]
        header_item += massage_utils.PAYMENT_ITEMS

        self.ui.tableWidget_income.setColumnCount(len(header_item))
        for col_no in range(len(header_item)):
            self.ui.tableWidget_income.setHorizontalHeaderItem(
                col_no, QtWidgets.QTableWidgetItem(header_item[col_no])
            )

    # 設定欄位寬度
    def _set_table_width(self):
        width = [
            100, 110, 50, 90, 100, 100, 100, 100,
        ]
        width += [100 for i in range(len(massage_utils.PAYMENT_ITEMS))]

        self.table_widget_income.set_table_heading_width(width)

    def open_medical_record(self):
        pass

    def _get_payment_rows(self, massage_case_key):
        sql = '''
            SELECT * FROM massage_payment
            WHERE
                MassageCaseKey = {massage_case_key}
        '''.format(
            massage_case_key=massage_case_key,
        )
        rows = self.database.select_record(sql)

        return rows

    def read_massage_data(self):
        sql = '''
            SELECT * FROM massage_cases
            WHERE 
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                (InsType = "自費")
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

        self.table_widget_income.set_db_data(sql, self._set_massage_table_data)

        self._calculate_total()

    def _set_massage_table_data(self, row_no, row):
        massage_case_key = number_utils.get_integer(row['MassageCaseKey'])

        payment_rows = self._get_payment_rows(massage_case_key)
        payment_row = []
        for i in range(len(massage_utils.PAYMENT_ITEMS)):
            item = massage_utils.PAYMENT_ITEMS[i]
            payment = _get_payment(payment_rows, item)
            payment_row.append(payment)

        massage_row = [
            string_utils.xstr(massage_case_key),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['MassageCustomerKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['TreatType']),
            number_utils.get_integer(row['TotalFee']),
            number_utils.get_integer(row['ReceiptFee']),
        ]
        massage_row += payment_row

        for col_no in range(len(massage_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, massage_row[col_no])
            self.ui.tableWidget_income.setItem(row_no, col_no, item)
            if col_no in [2]:
                self.ui.tableWidget_income.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            elif col_no not in [1, 4, 5]:
                self.ui.tableWidget_income.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _calculate_total(self):
        row_count = self.ui.tableWidget_income.rowCount()

        total_fee, receipt_fee = 0, 0
        payment_list = [0 for i in range(len(massage_utils.PAYMENT_ITEMS))]
        start_col = 8
        for row_no in range(row_count):
            total_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 6).text())
            receipt_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 7).text())
            for col_no in range(start_col, len(payment_list) + start_col):
                payment_list[col_no-start_col] += \
                    number_utils.get_integer(self.ui.tableWidget_income.item(row_no, col_no).text())

        total_row = [
            None, None, None, None, None,
            '合計',
            total_fee,
            receipt_fee,
        ] + payment_list

        self.ui.tableWidget_income.setRowCount(row_count + 1)

        font = QtGui.QFont()
        font.setBold(True)
        for col_no in range(len(total_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, total_row[col_no])
            self.ui.tableWidget_income.setItem(row_count, col_no, item)
            if col_no not in [1, 4, 5]:
                self.ui.tableWidget_income.item(
                    row_count, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            self.ui.tableWidget_income.item(row_count, col_no).setFont(font)

    def export_to_excel(self):
        if self.ui.tableWidget_income.rowCount() <= 0:
            return

        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出日報表",
            '{0}至{1}日報表.xlsx'.format(
                self.start_date[:10], self.end_date[:10]
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        fields = [3, 6, 7]
        for i in range(len(massage_utils.PAYMENT_ITEMS)):
            fields.append(fields[-1]+1)

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_income, [0], fields
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>日報表{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

