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


# 掛號櫃台結帳 - 收費一覽表
class IncomeList(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(IncomeList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.tableWidget_registration = args[2]
        self.tableWidget_charge = args[3]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._merge_table_widgets()

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INCOME_LIST, self)
        self.table_widget_income = table_widget.TableWidget(self.ui.tableWidget_income, self.database)
        self.table_widget_income.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        pass
        #self.ui.tableWidget_income.doubleClicked.connect(self.open_medical_record)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [
            100, 120, 50, 70, 80, 50, 80, 90, 90, 50,
            70, 85, 85, 70, 70, 85, 85, 85, 85, 85,
            80, 80,
        ]
        self.table_widget_income.set_table_heading_width(width)

    def open_medical_record(self):
        case_key = self.table_widget_income.field_value(0)
        self.parent.open_medical_record(case_key, '病歷查詢')

    def _merge_table_widgets(self):
        self.ui.tableWidget_income.setRowCount(0)

        self._merge_table_registration()
        self._merge_table_charge()
        self._calculate_total_income()

    def _table_widget_income_patient_key_exists(self, patient_key):
        row_no_exists = None
        for row_no in range(self.ui.tableWidget_income.rowCount()):
            patient_key_item = self.ui.tableWidget_income.item(row_no, 3)
            if patient_key_item is not None and patient_key_item.text() == patient_key:
                row_no_exists = row_no
                break

        return row_no_exists

    def _merge_table_registration(self):
        for row_no in range(self.tableWidget_registration.rowCount()):
            patient_key = self.tableWidget_registration.item(row_no, 3).text()
            if patient_key == '':  # at end
                break

            row_no_exists = self._table_widget_income_patient_key_exists(patient_key)
            if row_no_exists is None:
                self._append_registration_item(row_no)
            else:
                self._insert_registration_item(row_no_exists, row_no)

    def _append_registration_item(self, registration_row_no):
        cell_data = [
            [0, self.tableWidget_registration.item(registration_row_no, 0)],
            [1, self.tableWidget_registration.item(registration_row_no, 1)],
            [2, self.tableWidget_registration.item(registration_row_no, 2)],
            [3, self.tableWidget_registration.item(registration_row_no, 3)],
            [4, self.tableWidget_registration.item(registration_row_no, 4)],
            [5, self.tableWidget_registration.item(registration_row_no, 5)],
            [6, self.tableWidget_registration.item(registration_row_no, 6)],
            [7, self.tableWidget_registration.item(registration_row_no, 7)],
            [8, self.tableWidget_registration.item(registration_row_no, 8)],

            [10, self.tableWidget_registration.item(registration_row_no, 9)],  # 掛號費
            [11, self.tableWidget_registration.item(registration_row_no, 10)], # 門診負擔
            [13, self.tableWidget_registration.item(registration_row_no, 11)], # 欠卡費
            [14, self.tableWidget_registration.item(registration_row_no, 12)], # 還卡費
            [15, self.tableWidget_registration.item(registration_row_no, 14)], # 自費還款
            [18, self.tableWidget_registration.item(registration_row_no, 13)], # 掛號欠款
            # [19, self.tableWidget_registration.item(registration_row_no, 15)],

        ]

        row_no = self.ui.tableWidget_income.rowCount()
        self.ui.tableWidget_income.setRowCount(row_no+1)
        for cell in cell_data:
            self.ui.tableWidget_income.setItem(
                row_no, cell[0],
                QtWidgets.QTableWidgetItem(cell[1])
            )

    def _insert_registration_item(self, income_row_no, registration_row_no):
        cell_data = [
            [0, self.tableWidget_registration.item(registration_row_no, 0)],
            [1, self.tableWidget_registration.item(registration_row_no, 1)],
            [2, self.tableWidget_registration.item(registration_row_no, 2)],
            [3, self.tableWidget_registration.item(registration_row_no, 3)],
            [4, self.tableWidget_registration.item(registration_row_no, 4)],
            [5, self.tableWidget_registration.item(registration_row_no, 5)],
            [6, self.tableWidget_registration.item(registration_row_no, 6)],
            [7, self.tableWidget_registration.item(registration_row_no, 7)],
            [8, self.tableWidget_registration.item(registration_row_no, 8)],

            [10, self.tableWidget_registration.item(registration_row_no, 9)],  # 掛號費
            [11, self.tableWidget_registration.item(registration_row_no, 10)], # 門診負擔
            [13, self.tableWidget_registration.item(registration_row_no, 11)], # 欠卡費
            [14, self.tableWidget_registration.item(registration_row_no, 12)], # 還卡費
            [15, self.tableWidget_registration.item(registration_row_no, 14)], # 自費還款
            [18, self.tableWidget_registration.item(registration_row_no, 13)], # 自費還款

        ]

        for cell in cell_data:
            if self.ui.tableWidget_income.item(income_row_no, cell[0]).text() != '':
                continue

            self.ui.tableWidget_income.setItem(
                income_row_no, cell[0],
                QtWidgets.QTableWidgetItem(cell[1])
            )

    def _merge_table_charge(self):
        for row_no in range(self.tableWidget_charge.rowCount()):
            patient_key = self.tableWidget_charge.item(row_no, 3).text()
            if patient_key == '':  # at end
                break

            row_no_exists = self._table_widget_income_patient_key_exists(patient_key)
            if row_no_exists is None:
                self._append_charge_item(row_no)
            else:
                self._insert_charge_item(row_no_exists, row_no)

    def _append_charge_item(self, charge_row_no):
        cell_data = [
            [0, self.tableWidget_charge.item(charge_row_no, 0)],
            [1, self.tableWidget_charge.item(charge_row_no, 1)],
            [2, self.tableWidget_charge.item(charge_row_no, 2)],
            [3, self.tableWidget_charge.item(charge_row_no, 3)],
            [4, self.tableWidget_charge.item(charge_row_no, 4)],
            [5, self.tableWidget_charge.item(charge_row_no, 5)],
            [6, self.tableWidget_charge.item(charge_row_no, 6)],
            [7, self.tableWidget_charge.item(charge_row_no, 7)],
            [8, self.tableWidget_charge.item(charge_row_no, 8)],
            [9, self.tableWidget_charge.item(charge_row_no, 9)],

            [12, self.tableWidget_charge.item(charge_row_no, 11)],
            [16, self.tableWidget_charge.item(charge_row_no, 12)],
            [17, self.tableWidget_charge.item(charge_row_no, 13)],
            #
            # [19, self.tableWidget_charge.item(charge_row_no, 15)],

        ]

        row_no = self.ui.tableWidget_income.rowCount()
        self.ui.tableWidget_income.setRowCount(row_no+1)
        for cell in cell_data:
            self.ui.tableWidget_income.setItem(
                row_no, cell[0],
                QtWidgets.QTableWidgetItem(cell[1])
            )

    def _insert_charge_item(self, income_row_no, charge_row_no):
        cell_data = [
            [0, self.tableWidget_charge.item(charge_row_no, 0)],
            [1, self.tableWidget_charge.item(charge_row_no, 1)],
            [2, self.tableWidget_charge.item(charge_row_no, 2)],
            [3, self.tableWidget_charge.item(charge_row_no, 3)],
            [4, self.tableWidget_charge.item(charge_row_no, 4)],
            [5, self.tableWidget_charge.item(charge_row_no, 5)],
            [6, self.tableWidget_charge.item(charge_row_no, 6)],
            [7, self.tableWidget_charge.item(charge_row_no, 7)],
            [8, self.tableWidget_charge.item(charge_row_no, 8)],
            [9, self.tableWidget_charge.item(charge_row_no, 9)],

            [12, self.tableWidget_charge.item(charge_row_no, 11)],
            [16, self.tableWidget_charge.item(charge_row_no, 12)],
            [17, self.tableWidget_charge.item(charge_row_no, 13)],
            #
            # [20, self.tableWidget_charge.item(charge_row_no, 15)],

        ]

        for cell in cell_data:
            if (self.ui.tableWidget_income.item(income_row_no, cell[0]) is not None and
                    self.ui.tableWidget_income.item(income_row_no, cell[0]).text() != ''):
                continue

            self.ui.tableWidget_income.setItem(
                income_row_no, cell[0],
                QtWidgets.QTableWidgetItem(cell[1])
            )

    def _calculate_total_income(self):
        self._calculate_subtotal()
        self._calculate_total()

    def _calculate_subtotal(self):
        row_count = self.ui.tableWidget_income.rowCount()
        for row_no in range(row_count):
            subtotal = 0
            for col_no in range(10, 19):
                cell = self.ui.tableWidget_income.item(row_no, col_no)
                if cell is None or cell.text() == '':
                    self.ui.tableWidget_income.setItem(
                        row_no, col_no,
                        QtWidgets.QTableWidgetItem('0')
                    )
                else:
                    subtotal += number_utils.get_integer(
                        cell.text()
                    )
                self.ui.tableWidget_income.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

            self.ui.tableWidget_income.setItem(
                row_no, 19,
                QtWidgets.QTableWidgetItem(string_utils.xstr(subtotal))
            )
            self.ui.tableWidget_income.item(
                row_no, 19).setTextAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )

    def _calculate_total(self):
        row_count = self.ui.tableWidget_income.rowCount()
        regist_fee, diag_share_fee, drug_share_fee, deposit_fee, refund_fee = 0, 0, 0, 0, 0
        repayment, total_fee, debt_fee, subtotal = 0, 0, 0, 0

        for row_no in range(row_count):
            regist_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 10).text())
            diag_share_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 11).text())
            drug_share_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 12).text())
            deposit_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 13).text())
            refund_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 14).text())
            repayment += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 15).text())
            total_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 16).text())
            debt_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 17).text())
            subtotal += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 18).text())

        total_record = [
            None, None, None, None,
            '合計',
            None, None, None, None, None,
            string_utils.xstr(regist_fee),
            string_utils.xstr(diag_share_fee),
            string_utils.xstr(drug_share_fee),
            string_utils.xstr(deposit_fee),
            string_utils.xstr(refund_fee),
            string_utils.xstr(repayment),
            string_utils.xstr(total_fee),
            string_utils.xstr(debt_fee),
            string_utils.xstr(subtotal),
        ]

        self.ui.tableWidget_income.setRowCount(row_count+1)

        font = QtGui.QFont()
        font.setBold(True)
        for col_no in range(len(total_record)):
            self.ui.tableWidget_income.setItem(
                row_count, col_no,
                QtWidgets.QTableWidgetItem(total_record[col_no])
            )
            if col_no in [10, 11, 12, 13, 14, 15, 16, 17, 18]:
                self.ui.tableWidget_income.item(
                    row_count, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            self.ui.tableWidget_income.item(row_count, col_no).setFont(font)

