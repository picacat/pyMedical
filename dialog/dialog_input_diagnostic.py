#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from libs import ui_utils
from libs import system_utils


# 主視窗
class DialogInputDiagnostic(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInputDiagnostic, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        try:
            self.diagnostic_key = args[2]
        except IndexError:
            self.diagnostic_key = None

        self.ui = None

        self._set_ui()
        self._set_signal()
        if self.diagnostic_key is not None:
            self._edit_diagnostic()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INPUT_DIAGNOSTIC, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('存檔')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.lineEdit_diagnostic_name.setFocus()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def _edit_diagnostic(self):
        sql = 'SELECT * FROM clinic WHERE ClinicKey = {0}'.format(self.diagnostic_key)
        row_data = self.database.select_record(sql)[0]
        self.ui.lineEdit_diagnostic_code.setText(row_data['ClinicCode'])
        self.ui.lineEdit_input_code.setText(row_data['InputCode'])
        self.ui.lineEdit_diagnostic_name.setText(row_data['ClinicName'])

    def accepted_button_clicked(self):
        if self.diagnostic_key is None:
            return

        fields = ['ClinicCode', 'InputCode', 'ClinicName']
        data = [
            self.ui.lineEdit_diagnostic_code.text(),
            self.ui.lineEdit_input_code.text(),
            self.ui.lineEdit_diagnostic_name.text(),
        ]
        
        self.database.update_record('clinic', fields, 'ClinicKey',
                                    self.diagnostic_key, data)
