#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

import datetime
from libs import ui_utils
from libs import string_utils
from libs import system_utils
from libs import personnel_utils
from classes import table_widget
from dialog import dialog_return_card
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
        self.ui = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()
        # self.read_return_card()   # activate by pymedical.py->tab_changed

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

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_return_card)
        self.ui.action_return_card.triggered.connect(self.return_card)
        self.ui.action_open_medical_record.triggered.connect(self.open_medical_record)
        self.ui.action_undo.triggered.connect(self._undo_return_card)
        self.ui.action_print_registration_form.triggered.connect(self._print_registration_form)
        self.ui.tableWidget_return_card.doubleClicked.connect(self.open_medical_record)
        self.ui.tableWidget_return_card.itemSelectionChanged.connect(self._return_card_item_changed)

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

    # 列印收據
    def _print_registration_form(self, printable, case_key=False):
        if not case_key:
            case_key = self.table_widget_return_card.field_value(1)

        print_regist = print_registration.PrintRegistration(
            self, self.database, self.system_settings, case_key, '還卡收據')
        print_regist.print()
        del print_regist

    # 讀取欠卡資料
    def read_return_card(self, return_date=None):
        if return_date is None:
            since_date = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
            return_date = since_date.strftime('%Y-%m-01')

        sql = '''
            SELECT 
                deposit.*, 
                cases.Card, cases.Continuance, cases.DoctorDone, 
                patient.Birthday, patient.ID, patient.CardNo 
            FROM deposit 
                LEFT JOIN cases ON cases.CaseKey = deposit.CaseKey
                LEFT JOIN patient ON patient.PatientKey = deposit.PatientKey
            WHERE DepositDate >= "{0}"
            ORDER BY DepositDate DESC
        '''.format(return_date)
        self.table_widget_return_card.set_db_data(sql, self._set_deposit_data)
        self._set_tool_buttons()
        self._return_card_item_changed()

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

        return_card_data = [
            string_utils.xstr(row['DepositKey']),
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['ID']),
            string_utils.xstr(row['CardNo']),
            string_utils.xstr(row['DepositDate']),
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

