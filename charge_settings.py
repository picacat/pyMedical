#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from libs import ui_settings
import charge_settings_regist
import charge_settings_share


# 收費設定 2018.04.14
class ChargeSettings(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ChargeSettings, self).__init__(parent)
        self.parent = parent
        self.args = args
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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_CHARGE_SETTINGS, self)
        self.ui.tabWidget_charge_settings.addTab(
            charge_settings_regist.ChargeSettingsRegist(self, *self.args), '掛號費')
        self.ui.tabWidget_charge_settings.addTab(
            charge_settings_share.ChargeSettingsShare(self, *self.args), '部份負擔')

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_charge_settings)

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = ChargeSettings()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
