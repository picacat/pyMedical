#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import datetime
from libs import ui_utils
from dialog import dialog_ins_check
from libs import date_utils
from libs import string_utils
from libs import nhi_utils
from classes import table_widget

import check_errors
import check_course

# 候診名單 2018.01.31
class InsCheck(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsCheck, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.apply_year = None
        self.apply_month = None
        self.apply_type = None
        self._set_ui()
        self._set_signal()

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_CHECK, self)

    # 設定信號
    def _set_signal(self):
        self.ui.action_medical_record.triggered.connect(self.open_medical_record)
        self.ui.action_recheck.triggered.connect(self.open_dialog)
        self.ui.action_close.triggered.connect(self.close_app)

    def open_medical_record(self, case_key):
        self.parent.open_medical_record(case_key, '申報預檢')

    def open_dialog(self):
        dialog = dialog_ins_check.DialogInsCheck(self.ui, self.database, self.system_settings)
        if self.apply_year is not None:
            dialog.ui.comboBox_year.setCurrentText(self.apply_year)
            dialog.ui.comboBox_month.setCurrentText(self.apply_month)
            if self.apply_type == '申報':
                dialog.ui.radioButton_apply.setChecked(True)
            else:
                dialog.ui.radioButton_reapply.setChecked(True)

        if dialog.exec_():
            self.apply_year = dialog.ui.comboBox_year.currentText()
            self.apply_month = dialog.ui.comboBox_month.currentText()
            if dialog.ui.radioButton_apply.isChecked():
                self.apply_type = '申報'
            else:
                self.apply_type = '補報'

            self._check_everything()

        dialog.close_all()
        dialog.deleteLater()

    def _check_everything(self):
        self.ui.tabWidget_ins_data.clear()

        tab_check_errors = check_errors.CheckErrors(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month, self.apply_type
        )
        tab_check_course = check_course.CheckCourse(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month, self.apply_type
        )
        self.ui.tabWidget_ins_data.addTab(tab_check_errors, '錯誤檢查')
        tab_check_errors.start_check()
        self.ui.tabWidget_ins_data.addTab(tab_check_course, '療程檢查')
        tab_check_course.start_check()
