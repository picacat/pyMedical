#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import datetime
from libs import ui_utils
from libs import date_utils
from libs import string_utils
from libs import nhi_utils
from classes import table_widget


# 候診名單 2018.01.31
class InsJudge(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsJudge, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        # self.read_wait()   # activate by pymedical.py->tab_changed

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_app(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_JUDGE, self)

    # 設定信號
    def _set_signal(self):
        self.ui.action_medical_record.triggered.connect(self.open_medical_record)
        self.ui.action_close.triggered.connect(self.close_app)

    def open_medical_record(self):
        # case_key = self.table_widget_waiting_list.field_value(1)
        case_key = 0
        self.parent.open_medical_record(case_key, '申報檢查')
