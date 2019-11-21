#!/usr/bin/env python3
# 掛號櫃台結帳 2018.11.15
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import personnel_utils
from libs import system_utils
from libs import export_utils


# 掛號櫃台結帳 - 收費一覽表
class IncomeList(QtWidgets.QMainWindow):
    program_name = '掛號櫃台結帳'

    # 初始化
    def __init__(self, parent=None, *args):
        super(IncomeList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.period = args[4]
        self.doctor = args[5]
        self.tableWidget_registration = args[6]
        self.tableWidget_charge = args[7]
        self.ui = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()

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
        system_utils.set_css(self, self.system_settings)
        self.table_widget_income = table_widget.TableWidget(self.ui.tableWidget_income, self.database)
        self.table_widget_income.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_income.doubleClicked.connect(self.open_medical_record)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

    # 設定欄位寬度
    def _set_table_width(self):
        width = [
            100, 110, 45, 70, 80, 45, 80, 80, 80, 70, 50,
            70, 80, 80, 70, 70, 80, 80, 80, 80, 80,
            80, 80,
        ]
        self.table_widget_income.set_table_heading_width(width)

    def open_medical_record(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, self.program_name, '進入病歷', self.user_name) != 'Y'):
            return

        case_key = self.table_widget_income.field_value(0)
        self.parent.open_medical_record(case_key, '病歷查詢')

    def _merge_table_widgets(self):
        self.ui.tableWidget_income.setRowCount(0)

        self._merge_table_registration()
        self._merge_table_charge()
        self._calculate_total_income()

    def _table_widget_income_patient_key_exists(self, patient_key, name, ins_type):
        row_no_exists = None
        for row_no in range(self.ui.tableWidget_income.rowCount()):
            patient_key_item = self.ui.tableWidget_income.item(row_no, 3)
            name_item = self.ui.tableWidget_income.item(row_no, 4)
            ins_type_item = self.ui.tableWidget_income.item(row_no, 5)
            if (patient_key_item is not None and patient_key_item.text() == patient_key and
                    name_item is not None and name_item.text() == name and
                    ins_type_item is not None and ins_type_item.text() == ins_type):
                row_no_exists = row_no
                break

        return row_no_exists

    def _merge_table_registration(self):
        for row_no in range(self.tableWidget_registration.rowCount()):
            patient_key = self.tableWidget_registration.item(row_no, 3).text()
            name = self.tableWidget_registration.item(row_no, 4).text()
            ins_type = self.tableWidget_registration.item(row_no, 5).text()
            if patient_key == '':  # at end
                break

            row_no_exists = self._table_widget_income_patient_key_exists(patient_key, name, ins_type)
            if row_no_exists is None:  # 不存在
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
            [7, self.tableWidget_registration.item(registration_row_no, 7)],    # 負擔類別
            [8, self.tableWidget_registration.item(registration_row_no, 8)],    # 優待類別

            [9, self.tableWidget_registration.item(registration_row_no, 9)],    # 卡序

            [11, self.tableWidget_registration.item(registration_row_no, 10)],  # 掛號費
            [12, self.tableWidget_registration.item(registration_row_no, 11)],  # 門診負擔
            [14, self.tableWidget_registration.item(registration_row_no, 12)],  # 欠卡費
            [15, self.tableWidget_registration.item(registration_row_no, 13)],  # 還卡費
            [16, self.tableWidget_registration.item(registration_row_no, 15)],  # 自費還款
            [19, self.tableWidget_registration.item(registration_row_no, 14)],  # 掛號欠款

            [21, self.tableWidget_registration.item(registration_row_no, 17)],  # 掛號者
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
            [7, self.tableWidget_registration.item(registration_row_no, 7)],    # 負擔類別
            [8, self.tableWidget_registration.item(registration_row_no, 8)],    # 優待類別

            [9, self.tableWidget_registration.item(registration_row_no, 8)],    # 卡序

            [11, self.tableWidget_registration.item(registration_row_no, 10)],  # 掛號費
            [12, self.tableWidget_registration.item(registration_row_no, 11)],  # 門診負擔
            [14, self.tableWidget_registration.item(registration_row_no, 12)],  # 欠卡費
            [15, self.tableWidget_registration.item(registration_row_no, 13)],  # 還卡費
            [16, self.tableWidget_registration.item(registration_row_no, 15)],  # 自費還款
            [19, self.tableWidget_registration.item(registration_row_no, 14)],  # 掛號欠款

            [21, self.tableWidget_registration.item(registration_row_no, 17)], # 掛號者

        ]

        for cell in cell_data:
            if self.ui.tableWidget_income.item(income_row_no, cell[0]).text() != '0':
                continue

            self.ui.tableWidget_income.setItem(
                income_row_no, cell[0],
                QtWidgets.QTableWidgetItem(cell[1])
            )

    def _merge_table_charge(self):
        for row_no in range(self.tableWidget_charge.rowCount()):
            patient_key = self.tableWidget_charge.item(row_no, 3).text()
            name = self.tableWidget_charge.item(row_no, 4).text()
            ins_type = self.tableWidget_charge.item(row_no, 5).text()
            if patient_key == '':  # at end
                break

            row_no_exists = self._table_widget_income_patient_key_exists(patient_key, name, ins_type)
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
            [7, self.tableWidget_charge.item(charge_row_no, 7)],    # 負擔類別
            [8, self.tableWidget_charge.item(charge_row_no, 8)],    # 優待類別

            [9, self.tableWidget_charge.item(charge_row_no, 9)],    # 卡序
            [10, self.tableWidget_charge.item(charge_row_no, 10)],   # 藥日

            [13, self.tableWidget_charge.item(charge_row_no, 12)],  # 藥品負擔
            [17, self.tableWidget_charge.item(charge_row_no, 13)],  # 自費應收
            [18, self.tableWidget_charge.item(charge_row_no, 15)],  # 自費欠款
            [20, self.tableWidget_charge.item(charge_row_no, 16)],  # 實收現金

            [22, self.tableWidget_charge.item(charge_row_no, 17)],  # 批價員
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
            [7, self.tableWidget_charge.item(charge_row_no, 7)],    # 負擔類別
            [8, self.tableWidget_charge.item(charge_row_no, 8)],    # 優待類別

            [9, self.tableWidget_charge.item(charge_row_no, 9)],    # 卡序
            [10, self.tableWidget_charge.item(charge_row_no, 10)],   # 藥日

            [13, self.tableWidget_charge.item(charge_row_no, 12)],  # 藥品負擔
            [17, self.tableWidget_charge.item(charge_row_no, 13)],  # 自費應收
            [18, self.tableWidget_charge.item(charge_row_no, 15)],  # 自費欠款
            [20, self.tableWidget_charge.item(charge_row_no, 16)],  # 實收現金

            [22, self.tableWidget_charge.item(charge_row_no, 17)],  # 批價員
        ]

        for cell in cell_data:
            if (self.ui.tableWidget_income.item(income_row_no, cell[0]) is not None and
                    self.ui.tableWidget_income.item(income_row_no, cell[0]).text() != ''):
                if cell[0] == 17:
                    fee = number_utils.get_integer(
                        self.ui.tableWidget_income.item(income_row_no, cell[0]).text()
                    )
                    fee += number_utils.get_integer(cell[1].text())
                    self.ui.tableWidget_income.setItem(
                        income_row_no, cell[0],
                        QtWidgets.QTableWidgetItem(string_utils.xstr(fee))
                    )
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
            for col_no in range(11, 20):
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
                row_no, 20,
                QtWidgets.QTableWidgetItem(string_utils.xstr(subtotal))
            )
            self.ui.tableWidget_income.item(
                row_no, 20).setTextAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )

    def _calculate_total(self):
        row_count = self.ui.tableWidget_income.rowCount()
        regist_fee, diag_share_fee, drug_share_fee, deposit_fee, refund_fee = 0, 0, 0, 0, 0
        repayment, total_fee, debt_fee, regist_debt, subtotal = 0, 0, 0, 0, 0

        for row_no in range(row_count):
            regist_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 11).text())
            diag_share_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 12).text())
            drug_share_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 13).text())
            deposit_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 14).text())
            refund_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 15).text())
            repayment += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 16).text())
            total_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 17).text())
            debt_fee += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 18).text())
            regist_debt += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 19).text())
            subtotal += number_utils.get_integer(self.ui.tableWidget_income.item(row_no, 20).text())

        total_record = [
            None, None, None, None,
            '合計',
            None, None, None, None, None, None,
            string_utils.xstr(regist_fee),
            string_utils.xstr(diag_share_fee),
            string_utils.xstr(drug_share_fee),
            string_utils.xstr(deposit_fee),
            string_utils.xstr(refund_fee),
            string_utils.xstr(repayment),
            string_utils.xstr(total_fee),
            string_utils.xstr(debt_fee),
            string_utils.xstr(regist_debt),
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
            if col_no in [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
                self.ui.tableWidget_income.item(
                    row_count, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            self.ui.tableWidget_income.item(row_count, col_no).setFont(font)

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出日報表",
            '{0}至{1}{2}醫師門診日報表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.doctor
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_income, [0], [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>醫師門診日報表{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

