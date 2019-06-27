#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore

from libs import ui_utils
from dialog import dialog_ins_check

import check_errors
import check_course
import check_card
import check_medical_record_count
import check_prescript_days
import check_ins_drug
import check_ins_treat

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

        self.duplicated_days = 0
        self.treat_limit = 15
        self.diag_limit = 6

        self.check_errors = True
        self.check_course = True
        self.check_card = True
        self.check_medical_record_count = True
        self.check_prescript_days = True
        self.check_ins_drug = True
        self.check_ins_treat = True

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
        self.ui.action_recheck.triggered.connect(self.open_dialog)
        self.ui.action_close.triggered.connect(self.close_app)

    def open_medical_record(self, case_key):
        self.parent.open_medical_record(case_key, '申報檢查')

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

            self.duplicated_days = dialog.ui.spinBox_duplicated_days.value()
            self.treat_limit = dialog.ui.spinBox_treat_limit.value()
            self.diag_limit = dialog.ui.spinBox_diag_limit.value()

            self.check_errors = dialog.ui.checkBox_check_errors.isChecked()
            self.check_course = dialog.ui.checkBox_check_course.isChecked()
            self.check_card = dialog.ui.checkBox_check_card.isChecked()
            self.check_medical_record_count = dialog.ui.checkBox_check_medical_record_count.isChecked()
            self.check_prescript_days = dialog.ui.checkBox_check_prescript_days.isChecked()
            self.check_ins_drug = dialog.ui.checkBox_check_ins_drug.isChecked()
            self.check_ins_treat = dialog.ui.checkBox_check_ins_treat.isChecked()

            self._check_ins_data()

        dialog.close_all()
        dialog.deleteLater()

    # 開始申報檢查
    def _check_ins_data(self):
        self.ui.tabWidget_ins_data.clear()
        self.tab_icon_list = []

        self._check_errors()
        self._check_course()
        self._check_card()
        self._check_medical_record_count()
        self._check_prescript_days()
        self._check_ins_drug()
        self._check_ins_treat()

        self._set_tab_icon()

        self.ui.tabWidget_ins_data.setCurrentIndex(0)

    # 欄位錯誤檢查
    def _check_errors(self):
        if not self.check_errors:
            return

        tab_check_errors = check_errors.CheckErrors(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month, self.apply_type
        )
        tab_check_errors.start_check()
        self.ui.tabWidget_ins_data.addTab(tab_check_errors, '欄位錯誤檢查')
        self._check_icon(tab_check_errors)

    # 療程檢查
    def _check_course(self):
        if not self.check_course:
            return

        tab_check_course = check_course.CheckCourse(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month, self.apply_type
        )
        tab_check_course.start_check()
        self.ui.tabWidget_ins_data.addTab(tab_check_course, '療程檢查')
        self._check_icon(tab_check_course)

    # 卡序檢查
    def _check_card(self):
        if not self.check_card:
            return

        tab_check_card = check_card.CheckCard(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month, self.apply_type
        )
        tab_check_card.start_check()
        self.ui.tabWidget_ins_data.addTab(tab_check_card, '卡序檢查')
        self._check_icon(tab_check_card)

    # 門診次數檢查
    def _check_medical_record_count(self):
        if not self.check_medical_record_count:
            return

        tab_check_medical_record_count = check_medical_record_count.CheckMedicalRecordCount(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month, self.apply_type, self.treat_limit, self.diag_limit,
        )
        tab_check_medical_record_count.start_check()
        self.ui.tabWidget_ins_data.addTab(tab_check_medical_record_count, '門診次數檢查')
        self._check_icon(tab_check_medical_record_count)

    # 用藥天數檢查
    def _check_prescript_days(self):
        if not self.check_prescript_days:
            return

        tab_check_prescript_days = check_prescript_days.CheckPrescriptDays(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month, self.apply_type, self.duplicated_days,
        )
        tab_check_prescript_days.start_check()
        self.ui.tabWidget_ins_data.addTab(tab_check_prescript_days, '用藥天數檢查')
        self._check_icon(tab_check_prescript_days)

    # 健保藥碼檢查
    def _check_ins_drug(self):
        if not self.check_ins_drug:
            return

        tab_check_ins_drug = check_ins_drug.CheckInsDrug(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month, self.apply_type,
        )
        tab_check_ins_drug.start_check()
        self.ui.tabWidget_ins_data.addTab(tab_check_ins_drug, '健保藥碼檢查')
        self._check_icon(tab_check_ins_drug)

    # 健保處置檢查
    def _check_ins_treat(self):
        if not self.check_ins_treat:
            return

        tab_check_ins_treat = check_ins_treat.CheckInsTreat(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month, self.apply_type,
        )
        tab_check_ins_treat.start_check()
        self.ui.tabWidget_ins_data.addTab(tab_check_ins_treat, '健保處置檢查')
        self._check_icon(tab_check_ins_treat)

    def _check_icon(self, tab):
        icon = ui_utils.ICON_OK
        if tab.error_count() > 0:
            icon = ui_utils.ICON_NO

        self.tab_icon_list.append(icon)

    def _set_tab_icon(self):
        for i, icon in zip(range(len(self.tab_icon_list)), self.tab_icon_list):
            self.ui.tabWidget_ins_data.setTabIcon(i, icon)
