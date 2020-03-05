#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
import datetime

from libs import system_utils
from libs import ui_utils
from libs import nhi_utils
from libs import personnel_utils
from libs import registration_utils
from libs import string_utils


# 主視窗
class DialogDebt(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogDebt, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.debt_key = args[2]
        self.case_key = args[3]

        self.debt_row = None
        self.case_row = None

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_DEBT, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self._set_debt_data()

    def _set_debt_data(self):
        sql = '''
            SELECT * FROM debt
            WHERE
                DebtKey = {0}
        '''.format(self.debt_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        self.debt_row = rows[0]

        self.ui.dateEdit_return_date.setDate(datetime.datetime.today())

        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD)
        ui_utils.set_combo_box(
            self.ui.comboBox_cashier,
            personnel_utils.get_personnel(self.database, '全部'),
        )

        self.ui.comboBox_cashier.setCurrentText(self.system_settings.field('使用者'))
        period = registration_utils.get_current_period(self.system_settings)
        self.ui.comboBox_period.setCurrentText(period)

        self.ui.lineEdit_debt.setText(string_utils.xstr(self.debt_row['Fee']))
        self.ui.lineEdit_pay_back.setText(self.ui.lineEdit_debt.text())
        self.ui.lineEdit_pay_back.setFocus()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def accepted_button_clicked(self):
        self._update_debt()

    def _update_debt(self):
        fields = [
            'ReturnDate1',
            'Period1',
            'Fee1',
            'Cashier1',
            'TotalReturn',
        ]
        data = [
            self.ui.dateEdit_return_date.date().toString('yyyy-MM-dd 00:00:00'),
            self.ui.comboBox_period.currentText(),
            self.ui.lineEdit_pay_back.text(),
            self.ui.comboBox_cashier.currentText(),
            self.ui.lineEdit_pay_back.text(),
        ]

        self.database.update_record('debt', fields, 'DebtKey', self.debt_key, data)
