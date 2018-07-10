#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import ui_utils
from libs import string_utils
from classes import table_widget
from dialog import dialog_input_regist, dialog_input_discount


# 收費設定 2018.04.14
class ChargeSettingsRegist(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ChargeSettingsRegist, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHARGE_SETTINGS_REGIST, self)
        self.table_widget_regist_fee = table_widget.TableWidget(self.ui.tableWidget_regist_fee, self.database)
        self.table_widget_regist_fee.set_column_hidden([0, 1])
        self.table_widget_discount = table_widget.TableWidget(self.ui.tableWidget_discount, self.database)
        self.table_widget_discount.set_column_hidden([0, 1])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_regist_fee_add.clicked.connect(self._regist_fee_add)
        self.ui.toolButton_regist_fee_delete.clicked.connect(self._regist_fee_delete)
        self.ui.toolButton_regist_fee_edit.clicked.connect(self._regist_fee_edit)
        self.ui.tableWidget_regist_fee.doubleClicked.connect(self._regist_fee_edit)
        self.ui.toolButton_discount_add.clicked.connect(self._discount_add)
        self.ui.toolButton_discount_delete.clicked.connect(self._discount_delete)
        self.ui.toolButton_discount_edit.clicked.connect(self._discount_edit)
        self.ui.tableWidget_discount.doubleClicked.connect(self._discount_edit)

    # 設定欄位寬度
    def _set_table_width(self):
        regist_fee_width = [60, 60, 300, 100, 100, 100, 100, 100, 310]
        self.table_widget_regist_fee.set_table_heading_width(regist_fee_width)
        discount_width = [60, 60, 150, 80, 200]
        self.table_widget_discount.set_table_heading_width(discount_width)

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()

    def _read_charge(self):
        self._read_regist_fee()
        self._read_discount()

    # 掛號費 ************************************************************************************************************
    def _regist_fee_add(self):
        dialog = dialog_input_regist.DialogInputRegist(self, self.database, self.system_settings)
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_regist_fee.rowCount()
            self.ui.tableWidget_regist_fee.insertRow(current_row)
            fields = ['ChargeType', 'ItemName', 'InsType', 'ShareType', 'TreatType', 'Course',
                      'Amount', 'Remark']
            data = [
                '掛號費',
                dialog.ui.lineEdit_item_name.text(),
                dialog.ui.comboBox_ins_type.currentText(),
                dialog.ui.comboBox_share_type.currentText(),
                dialog.ui.comboBox_treat_type.currentText(),
                dialog.ui.comboBox_course.currentText(),
                dialog.ui.spinBox_amount.value(),
                dialog.ui.lineEdit_remark.text()
            ]
            self.database.insert_record('charge_settings', fields, data)
            sql = 'SELECT * FROM charge_settings WHERE ChargeType = "掛號費" ORDER BY ChargeSettingsKey desc limit 1'
            row_data = self.database.select_record(sql)[0]
            self._set_regist_fee_data(current_row, row_data)
            self.ui.tableWidget_regist_fee.setCurrentCell(current_row, 3)

        dialog.close_all()

    def _regist_fee_edit(self):
        key = self.table_widget_regist_fee.field_value(0)
        dialog = dialog_input_regist.DialogInputRegist(self, self.database, self.system_settings, key)
        dialog.exec_()
        dialog.close_all()
        sql = 'SELECT * FROM charge_settings WHERE ChargeSettingsKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_regist_fee_data(self.ui.tableWidget_regist_fee.currentRow(), row_data)

    def _regist_fee_delete(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除掛號費資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此筆掛號收費資料?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        key = self.table_widget_regist_fee.field_value(0)
        self.database.delete_record('charge_settings', 'ChargeSettingsKey', key)
        self.ui.tableWidget_regist_fee.removeRow(self.ui.tableWidget_regist_fee.currentRow())

    def _read_regist_fee(self):
        sql = 'SELECT * FROM charge_settings WHERE ChargeType = "掛號費" ORDER BY ChargeSettingsKey'
        self.table_widget_regist_fee.set_db_data(sql, self._set_regist_fee_data)
        row_count = self.table_widget_regist_fee.row_count()
        if row_count <= 0:
            self._set_regist_fee_basic_data()

    def _set_regist_fee_data(self, rec_no, rec):
        regist_fee_rec = [
            str(rec['ChargeSettingsKey']),
            string_utils.xstr(rec['ChargeType']),
            string_utils.xstr(rec['ItemName']),
            string_utils.xstr(rec['InsType']),
            string_utils.xstr(rec['ShareType']),
            string_utils.xstr(rec['TreatType']),
            string_utils.xstr(rec['Course']),
            string_utils.xstr(rec['Amount']),
            string_utils.xstr(rec['Remark']),
        ]

        for column in range(0, self.ui.tableWidget_regist_fee.columnCount()):
            self.ui.tableWidget_regist_fee.setItem(rec_no, column, QtWidgets.QTableWidgetItem(regist_fee_rec[column]))
            if column in [7]:
                self.ui.tableWidget_regist_fee.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _set_regist_fee_basic_data(self):
        fields = ['ChargeType', 'ItemName', 'InsType', 'ShareType', 'TreatType', 'Course',
                  'Amount', 'Remark']
        data = [
            ('掛號費', '基本掛號費', '健保', '不分類', '不分類', '首次', 100, None),
            ('掛號費', '基本掛號費', '自費', '不分類', '不分類', '首次', 50, None),
            ('掛號費', '民俗調理費', '健保', '不分類', '不分類', '首次', 50, None),
            ('掛號費', '民俗調理費', '自費', '不分類', '不分類', '首次', 100, None),
            ('掛號費', '欠卡費', '健保', '不分類', '不分類', '首次', 500, None),
            ('掛號費', '內科掛號費', '健保', '基層醫療', '內科', '首次', 100, None),
            ('掛號費', '傷科首次掛號費', '健保', '基層醫療', '傷科治療', '首次', 100, None),
            ('掛號費', '傷科療程掛號費', '健保', '基層醫療', '傷科治療', '療程', 100, None),
            ('掛號費', '針灸首次掛號費', '健保', '基層醫療', '針灸治療', '首次', 100, None),
            ('掛號費', '針灸療程掛號費', '健保', '基層醫療', '針灸治療', '療程', 150, None),
            ('掛號費', '榮民內科掛號費', '健保', '榮民', '內科', '首次', 0, None),
            ('掛號費', '榮民傷科首次掛號費', '健保', '榮民', '傷科治療', '首次', 0, None),
            ('掛號費', '榮民傷科療程掛號費', '健保', '榮民', '傷科治療', '療程', 0, None),
            ('掛號費', '榮民針灸首次掛號費', '健保', '榮民', '針灸治療', '首次', 0, None),
            ('掛號費', '榮民針灸療程掛號費', '健保', '榮民', '針灸治療', '療程', 0, None),
            ('掛號費', '低收入戶內科掛號費', '健保', '低收入戶', '內科', '首次', 0, None),
            ('掛號費', '低收入戶傷科首次掛號費', '健保', '低收入戶', '傷科治療', '首次', 0, None),
            ('掛號費', '低收入戶傷科療程掛號費', '健保', '低收入戶', '傷科治療', '療程', 0, None),
            ('掛號費', '低收入戶針灸首次掛號費', '健保', '低收入戶', '針灸治療', '首次', 0, None),
            ('掛號費', '低收入戶針灸療程掛號費', '健保', '低收入戶', '針灸治療', '療程', 0, None),
        ]
        for rec in data:
            self.database.insert_record('charge_settings', fields, rec)

        self._read_regist_fee()

    # 掛號費優待 *********************************************************************************************************
    def _read_discount(self):
        sql = 'SELECT * FROM charge_settings WHERE ChargeType = "掛號費優待" ORDER BY ChargeSettingsKey'
        self.table_widget_discount.set_db_data(sql, self._set_discount_data)
        row_count = self.table_widget_discount.row_count()
        if row_count <= 0:
            self._set_discount_basic_data()

    def _set_discount_data(self, rec_no, rec):
        discount_rec = [
            str(rec['ChargeSettingsKey']),
            string_utils.xstr(rec['ChargeType']),
            string_utils.xstr(rec['ItemName']),
            string_utils.xstr(rec['Amount']),
            string_utils.xstr(rec['Remark']),
        ]

        for column in range(0, self.ui.tableWidget_discount.columnCount()):
            self.ui.tableWidget_discount.setItem(rec_no, column, QtWidgets.QTableWidgetItem(discount_rec[column]))
            if column in [3]:
                self.ui.tableWidget_discount.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _set_discount_basic_data(self):
        fields = ['ChargeType', 'ItemName', 'InsType', 'ShareType', 'TreatType',
                  'Amount', 'Remark']
        data = [
            ('掛號費優待', '年長病患', None, None, None, 0, None),
            ('掛號費優待', '殘障病患', None, None, None, 0, None),
            ('掛號費優待', '本院員工', None, None, None, 0, None),
            ('掛號費優待', '其他優待', None, None, None, 0, None),
        ]

        for rec in data:
            self.database.insert_record('charge_settings', fields, rec)

        self._read_discount()

    def _discount_add(self):
        dialog = dialog_input_discount.DialogInputDiscount(self, self.database, self.system_settings)
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_discount.rowCount()
            self.ui.tableWidget_discount.insertRow(current_row)
            fields = ['ChargeType', 'ItemName', 'Amount', 'Remark']
            data = [
                '掛號費優待',
                dialog.ui.lineEdit_item_name.text(),
                dialog.ui.spinBox_amount.value(),
                dialog.ui.lineEdit_remark.text()
            ]
            self.database.insert_record('charge_settings', fields, data)
            sql = 'SELECT * FROM charge_settings WHERE ChargeType = "掛號費優待" ORDER BY ChargeSettingsKey desc limit 1'
            row_data = self.database.select_record(sql)[0]
            self._set_discount_data(current_row, row_data)
            self.ui.tableWidget_discount.setCurrentCell(current_row, 3)

        dialog.close_all()

    def _discount_delete(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除掛號費優待資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此筆掛號費優待資料?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        key = self.table_widget_discount.field_value(0)
        self.database.delete_record('charge_settings', 'ChargeSettingsKey', key)
        self.ui.tableWidget_discount.removeRow(self.ui.tableWidget_discount.currentRow())

    def _discount_edit(self):
        key = self.table_widget_discount.field_value(0)
        dialog = dialog_input_discount.DialogInputDiscount(self, self.database, self.system_settings, key)
        dialog.exec_()
        dialog.close_all()
        sql = 'SELECT * FROM charge_settings WHERE ChargeSettingsKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_discount_data(self.ui.tableWidget_discount.currentRow(), row_data)
