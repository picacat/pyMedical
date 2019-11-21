#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton, QInputDialog

import datetime
from libs import ui_utils
from libs import string_utils
from libs import system_utils
from libs import personnel_utils
from libs import dialog_utils
from libs import number_utils
from classes import table_widget
from dialog import dialog_return_card
from dialog import dialog_add_deposit

from printer import print_registration


# 樣板 2018.01.31
class ReturnCard(QtWidgets.QMainWindow):
    program_name = '健保卡欠還卡'

    # 初始化
    def __init__(self, parent=None, *args):
        super(ReturnCard, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.patient_key = args[2]
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

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_return_card(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_RETURN_CARD, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_return_card = table_widget.TableWidget(self.ui.tableWidget_return_card, self.database)
        self.table_widget_return_card.set_column_hidden([0, 1])
        self._set_table_width()
        self._set_date()
        self.ui.statusbar.showMessage('紅色字體代表欠卡日期超過10天')

    def _set_date(self):
        last_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        self.ui.dateEdit_start_date.setDate(last_month.replace(day=1))
        self.ui.dateEdit_end_date.setDate(datetime.date.today())

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_return_card)
        self.ui.action_return_card.triggered.connect(self.return_card)
        self.ui.action_add_deposit.triggered.connect(self._add_deposit)
        self.ui.action_remove_deposit.triggered.connect(self._remove_deposit)
        self.ui.action_open_medical_record.triggered.connect(self.open_medical_record)
        self.ui.action_undo.triggered.connect(self._undo_return_card)
        self.ui.action_print_registration_form.triggered.connect(self._print_registration_form)
        self.ui.action_print_return_registration_form.triggered.connect(self._print_return_registration_form)
        self.ui.action_modify_deposit_fee.triggered.connect(self._modify_deposit_fee)
        self.ui.tableWidget_return_card.doubleClicked.connect(self.open_medical_record)
        self.ui.tableWidget_return_card.itemSelectionChanged.connect(self._return_card_item_changed)
        self.ui.dateEdit_start_date.dateChanged.connect(self.read_return_card)
        self.ui.dateEdit_end_date.dateChanged.connect(self.read_return_card)
        self.ui.radioButton_deposit.clicked.connect(self.read_return_card)
        self.ui.radioButton_return.clicked.connect(self.read_return_card)
        self.ui.radioButton_all.clicked.connect(self.read_return_card)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, self.program_name, '健保還卡', self.user_name) != 'Y':
            self.ui.action_return_card.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '調閱病歷', self.user_name) != 'Y':
            self.ui.action_open_medical_record.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '還原欠卡', self.user_name) != 'Y':
            self.ui.action_undo.setEnabled(False)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 80, 80, 80, 130, 130, 150, 200, 200, 60, 80, 40, 100, 100, 80, 70]
        self.table_widget_return_card.set_table_heading_width(width)

    # 列印欠卡收據
    def _print_registration_form(self):
        case_key = self.table_widget_return_card.field_value(1)
        self.print_registration_form('直接列印', case_key)

    # 列印還卡收據
    def _print_return_registration_form(self):
        case_key = self.table_widget_return_card.field_value(1)
        self.print_registration_form('還卡收據', case_key)

    # 列印掛號收據
    def print_registration_form(self, printable, case_key=False):
        if not case_key:
            case_key = self.table_widget_return_card.field_value(1)

        print_regist = print_registration.PrintRegistration(
            self, self.database, self.system_settings, case_key, printable
        )
        print_regist.print()
        del print_regist

    # 讀取欠卡資料
    def read_return_card(self):
        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')

        return_condition = ''
        if self.ui.radioButton_deposit.isChecked():
            return_condition = ' AND ReturnDate IS NULL'
        elif self.ui.radioButton_return.isChecked():
            return_condition = ' AND ReturnDate IS NOT NULL'

        sql = '''
            SELECT 
                deposit.*, 
                cases.Card, cases.Continuance, cases.DoctorDone, 
                patient.Birthday, patient.ID, patient.CardNo 
            FROM deposit 
                LEFT JOIN cases ON cases.CaseKey = deposit.CaseKey
                LEFT JOIN patient ON patient.PatientKey = deposit.PatientKey
            WHERE 
                DepositDate BETWEEN "{start_date}" AND "{end_date}"
                {return_condition}
            ORDER BY DepositDate DESC
        '''.format(
            start_date=start_date,
            end_date=end_date,
            return_condition=return_condition,
        )

        self.table_widget_return_card.set_db_data(sql, self._set_deposit_data)
        self._set_tool_buttons()
        self._return_card_item_changed()

        if self.patient_key is not None:
            self._locate_patient(self.patient_key)

    def _set_tool_buttons(self):
        if self.ui.tableWidget_return_card.rowCount() <= 0:
            enabled = False
        else:
            enabled = True

        self.ui.action_open_medical_record.setEnabled(enabled)
        self.ui.action_return_card.setEnabled(enabled)
        self.ui.action_undo.setEnabled(enabled)

        self._set_permission()

    def _set_deposit_data(self, row_no, row):
        if string_utils.xstr(row['DoctorDone']) == 'True':
            doctor_done = '是'
        else:
            doctor_done = '否'

        deposit_date = row['DepositDate'].date()
        present = datetime.datetime.today().date()
        delta = present - deposit_date
        return_card_data = [
            string_utils.xstr(row['DepositKey']),
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['ID']),
            string_utils.xstr(row['CardNo']),
            string_utils.xstr(deposit_date),
            string_utils.xstr(row['ReturnDate']),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Continuance']),
            string_utils.xstr(row['Register']),
            string_utils.xstr(row['Refunder']),
            string_utils.xstr(row['Fee']),
            doctor_done,
        ]

        for column in range(len(return_card_data)):
            self.ui.tableWidget_return_card.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(return_card_data[column])
            )
            if column in [2, 14]:
                self.ui.tableWidget_return_card.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [9, 15]:
                self.ui.tableWidget_return_card.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if delta.days > 10:
                self.ui.tableWidget_return_card.item(
                    row_no, column).setForeground(
                    QtGui.QColor('red')
                )

    def refresh_record(self):
        sql = '''
            SELECT 
                deposit.*, 
                cases.Card, cases.Continuance, cases.DoctorDone, 
                patient.Birthday, patient.ID, patient.CardNo 
            FROM deposit 
                LEFT JOIN cases ON cases.CaseKey = deposit.CaseKey
                LEFT JOIN patient ON patient.PatientKey = deposit.PatientKey
            WHERE DepositKey = {0}
        '''.format(self.table_widget_return_card.field_value(0))
        row = self.database.select_record(sql)
        if len(row) > 0:
            self._set_deposit_data(self.ui.tableWidget_return_card.currentRow(), row[0])

        self._return_card_item_changed()

    # 還卡
    def return_card(self):
        if self.table_widget_return_card.field_value(10) != '欠卡':
            system_utils.show_message_box(
                QMessageBox.Critical,
                '不需還卡',
                '<font size="4" color="red"><b>此筆病歷的卡序不是"欠卡", 不需執行還卡作業.</b></font>',
                '請確定此人是否已經還卡.'
            )
            return

        if self.table_widget_return_card.field_value(15) != '是':
            system_utils.show_message_box(
                QMessageBox.Critical,
                '暫時無法還卡',
                '<font size="4" color="red"><b>此筆病歷尚未看診完畢, 暫時不需執行還卡作業.</b></font>',
                '請確定此人看診完畢後, 再執行還卡作業, 已利系統進行健保卡病歷及處方寫入的程序.'
            )
            return

        dialog = dialog_return_card.DialogReturnCard(
            self, self.database, self.system_settings,
            self.table_widget_return_card.field_value(0),
            self.table_widget_return_card.field_value(1),
            self.table_widget_return_card.field_value(2),
        )
        if dialog.exec_():
            self.refresh_record()

        dialog.deleteLater()

    def open_medical_record(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, self.program_name, '調閱病歷', self.user_name) != 'Y'):
            return

        case_key = self.table_widget_return_card.field_value(1)
        self.parent.open_medical_record(case_key, '欠還卡作業')

    def _undo_return_card(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle('還原成欠卡')
        msg_box.setText(
            '''
            <font size="4" color="red">
              <b>將已還卡資料還原成欠卡狀態?<br>
            </font>
            '''
        )
        msg_box.setInformativeText("若已經執行IC卡還卡，則會產生新的健保卡序!")
        msg_box.addButton(QPushButton("還原"), QMessageBox.YesRole)
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        cancel = msg_box.exec_()
        if cancel:
            return

        self.refresh_record()
        deposit_key = self.table_widget_return_card.field_value(0)
        case_key = self.table_widget_return_card.field_value(1)

        sql = '''
            UPDATE deposit
            SET
                ReturnDate = NULL, Period = NULL, Refunder = NULL
            WHERE
                DepositKey = {deposit_key}
        '''.format(
            deposit_key=deposit_key,
        )
        self.database.exec_sql(sql)

        sql = 'UPDATE cases SET Card = "欠卡" WHERE CaseKey = {0}'.format(case_key)
        self.database.exec_sql(sql)

        self.refresh_record()

    def _return_card_item_changed(self):
        return_date = self.table_widget_return_card.field_value(8)

        if return_date == '':
            enabled = False
        else:
            enabled = True

        self.ui.action_return_card.setEnabled(not enabled)
        self.ui.action_undo.setEnabled(enabled)

        self._set_permission()

    # 新增欠卡資料
    def _add_deposit(self):
        dialog = dialog_add_deposit.DialogAddDeposit(
            self, self.database, self.system_settings
        )

        if not dialog.exec_():
            dialog.deleteLater()
            return

        self.read_return_card()
        dialog.deleteLater()

    # 刪除欠卡資料
    def _remove_deposit(self):
        msg_box = dialog_utils.get_message_box(
            '刪除欠卡資料', QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除{0}的欠卡資料?</b></font>'.format(
                self.table_widget_return_card.field_value(3)),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_return_card.field_value(0)
        self.database.delete_record('deposit', 'DepositKey', key)
        self.ui.tableWidget_return_card.removeRow(self.ui.tableWidget_return_card.currentRow())

    def _locate_patient(self, patient_key):
        patient_key = string_utils.xstr(patient_key)

        for row_no in range(self.ui.tableWidget_return_card.rowCount()):
            self.ui.tableWidget_return_card.setCurrentCell(row_no, 2)
            patient_key_item = self.ui.tableWidget_return_card.item(row_no, 2).text()
            if patient_key == patient_key_item:
                break

    def _modify_deposit_fee(self):
        deposit_fee = number_utils.get_integer(self.table_widget_return_card.field_value(14))

        input_dialog = QInputDialog()
        input_dialog.setOkButtonText('確定')
        input_dialog.setCancelButtonText('取消')
        deposit_fee, ok = input_dialog.getInt(
            self, '更改欠卡費', '請輸入新的欠卡費', deposit_fee, 0, 1000, 100)
        if not ok:
            return

        deposit_key = self.table_widget_return_card.field_value(0)
        case_key = self.table_widget_return_card.field_value(1)

        sql = '''
            UPDATE deposit
            SET
                Fee = {deposit_fee}
            WHERE
                DepositKey = {deposit_key}
        '''.format(
            deposit_key=deposit_key,
            deposit_fee=deposit_fee,
        )
        self.database.exec_sql(sql)

        sql = '''
            UPDATE cases 
            SET 
                DepositFee = {deposit_fee} 
            WHERE 
                CaseKey = {case_key}
        '''.format(
            case_key=case_key,
            deposit_fee=deposit_fee,
        )
        self.database.exec_sql(sql)

        self.refresh_record()
