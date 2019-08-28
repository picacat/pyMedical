#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import system_utils

import ins_apply_list


# 候診名單 2018.01.31
class InsApplyTab(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsApplyTab, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = args[2]
        self.apply_month = args[3]
        self.period = args[4]
        self.apply_type = args[5]
        self.clinic_id = args[6]
        self.ui = None

        self.apply_date = nhi_utils.get_apply_date(self.apply_year, self.apply_month)
        self.apply_type_code = nhi_utils.APPLY_TYPE_CODE[self.apply_type]
        self.show_warning = False

        self._set_ui()
        self._set_signal()
        self._add_ins_apply_list()

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_APPLY_TAB, self)
        system_utils.set_css(self, self.system_settings)

    # 設定信號
    def _set_signal(self):
        pass

    def _add_ins_apply_list(self):
        sql = '''
            SELECT *
            FROM insapply 
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}"
            GROUP BY CaseType
        '''.format(self.apply_date, self.apply_type_code, self.period, self.clinic_id)

        rows = self.database.select_record(sql)
        for row in rows:
            case_type = string_utils.xstr(row['CaseType'])
            self.ui.tabWidget_ins_apply.addTab(
                ins_apply_list.InsApplyList(
                    self, self.database, self.system_settings,
                    self.apply_year, self.apply_month,
                    self.period, self.apply_type, self.clinic_id, case_type,
                ),
                '案件分類-{0}'.format(case_type)
            )

        self._set_tab_icon()

        if self.show_warning:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('申報檔有誤')
            msg_box.setText("<font size='4' color='red'><b>申報檔有錯誤, 請至申報檢查完成錯誤檢查流程.</b></font>")
            msg_box.setInformativeText("錯誤未全部更正前, 請勿申報上傳, 以免遭到退件.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()

    def _set_tab_icon(self):
        tab_icon_list = [ui_utils.ICON_OK for i in range(self.ui.tabWidget_ins_apply.count())]

        for i in range(self.ui.tabWidget_ins_apply.count()):
            tab = self.ui.tabWidget_ins_apply.widget(i)

            if tab.error_count > 0:
                tab_icon_list[i] = ui_utils.ICON_NO
                self.show_warning = True

        for i, icon in zip(range(len(tab_icon_list)), tab_icon_list):
            self.ui.tabWidget_ins_apply.setTabIcon(i, icon)


    def open_medical_record(self, case_key):
        self.parent.open_medical_record(case_key)
