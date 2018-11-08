#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import ui_utils
from libs import string_utils
from libs import charge_utils
from classes import table_widget
from dialog import dialog_input_share


# 收費設定 2018.04.14
class ChargeSettingsShare(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ChargeSettingsShare, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_charge()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHARGE_SETTINGS_SHARE, self)
        self.table_widget_diag_share = table_widget.TableWidget(self.ui.tableWidget_diag_share, self.database)
        self.table_widget_diag_share.set_column_hidden([0, 1])
        self.table_widget_drug_share = table_widget.TableWidget(self.ui.tableWidget_drug_share, self.database)
        self.table_widget_drug_share.set_column_hidden([0, 1])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_diag_share_add.clicked.connect(self._diag_share_add)
        self.ui.toolButton_diag_share_delete.clicked.connect(self._diag_share_delete)
        self.ui.toolButton_diag_share_edit.clicked.connect(self._diag_share_edit)
        self.ui.tableWidget_diag_share.doubleClicked.connect(self._diag_share_edit)
        self.ui.toolButton_drug_share_add.clicked.connect(self._drug_share_add)
        self.ui.toolButton_drug_share_delete.clicked.connect(self._drug_share_delete)
        self.ui.toolButton_drug_share_edit.clicked.connect(self._drug_share_edit)
        self.ui.tableWidget_drug_share.doubleClicked.connect(self._drug_share_edit)

    # 設定欄位寬度
    def _set_table_width(self):
        diag_share_width = [60, 60, 180, 120, 100, 60, 80, 80, 150]
        self.table_widget_diag_share.set_table_heading_width(diag_share_width)
        drug_share_width = [60, 60, 220, 150, 100, 100, 200]
        self.table_widget_drug_share.set_table_heading_width(drug_share_width)

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()

    def _read_charge(self):
        self._read_diag_share()
        self._read_drug_share()

    # 門診負擔 **********************************************************************************************************
    def _read_diag_share(self):
        sql = 'SELECT * FROM charge_settings WHERE ChargeType = "門診負擔" ORDER BY ChargeSettingsKey'
        self.table_widget_diag_share.set_db_data(sql, self._set_diag_share_data)
        row_count = self.table_widget_diag_share.row_count()
        if row_count <= 0:
            charge_utils.set_diag_share_basic_data(self.database)
            self._read_diag_share()

    def _set_diag_share_data(self, rec_no, rec):
        diag_share_rec = [
            str(rec['ChargeSettingsKey']),
            string_utils.xstr(rec['ChargeType']),
            string_utils.xstr(rec['ItemName']),
            string_utils.xstr(rec['ShareType']),
            string_utils.xstr(rec['TreatType']),
            string_utils.xstr(rec['Course']),
            string_utils.xstr(rec['InsCode']),
            string_utils.xstr(rec['Amount']),
            string_utils.xstr(rec['Remark']),
        ]

        for column in range(len(diag_share_rec)):
            self.ui.tableWidget_diag_share.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(diag_share_rec[column])
            )
            if column in [7]:
                self.ui.tableWidget_diag_share.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _diag_share_add(self):
        dialog = dialog_input_share.DialogInputShare(self, self.database, self.system_settings, None, '門診負擔')
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_diag_share.rowCount()
            self.ui.tableWidget_diag_share.insertRow(current_row)
            fields = ['ChargeType', 'ItemName', 'ShareType', 'InsCode', 'Amount', 'Remark']
            data = [
                '門診負擔',
                dialog.ui.lineEdit_item_name.text(),
                dialog.ui.comboBox_share_type.currentText(),
                dialog.ui.lineEdit_ins_code.text(),
                dialog.ui.spinBox_amount.value(),
                dialog.ui.lineEdit_remark.text()
            ]
            self.database.insert_record('charge_settings', fields, data)
            sql = 'SELECT * FROM charge_settings WHERE ChargeType = "門診負擔" ORDER BY ChargeSettingsKey desc limit 1'
            row_data = self.database.select_record(sql)[0]
            self._set_diag_share_data(current_row, row_data)
            self.ui.tableWidget_diag_share.setCurrentCell(current_row, 3)

        dialog.close_all()
        dialog.deleteLater()

    def _diag_share_edit(self):
        key = self.table_widget_diag_share.field_value(0)
        dialog = dialog_input_share.DialogInputShare(self, self.database, self.system_settings, key, '門診負擔')
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

        sql = 'SELECT * FROM charge_settings WHERE ChargeSettingsKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_diag_share_data(self.ui.tableWidget_diag_share.currentRow(), row_data)

    def _diag_share_delete(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除門診負擔資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此筆門診負擔資料?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        key = self.table_widget_diag_share.field_value(0)
        self.database.delete_record('charge_settings', 'ChargeSettingsKey', key)
        self.ui.tableWidget_diag_share.removeRow(self.ui.tableWidget_diag_share.currentRow())

    # 藥品負擔 **********************************************************************************************************
    def _read_drug_share(self):
        sql = 'SELECT * FROM charge_settings WHERE ChargeType = "藥品負擔" ORDER BY ChargeSettingsKey'
        self.table_widget_drug_share.set_db_data(sql, self._set_drug_share_data)
        row_count = self.table_widget_drug_share.row_count()
        if row_count <= 0:
            charge_utils.set_drug_share_basic_data(self.database)
            self._read_drug_share()

    def _set_drug_share_data(self, rec_no, rec):
        drug_share_rec = [
            str(rec['ChargeSettingsKey']),
            string_utils.xstr(rec['ChargeType']),
            string_utils.xstr(rec['ItemName']),
            string_utils.xstr(rec['ShareType']),
            string_utils.xstr(rec['InsCode']),
            string_utils.xstr(rec['Amount']),
            string_utils.xstr(rec['Remark']),
        ]

        for column in range(len(drug_share_rec)):
            self.ui.tableWidget_drug_share.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(drug_share_rec[column])
            )
            if column in [5]:
                self.ui.tableWidget_drug_share.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _drug_share_add(self):
        dialog = dialog_input_share.DialogInputShare(self, self.database, self.system_settings, None, '藥品負擔')
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_drug_share.rowCount()
            self.ui.tableWidget_drug_share.insertRow(current_row)
            fields = ['ChargeType', 'ItemName', 'ShareType', 'InsCode', 'Amount', 'Remark']
            data = [
                '藥品負擔',
                dialog.ui.lineEdit_item_name.text(),
                dialog.ui.comboBox_share_type.currentText(),
                dialog.ui.lineEdit_ins_code.text(),
                dialog.ui.spinBox_amount.value(),
                dialog.ui.lineEdit_remark.text()
            ]
            self.database.insert_record('charge_settings', fields, data)
            sql = 'SELECT * FROM charge_settings WHERE ChargeType = "藥品負擔" ORDER BY ChargeSettingsKey desc limit 1'
            row_data = self.database.select_record(sql)[0]
            self._set_drug_share_data(current_row, row_data)
            self.ui.tableWidget_drug_share.setCurrentCell(current_row, 3)

        dialog.close_all()
        dialog.deleteLater()

    def _drug_share_delete(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除藥品負擔資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此筆藥品負擔資料?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        key = self.table_widget_drug_share.field_value(0)
        self.database.delete_record('charge_settings', 'ChargeSettingsKey', key)
        self.ui.tableWidget_drug_share.removeRow(self.ui.tableWidget_drug_share.currentRow())

    def _drug_share_edit(self):
        key = self.table_widget_drug_share.field_value(0)
        dialog = dialog_input_share.DialogInputShare(self, self.database, self.system_settings, key, '藥品負擔')
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

        sql = 'SELECT * FROM charge_settings WHERE ChargeSettingsKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_drug_share_data(self.ui.tableWidget_drug_share.currentRow(), row_data)


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = ChargeSettingsShare()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
