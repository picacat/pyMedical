#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from libs import ui_settings
from libs import system


# 主視窗
class DialogInputShare(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInputShare, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        try:
            self.charge_settings_key = args[2]
        except IndexError:
            self.charge_settings_key = None

        try:
            self.charge_type = args[3]
        except IndexError:
            self.charge_type = None

        self.ui = None

        self._set_ui()
        self._set_signal()
        if self.charge_settings_key is not None:
            self._edit_charge_settings()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_INPUT_SHARE, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system.set_css(self)
        self.setFixedSize(self.size()) # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('存檔')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.groupBox.setTitle(self.charge_type)
        self.ui.lineEdit_item_name.setFocus()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def _edit_charge_settings(self):
        sql = 'SELECT * FROM charge_settings where ChargeSettingsKey = {0}'.format(self.charge_settings_key)
        row_data = self.database.select_record(sql)[0]
        self.ui.lineEdit_item_name.setText(row_data['ItemName'])
        self.ui.lineEdit_ins_code.setText(row_data['InsCode'])
        self.ui.spinBox_amount.setValue(row_data['Amount'])
        self.ui.lineEdit_remark.setText(row_data['Remark'])

    def accepted_button_clicked(self):
        if self.charge_settings_key is None:
            return

        fields = ['ItemName', 'InsCode', 'Amount', 'Remark']
        data = (
            self.ui.lineEdit_item_name.text(),
            self.ui.lineEdit_ins_code.text(),
            self.ui.spinBox_amount.value(),
            self.ui.lineEdit_remark.text()
        )
        
        self.database.update_record('charge_settings', fields, 'ChargeSettingsKey',
                                    self.charge_settings_key, data)
