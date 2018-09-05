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
class WaitingList(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(WaitingList, self).__init__(parent)
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

    def close_waiting_list(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_WAITING_LIST, self)
        self.table_widget_waiting_list = table_widget.TableWidget(self.ui.tableWidget_waiting_list, self.database)
        self.table_widget_waiting_list.set_column_hidden([0, 1])
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_waiting_list.doubleClicked.connect(self.open_medical_record)
        self.ui.action_medical_record.triggered.connect(self.open_medical_record)
        self.ui.action_close.triggered.connect(self.close_waiting_list)

    def _set_table_width(self):
        width = [70, 70,
                 70, 80, 40, 90, 40, 60, 60, 70, 50,
                 80, 80, 80, 60, 80, 40, 80, 220]
        self.table_widget_waiting_list.set_table_heading_width(width)

    def read_wait(self):
        room = ''  # 預設顯示診別為全部
        sort = 'ORDER BY FIELD(Period, {0}), RegistNo'.format(str(nhi_utils.PERIOD)[1:-1])  # 預設為診號排序

        if self.system_settings.field('候診名單顯示診別') == '指定診別':
            room = 'AND Room = {0}'.format(self.system_settings.field('診療室'))

        if self.system_settings.field('看診排序') == '時間排序':
            sort = 'ORDER BY CaseDate'

        sql = '''
            SELECT wait.*, patient.Gender, patient.Birthday FROM wait 
            LEFT JOIN patient ON wait.PatientKey = patient.PatientKey 
            WHERE 
            DoctorDone = "False" {0}
            {1}
        '''.format(room, sort)

        self.table_widget_waiting_list.set_db_data(sql, self._set_table_data)

        row_count = self.table_widget_waiting_list.row_count()
        if row_count > 0:
            self._set_tool_button(True)
        else:
            self._set_tool_button(False)

    def _set_tool_button(self, enabled):
        self.ui.action_medical_record.setEnabled(enabled)

    def _set_table_data(self, rec_no, rec):
        registration_time = rec['CaseDate'].strftime('%H:%M')

        time_delta = datetime.datetime.now() - rec['CaseDate']
        wait_seconds = datetime.timedelta(seconds=time_delta.total_seconds())
        wait_time = '{0}分'.format(wait_seconds.seconds // 60)

        age_year, age_month = date_utils.get_age(rec['Birthday'], rec['CaseDate'])
        if age_year is None:
            age = 'N/A'
        else:
            age = '{0}歲{1}月'.format(age_year, age_month)

        wait_rec = [
                    string_utils.xstr(rec['WaitKey']),
                    string_utils.xstr(rec['CaseKey']),
                    string_utils.xstr(rec['PatientKey']),
                    string_utils.xstr(rec['Name']),
                    string_utils.xstr(rec['Gender']),
                    age,
                    string_utils.xstr(rec['Room']),
                    string_utils.xstr(rec['RegistNo']),
                    registration_time,
                    wait_time,
                    string_utils.xstr(rec['InsType']),
                    string_utils.xstr(rec['RegistType']),
                    string_utils.xstr(rec['Share']),
                    string_utils.xstr(rec['TreatType']),
                    string_utils.xstr(rec['Visit']),
                    string_utils.xstr(rec['Card']),
                    string_utils.int_to_str(rec['Continuance']).strip('0'),
                    string_utils.xstr(rec['Massager']),
                    string_utils.xstr(rec['Remark']),
        ]

        for column in range(len(wait_rec)):
            self.ui.tableWidget_waiting_list.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(wait_rec[column])
            )
            if column in [2, 5, 6, 7, 9, 16]:
                self.ui.tableWidget_waiting_list.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [4, 14]:
                self.ui.tableWidget_waiting_list.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if rec['InsType'] == '自費':
                self.ui.tableWidget_waiting_list.item(
                    rec_no, column).setForeground(
                    QtGui.QColor('blue')
                )

    def open_medical_record(self):
        case_key = self.table_widget_waiting_list.field_value(1)
        self.parent.open_medical_record(case_key, '醫師看診作業')
