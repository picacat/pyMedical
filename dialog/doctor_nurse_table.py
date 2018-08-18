#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime
import calendar

from classes import table_widget
from libs import ui_utils
from libs import date_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from dialog import dialog_ins_apply
from dialog import dialog_nurse_schedule

import ins_apply_generate_file
import ins_apply_list


# 候診名單 2018.01.31
class DoctorNurseTable(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DoctorNurseTable, self).__init__(parent)
        self.parent = parent
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

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_app(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DOCTOR_NURSE_TABLE, self)
        self.table_widget_doctor_nurse_table = table_widget.TableWidget(
            self.ui.tableWidget_doctor_nurse_table, self.database
        )
        self._set_table_width()
        self._set_combo_box()

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.read_schedule)
        self.ui.action_save.triggered.connect(self.save_schedule)
        self.ui.action_close.triggered.connect(self.close_app)
        self.ui.pushButton_query.clicked.connect(self.read_schedule)
        self.ui.tableWidget_doctor_nurse_table.cellDoubleClicked.connect(self._open_input_dialog)

    def _set_table_width(self):
        for i in range(0, self.ui.tableWidget_doctor_nurse_table.columnCount()):
            self.ui.tableWidget_doctor_nurse_table.setColumnWidth(i, 120)

        for i in range(0, self.ui.tableWidget_doctor_nurse_table.rowCount()):
            self.ui.tableWidget_doctor_nurse_table.setRowHeight(i, 110)

    def _set_combo_box(self):
        year_list = []
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month

        for i in range(current_year, current_year - 10, -1):
            year_list.append(str(i))

        ui_utils.set_combo_box(self.ui.comboBox_year, year_list)
        self.ui.comboBox_year.setCurrentText(str(current_year))
        self.ui.comboBox_month.setCurrentText(str(current_month))

        script = 'select * from person where Position = "醫師"'
        rows = self.database.select_record(script)
        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list)

    def open_medical_record(self):
        case_key = 0
        self.parent.open_medical_record(case_key, '健保申報')

    def _open_input_dialog(self):
        current_row = self.ui.tableWidget_doctor_nurse_table.currentRow()
        current_column = self.ui.tableWidget_doctor_nurse_table.currentColumn()
        item = self.ui.tableWidget_doctor_nurse_table.item(
            current_row, current_column
        )

        if item is None:
            return

        schedule_data = self._get_schedule_data(item)

        dialog = dialog_nurse_schedule.DialogNurseSchedule(
            self.ui, self.database, self.system_settings,
            schedule_data[0],
            schedule_data[1],
            schedule_data[2],
            schedule_data[3],
            schedule_data[4],
        )

        if dialog.exec_():
            nurse1 = dialog.ui.comboBox_nurse1.currentText()
            nurse2 = dialog.ui.comboBox_nurse2.currentText()
            nurse3 = dialog.ui.comboBox_nurse3.currentText()
            self.ui.tableWidget_doctor_nurse_table.setItem(
                current_row, current_column,
                QtWidgets.QTableWidgetItem(
                    item.text().split('\n')[0] + '\n' +
                    nurse1 + '\n'+
                    nurse2 + '\n' +
                    nurse3
                )
            )

        dialog.close_all()
        dialog.deleteLater()

    def read_schedule(self):
        year = int(self.ui.comboBox_year.currentText())
        month = int(self.ui.comboBox_month.currentText())
        doctor = self.ui.comboBox_doctor.currentText()

        start_day = datetime.datetime(year, month, 1).weekday()
        if start_day == 6:
            start_day = 0
        else:
            start_day += 1

        calendar_list = {
            0:  [0, 0], 1:  [0, 1], 2:  [0, 2], 3:  [0, 3], 4:  [0, 4], 5:  [0, 5], 6:  [0, 6],
            7:  [1, 0], 8:  [1, 1], 9:  [1, 2], 10: [1, 3], 11: [1, 4], 12: [1, 5], 13: [1, 6],
            14: [2, 0], 15: [2, 1], 16: [2, 2], 17: [2, 3], 18: [2, 4], 19: [2, 5], 20: [2, 6],
            21: [3, 0], 22: [3, 1], 23: [3, 2], 24: [3, 3], 25: [3, 4], 26: [3, 5], 27: [3, 6],
            28: [4, 0], 29: [4, 1], 30: [4, 2], 31: [4, 3], 32: [4, 4], 33: [4, 5], 34: [4, 6],
            35: [5, 0], 36: [5, 1], 37: [5, 2], 38: [5, 3], 39: [5, 4], 40: [5, 5], 41: [5, 6],
        }

        self._clear_calendar()
        last_day = calendar.monthrange(year, month)[1]
        for i in range(0, last_day):
            day = i + 1
            schedule_date = '{0}-{1}-{2}'.format(year, month, day)
            nurse1 = self._get_nurse_name(schedule_date, '早班', doctor)
            nurse2 = self._get_nurse_name(schedule_date, '午班', doctor)
            nurse3 = self._get_nurse_name(schedule_date, '晚班', doctor)
            self.ui.tableWidget_doctor_nurse_table.setItem(
                calendar_list[start_day+i][0],
                calendar_list[start_day+i][1],
                QtWidgets.QTableWidgetItem(
                    str(day) + '\n' +
                    nurse1 + '\n'+
                    nurse2 + '\n' +
                    nurse3
                )
            )
            self.ui.tableWidget_doctor_nurse_table.item(
                calendar_list[start_day+i][0],
                calendar_list[start_day+i][1],
            ).setBackground(QtGui.QColor('white'))

    def _get_nurse_name(self, schedule_date, period, doctor):
        nurse_name = ''
        sql = '''
            SELECT * FROM nurse_schedule
            WHERE
                ScheduleDate = "{0}" AND
                Doctor = "{2}"
        '''.format(schedule_date, period, doctor)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return nurse_name

        row = rows[0]

        nurse_list = {
            '早班': string_utils.xstr(row['Nurse1']),
            '午班': string_utils.xstr(row['Nurse2']),
            '晚班': string_utils.xstr(row['Nurse3']),

        }

        return nurse_list[period]

    def _clear_calendar(self):
        week_list = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
        period_list = ['日期', '早班', '午班', '晚班']
        self.ui.tableWidget_doctor_nurse_table.clear()

        for i in range(len(week_list)):
            self.ui.tableWidget_doctor_nurse_table.setHorizontalHeaderItem(
                i, QtWidgets.QTableWidgetItem(week_list[i])
            )
        for i in range(self.ui.tableWidget_doctor_nurse_table.rowCount()):
            self.ui.tableWidget_doctor_nurse_table.setVerticalHeaderItem(
                i, QtWidgets.QTableWidgetItem('\n'.join(period_list))
            )

    def _delete_existing_schedule(self):
        year = int(self.ui.comboBox_year.currentText())
        month = int(self.ui.comboBox_month.currentText())
        last_day = calendar.monthrange(year, month)[1]
        start_date = '{0}-{1}-{2}'.format(year, month, 1)
        end_date = '{0}-{1}-{2}'.format(year, month, last_day)
        doctor = self.ui.comboBox_doctor.currentText()
        sql = '''
            DELETE FROM nurse_schedule
            WHERE
                ScheduleDate BETWEEN "{0}" AND "{1}" AND
                Doctor = "{2}"
        '''.format(start_date, end_date, doctor)
        self.database.exec_sql(sql)

    def _get_schedule_data(self, item):
        schedule_list = item.text().split('\n')
        schedule_date = '{0}-{1:0>2}-{2:0>2}'.format(
            self.ui.comboBox_year.currentText(),
            self.ui.comboBox_month.currentText(),
            schedule_list[0]
        )
        doctor = self.ui.comboBox_doctor.currentText()
        nurse1 = schedule_list[1]
        nurse2 = schedule_list[2]
        nurse3 = schedule_list[3]

        return [schedule_date, doctor, nurse1, nurse2, nurse3]

    def save_schedule(self):
        self._delete_existing_schedule()

        for i in range(self.ui.tableWidget_doctor_nurse_table.rowCount()):
            for j in range(self.ui.tableWidget_doctor_nurse_table.columnCount()):
                item = self.ui.tableWidget_doctor_nurse_table.item(i, j)
                if item is None:
                    continue

                schedule_data = self._get_schedule_data(item)
                fields = [
                    'ScheduleDate', 'Doctor',
                    'Nurse1', 'Nurse2', 'Nurse3',
                ]

                data = [
                    schedule_data[0],
                    schedule_data[1],
                    schedule_data[2],
                    schedule_data[3],
                    schedule_data[4],
                ]

                self.database.insert_record('nurse_schedule', fields, data)

