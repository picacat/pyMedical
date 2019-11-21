#!/usr/bin/env python3
# 櫃台購藥 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton, QFileDialog
import datetime

from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import number_utils
from libs import personnel_utils
from libs import export_utils
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

        self.dialog_setting = {
            "dialog_executed": False,
            "start_date": None,
            "end_date": None,
            "period": None,
            "cashier": None,
            "doctor": None,
            "massager": None,
        }

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
        self.ui.action_export_excel.triggered.connect(self._export_to_excel)
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

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 130, 60, 90, 100, 700, 90, 90, 90, 90, 90, 90]
        self.table_widget_purchase_list.set_table_heading_width(width)
        self.table_widget_purchase_list.set_column_hidden([0])

    # 讀取病歷
    def _get_sql(self):
        dialog = dialog_purchase_list.DialogPurchaseList(self.ui, self.database, self.system_settings)
        if self.dialog_setting['dialog_executed']:
            dialog.ui.dateEdit_start_date.setDate(self.dialog_setting['start_date'])
            dialog.ui.dateEdit_end_date.setDate(self.dialog_setting['end_date'])
            dialog.ui.comboBox_period.setCurrentText(self.dialog_setting['period'])
            dialog.ui.comboBox_cashier.setCurrentText(self.dialog_setting['cashier'])
            dialog.ui.comboBox_doctor.setCurrentText(self.dialog_setting['doctor'])
            dialog.ui.comboBox_massager.setCurrentText(self.dialog_setting['massager'])

        result = dialog.exec_()
        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['start_date'] = dialog.ui.dateEdit_start_date.date()
        self.dialog_setting['end_date'] = dialog.ui.dateEdit_end_date.date()
        self.dialog_setting['period'] = dialog.comboBox_period.currentText()
        self.dialog_setting['cashier'] = dialog.comboBox_cashier.currentText()
        self.dialog_setting['doctor'] = dialog.comboBox_doctor.currentText()
        self.dialog_setting['massager'] = dialog.comboBox_massager.currentText()

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
        self.ui.action_open_record.setEnabled(enabled)

        self._set_permission()

    def _set_table_data(self, row_no, row):
        content = self._get_purchase_content(row['CaseKey'])
        discount_fee = number_utils.get_integer(row['DiscountFee'])

        purchase_row = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            content,
            number_utils.get_integer(row['SelfTotalFee']),
            discount_fee,
            number_utils.get_integer(row['TotalFee']),
            string_utils.xstr(row['Cashier']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['Massager']),
        ]

        for col_no in range(len(purchase_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, purchase_row[col_no])
            self.ui.tableWidget_purchase_list.setItem(
                row_no, col_no, item
            )
            if col_no in [3, 6, 7, 8]:
                self.ui.tableWidget_purchase_list.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2]:
                self.ui.tableWidget_purchase_list.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if discount_fee > 0:
                self.ui.tableWidget_purchase_list.item(row_no, col_no).setForeground(
                    QtGui.QColor('red')
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
            content.append('{medicine_name} ({quantity}{unit})'.format(
                medicine_name=string_utils.xstr(row['MedicineName']),
                quantity=string_utils.xstr(row['Dosage']),
                unit=string_utils.xstr(row['Unit']),
            ))

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

    # 匯出自購藥 2019.07.01
    def _export_to_excel(self):
        options = QFileDialog.Options()
        title = '{0}至{1}{2}自購藥報表'.format(
            self.dialog_setting['start_date'].toString('yyyy-MM-dd'),
            self.dialog_setting['end_date'].toString('yyyy-MM-dd'),
            self.dialog_setting['period'],
        )
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出自購藥",
            '{title}.xlsx'.format(
                title=title,
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_purchase_list,
            [0], [3, 6, 7, 8], title
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>自購藥報表{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )
