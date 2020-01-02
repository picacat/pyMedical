#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import personnel_utils
from dialog import dialog_customer
from classes import table_widget


# 養生館顧客資料查詢
class MassageCustomerList(QtWidgets.QMainWindow):
    program_name = '顧客資料查詢'

    # 初始化
    def __init__(self, parent=None, *args):
        super(MassageCustomerList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()
        self._read_massage_customer()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MASSAGE_CUSTOMER_LIST, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_massage_customer_list = table_widget.TableWidget(
            self.ui.tableWidget_massage_customer_list, self.database
        )
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_delete_record.triggered.connect(self._delete_patient_record)
        self.ui.action_open_massage_customer_record.triggered.connect(self._open_massage_customer_record)
        self.ui.action_open_patient_record.triggered.connect(self._open_patient_record)
        self.ui.action_close.triggered.connect(self.close_patient_list)
        self.ui.action_export_patient_list.triggered.connect(self.export_patient_list)
        self.ui.tableWidget_massage_customer_list.doubleClicked.connect(self._open_massage_customer_record)
        self.ui.lineEdit_keyword.textChanged.connect(self._keyword_changed)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

    # 設定欄位寬度
    def _set_table_width(self):
        width = [90, 90, 100, 50, 110, 150, 150, 150, 200, 350, 200]
        self.table_widget_massage_customer_list.set_table_heading_width(width)

    def _set_tool_button(self):
        if self.ui.tableWidget_massage_customer_list.rowCount() > 0:
            enabled = True
        else:
            enabled = False

        self.ui.action_delete_record.setEnabled(enabled)
        self.ui.action_export_patient_list.setEnabled(enabled)
        self.ui.action_open_massage_customer_record.setEnabled(enabled)
        self.ui.action_open_patient_record.setEnabled(enabled)
        if self.table_widget_massage_customer_list.field_value(1) is not None:
            self.ui.action_open_patient_record.setEnabled(True)

        self._set_permission()

    def _keyword_changed(self):
        sql = '''
            SELECT * FROM massage_customer
        '''
        keyword = self.ui.lineEdit_keyword.text().strip()
        if keyword != '':
            sql += ' WHERE '
            condition = []
            if keyword.isdigit():
                condition.append('MassageCustomerKey = {0}'.format(keyword))
                condition.append('PatientKey = {0}'.format(keyword))

            condition.append('Name LIKE "%{0}%"'.format(keyword))
            condition.append('ID LIKE "{0}%"'.format(keyword))
            condition.append('Telephone LIKE "%{0}%"'.format(keyword))
            condition.append('Cellphone LIKE "{0}%"'.format(keyword))
            sql += ' OR '.join(condition)

        sql += ' ORDER BY MassageCustomerKey'
        self.table_widget_massage_customer_list.set_db_data(sql, self._set_table_data)
        self.ui.lineEdit_keyword.setFocus(True)
        self.ui.lineEdit_keyword.setCursorPosition(len(keyword))
        self._set_tool_button()

    def _read_massage_customer(self):
        sql = '''
            SELECT * FROM massage_customer
            ORDER BY MassageCustomerKey
        '''
        self.table_widget_massage_customer_list.set_db_data(sql, self._set_table_data)
        self._set_tool_button()

    def _set_table_data(self, row_no, row):
        massage_customer_row = [
            row['MassageCustomerKey'],
            row['PatientKey'],
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['ID']),
            string_utils.xstr(row['Telephone']),
            string_utils.xstr(row['Cellphone']),
            string_utils.xstr(row['Email']),
            string_utils.xstr(row['Address']),
            string_utils.xstr(row['Remark']),
        ]

        for col_no in range(len(massage_customer_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, massage_customer_row[col_no])
            self.ui.tableWidget_massage_customer_list.setItem(row_no, col_no, item)
            if col_no in [0, 1]:
                self.ui.tableWidget_massage_customer_list.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [3]:
                self.ui.tableWidget_massage_customer_list.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _delete_patient_record(self):
        name = self.table_widget_massage_customer_list.field_value(2)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除顧客資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除<font color='blue'> {0} </font>的顧客資料?</b></font>"
                        .format(name))
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        massage_customer_key = self.table_widget_massage_customer_list.field_value(0)
        self.database.delete_record('massage_customer', 'MassageCustomerKey', massage_customer_key)
        current_row = self.ui.tableWidget_massage_customer_list.currentRow()
        self.ui.tableWidget_massage_customer_list.removeRow(current_row)

    def _open_patient_record(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, self.program_name, '調閱資料', self.user_name) != 'Y'):
            return

        patient_key = self.table_widget_massage_customer_list.field_value(1)
        if patient_key is not None:
            self.parent.open_patient_record(patient_key, '病患查詢')

    def _open_massage_customer_record(self):
        massage_customer_key = self.table_widget_massage_customer_list.field_value(0)
        dialog = dialog_customer.DialogCustomer(
            self, self.database, self.system_settings, massage_customer_key,
        )
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()
        self._refresh_massage_customer_record()

    def _refresh_massage_customer_record(self):
        massage_customer_key = self.table_widget_massage_customer_list.field_value(0)
        sql = 'SELECT * FROM massage_customer where MassageCustomerKey = {0}'.format(massage_customer_key)
        row = self.database.select_record(sql)[0]
        current_row = self.ui.tableWidget_massage_customer_list.currentRow()
        self._set_table_data(current_row, row)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_patient_list(self):
        self.close_all()
        self.close_tab()

    def export_patient_list(self):
        pass
