#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
import datetime

from libs import system_utils
from libs import ui_utils
from libs import nhi_utils
from libs import personnel_utils
from libs import string_utils


# 主視窗
class DialogIncome(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogIncome, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INCOME, self)
        system_utils.set_css(self)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')

        ui_utils.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM, '全部')
        ui_utils.set_combo_box(
            self.ui.comboBox_cashier,
            personnel_utils.get_personnel(self.database, '全部'), '全部',
        )
        self.ui.dateEdit_case_date.setDate(datetime.datetime.today())

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    # 設定 mysql script
    def get_sql(self):
        start_date = self.ui.dateEdit_case_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_case_date.date().toString('yyyy-MM-dd 23:59:59')

        sql = '''
            SELECT 
                cases.*, cases.Register as Registrar, deposit.ReturnDate, deposit.Fee, deposit.refunder,
                debt.ReturnDate1, debt.Period1, debt.Cashier1, debt.Fee1
            FROM cases
                LEFT JOIN deposit ON deposit.CaseKey = cases.CaseKey
                LEFT JOIN debt ON debt.CaseKey = cases.CaseKey
            WHERE
                ((cases.CaseDate BETWEEN "{0}" AND "{1}") OR
                 (ReturnDate BETWEEN "{0}" AND "{1}") OR
                 (ReturnDate1 BETWEEN "{0}" AND "{1}"))
        '''.format(start_date, end_date)

        period = None
        if self.ui.radioButton_period1.isChecked():
            period = '早班'
        elif self.ui.radioButton_period2.isChecked():
            period = '午班'
        elif self.ui.radioButton_period2.isChecked():
            period = '晚班'

        if period is not None:
            sql += '''
                AND (cases.Period = "{0}" or deposit.Period = "{0}" or debt.Period1 = "{0}")
            '''.format(period)

        room = self.ui.comboBox_room.currentText()
        if room != '全部':
            sql += ' AND Room = {0}'.format(room)

        cashier = self.ui.comboBox_cashier.currentText()
        if cashier != '全部':
            sql += ''' 
                AND (Cashier = "{0}" or Refunder = "{0}" or Cashier1 = "{0}")
            '''.format(cashier)

        sql += ''' 
            AND ChargeDone = "True" 
            ORDER BY CaseDate, FIELD(cases.Period, {0})
        '''.format(str(nhi_utils.PERIOD)[1:-1])

        return sql

    def accepted_button_clicked(self):
        pass
