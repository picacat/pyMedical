#!/usr/bin/env python3
# 櫃台購藥 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime

from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import personnel_utils
from dialog import dialog_purchase_list
from classes import table_widget
from printer import print_receipt


# 櫃台購藥
class PurchaseList(QtWidgets.QMainWindow):
    program_name = '櫃台購藥'

    # 初始化
    def __init__(self, parent=None, *args):
        super(PurchaseList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()

        self.read_purchase_today()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_PURCHASE_LIST, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_purchase_list = table_widget.TableWidget(self.ui.tableWidget_purchase_list, self.database)
        self._set_table_width()
        self._set_tool_button()

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_purchase.triggered.connect(self._purchase)
        self.ui.action_delete_record.triggered.connect(self.delete_purchase)
        self.ui.action_open_record.triggered.connect(self.open_medical_record)
        self.ui.action_close.triggered.connect(self.close_purchase_list)
        self.ui.action_print_receipt.triggered.connect(self._print_receipt)
        self.ui.action_print_purchase_list.triggered.connect(self._print_purchase_list)
        self.ui.tableWidget_purchase_list.doubleClicked.connect(self.open_medical_record)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, self.program_name, '購買商品', self.user_name) != 'Y':
            self.ui.action_purchase.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '購藥明細', self.user_name) != 'Y':
            self.ui.action_open_record.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '資料刪除', self.user_name) != 'Y':
            self.ui.action_delete_record.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '列印名單', self.user_name) != 'Y':
            self.ui.action_print_purchase_list.setEnabled(False)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 200, 60, 100, 120, 100, 100, 100, 800]
        self.table_widget_purchase_list.set_table_heading_width(width)
        self.table_widget_purchase_list.set_column_hidden([0])

    # 讀取病歷
    def _get_sql(self):
        dialog = dialog_purchase_list.DialogPurchaseList(self.ui, self.database, self.system_settings)
        result = dialog.exec_()

        sql = dialog.get_sql()
        start_date = dialog.ui.dateEdit_start_date.date().toString('yyyy-MM-dd')
        end_date = dialog.ui.dateEdit_end_date.date().toString('yyyy-MM-dd')

        dialog.close_all()
        dialog.deleteLater()

        if result == 0:
            return None, None, None
        else:
            return sql, start_date, end_date

    def open_dialog(self):
        sql, start_date, end_date = self._get_sql()
        if sql is None:
            return

        self.ui.label_data_period.setText('資料期間: {0} 至 {1}'.format(start_date, end_date))
        self.table_widget_purchase_list.set_db_data(sql, self._set_table_data)
        self._set_tool_button()

    def read_purchase_today(self):
        start_date = datetime.datetime.now().strftime('%Y-%m-%d')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.ui.label_data_period.setText('資料期間: {0} 至 {1}'.format(start_date, end_date))

        start_date += ' 00:00:00'
        end_date += ' 23:59:59'

        sql = '''
            SELECT * FROM cases
            WHERE
                CaseDate BETWEEN "{0}" AND "{1}" AND
                TreatType = "自購"
            ORDER BY CaseDate
        '''.format(
            start_date, end_date,
        )
        self.table_widget_purchase_list.set_db_data(sql, self._set_table_data)
        self._set_tool_button()

    def _set_tool_button(self):
        if self.ui.tableWidget_purchase_list.rowCount() > 0:
            enabled = True
        else:
            enabled = False

        self.ui.action_delete_record.setEnabled(enabled)
        self.ui.action_print_receipt.setEnabled(enabled)
        self.ui.action_print_purchase_list.setEnabled(enabled)
        self.ui.action_open_record.setEnabled(enabled)

        self._set_permission()

    def _set_table_data(self, row_no, row):
        content = self._get_purchase_content(row['CaseKey'])

        purchase_row = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['TotalFee']),
            string_utils.xstr(row['Cashier']),
            string_utils.xstr(row['Doctor']),
            content,
        ]

        for column in range(len(purchase_row)):
            self.ui.tableWidget_purchase_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(purchase_row[column])
            )
            if column in [3, 5]:
                self.ui.tableWidget_purchase_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [2]:
                self.ui.tableWidget_purchase_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _get_purchase_content(self, case_key):
        sql = '''
            SELECT * FROM prescript
            WHERE
                CaseKey = {0}
            ORDER BY PrescriptKey
        '''.format(case_key)

        rows = self.database.select_record(sql)
        content = []
        for row in rows:
            content.append(string_utils.xstr(row['MedicineName']))

        return ', '.join(content)

    def delete_purchase(self):
        name = self.table_widget_purchase_list.field_value(4)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除購藥資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除<font color='blue'> {0} </font>的購藥資料?</b></font>"
                        .format(name))
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        case_key = self.table_widget_purchase_list.field_value(0)
        self.database.delete_record('prescript', 'CaseKey', case_key)
        self.database.delete_record('cases', 'CaseKey', case_key)
        self.database.delete_record('wait', 'CaseKey', case_key)
        current_row = self.ui.tableWidget_purchase_list.currentRow()
        self.ui.tableWidget_purchase_list.removeRow(current_row)

    def open_medical_record(self):
        case_key = self.table_widget_purchase_list.field_value(0)
        self.parent.open_medical_record(case_key, '櫃台購藥')

    # 重新顯示資料 call from pymedical (call from here is not working)
    def refresh_purchase(self):
        case_key = self.table_widget_purchase_list.field_value(0)
        sql = 'SELECT * FROM cases where CaseKey = {0}'.format(case_key)
        row = self.database.select_record(sql)[0]
        current_row = self.ui.tableWidget_purchase_list.currentRow()
        self._set_table_data(current_row, row)

    # 輸入購物資料
    def _purchase(self):
        self.parent.open_purchase_tab()

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_purchase_list(self):
        self.close_all()
        self.close_tab()

    def _print_receipt(self):
        case_key = self.table_widget_purchase_list.field_value(0)
        print_charge = print_receipt.PrintReceipt(
            self, self.database, self.system_settings, case_key, '選擇列印')
        print_charge.print()

        del print_charge

    def _print_purchase_list(self):
        pass
