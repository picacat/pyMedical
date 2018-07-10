#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from libs import ui_utils
import dict_drug
import dict_treat
import dict_compound


# 樣板 2018.01.31
class DictMedicine(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictMedicine, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DICT_MEDICINE, self)
        self.ui.tabWidget_medicine.addTab(
            dict_drug.DictDrug(self, *self.args), '藥品資料')
        self.ui.tabWidget_medicine.addTab(
            dict_treat.DictTreat(self, *self.args), '處置資料')
        self.ui.tabWidget_medicine.addTab(
            dict_compound.DictCompound(self, *self.args), '成方資料')

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_template)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_template(self):
        self.close_all()
        self.close_tab()
