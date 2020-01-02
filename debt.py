#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox

from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import personnel_utils
from libs import dialog_utils
from dialog import dialog_debt
from classes import table_widget


# 欠還款作業
class Debt(QtWidgets.QMainWindow):
    program_name = '欠還款作業'

    # 初始化
    def __init__(self, parent=None, *args):
        super(Debt, self).__init__(parent)
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

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DEBT, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_debt = table_widget.TableWidget(self.ui.tableWidget_debt, self.database)
        self.table_widget_debt.set_column_hidden([0, 1])
        # database._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_debt)
        self.ui.action_pay_back.triggered.connect(self.pay_back)
        self.ui.action_remove_debt.triggered.connect(self._remove_debt)
        self.ui.tableWidget_debt.itemSelectionChanged.connect(self._debt_item_selection_changed)
        self.ui.action_open_medical_record.triggered.connect(self.open_medical_record)
        self.ui.tableWidget_debt.doubleClicked.connect(self.open_medical_record)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, self.program_name, '現金還款', self.user_name) != 'Y':
            self.ui.action_pay_back.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '調閱病歷', self.user_name) != 'Y':
            self.ui.action_open_medical_record.setEnabled(False)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 100, 40, 120, 100, 120, 60, 80, 80, 180, 120, 120, 120, 400]
        self.table_widget_income.set_table_heading_width(width)

    def read_debt(self):
        sql = '''
            SELECT * FROM debt
            ORDER BY TotalReturn, CaseDate DESC
        '''

        self.table_widget_debt.set_db_data(sql, self._set_table_data)
        self._set_tool_button()

    def _set_tool_button(self):
        if self.ui.tableWidget_debt.rowCount() <= 0:
            enabled = False
        else:
            enabled = True

        self.ui.action_open_medical_record.setEnabled(enabled)
        self.ui.action_pay_back.setEnabled(enabled)
        self.ui.action_remove_debt.setEnabled(enabled)

        self._set_permission()

    def _set_table_data(self, rec_no, rec):
        case_key = number_utils.get_integer(rec['CaseKey'])
        if rec['ReturnDate1'] is not None:
            return_date = rec['ReturnDate1'].date()
        else:
            return_date = None

        medical_record = [
            string_utils.xstr(rec['DebtKey']),
            string_utils.xstr(case_key),
            string_utils.xstr(rec['CaseDate'].date()),
            string_utils.xstr(rec['Period']),
            string_utils.xstr(rec['DebtType']),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Fee']),
            string_utils.xstr(return_date),
            string_utils.xstr(rec['Period1']),
            string_utils.xstr(rec['Fee1']),
            string_utils.xstr(rec['Cashier1']),
        ]

        for column in range(len(medical_record)):
            self.ui.tableWidget_debt.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(medical_record[column])
            )
            if column in [5, 7]:
                self.ui.tableWidget_debt.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [3]:
                self.ui.tableWidget_debt.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def pay_back(self):
        debt_key = self.table_widget_debt.field_value(0)
        case_key = self.table_widget_debt.field_value(1)

        dialog = dialog_debt.DialogDebt(
            self, self.database, self.system_settings,
            debt_key, case_key,
        )
        if dialog.exec_():
            self.refresh_record(debt_key)

        dialog.deleteLater()

    def refresh_record(self, debt_key):
        sql = '''
            SELECT * FROM debt
            WHERE 
                DebtKey = {0}
        '''.format(debt_key)
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            self._set_table_data(self.ui.tableWidget_debt.currentRow(), rows[0])

    def open_medical_record(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, self.program_name, '調閱病歷', self.user_name) != 'Y'):
            return

        case_key = self.table_widget_debt.field_value(1)
        self.parent.open_medical_record(case_key, '病歷查詢')

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_debt(self):
        self.close_all()
        self.close_tab()

    def _debt_item_selection_changed(self):
        self._set_tool_button()

    def _remove_debt(self):
        msg_box = dialog_utils.get_message_box(
            '刪除欠款資料', QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除此筆欠款資料?</b></font>',
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_debt.field_value(0)
        self.database.delete_record('debt', 'DebtKey', key)
        self.ui.tableWidget_debt.removeRow(self.ui.tableWidget_debt.currentRow())
