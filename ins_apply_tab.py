#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime

from classes import table_widget
from libs import ui_utils
from libs import date_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from dialog import dialog_ins_apply

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

    # 設定信號
    def _set_signal(self):
        pass

    def _add_ins_apply_list(self):
        apply_date = '{0:0>3}{1:0>2}'.format(self.apply_year-1911, self.apply_month)
        if self.apply_type == '申報':
            apply_type = '1'
        else:
            apply_type = '2'

        sql = '''
            SELECT *
            FROM insapply 
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}"
            GROUP BY CaseType
        '''.format(apply_date, apply_type, self.period, self.clinic_id)
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
