#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

from classes import table_widget
from libs import ui_utils
from libs import nhi_utils
from libs import string_utils
from dialog import dialog_doctor_schedule


# 健保抽審 2018.01.31
class DoctorSchedule(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DoctorSchedule, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]

        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_doctor_schedule()

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DOCTOR_SCHEDULE, self)
        self.table_widget_doctor_schedule = table_widget.TableWidget(
            self.ui.tableWidget_doctor_schedule, self.database
        )
        self.table_widget_doctor_schedule.set_column_hidden([0])
        self._set_table_width()

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 60, 60, 120, 120, 120, 120, 120, 120, 120]
        self.table_widget_doctor_schedule.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.action_add_schedule.triggered.connect(self._add_schedule)
        self.ui.action_edit_schedule.triggered.connect(self._edit_schedule)
        self.ui.action_remove_schedule.triggered.connect(self._remove_schedule)
        self.ui.action_close.triggered.connect(self._close_doctor_schedule)
        self.ui.tableWidget_doctor_schedule.doubleClicked.connect(self._edit_schedule)

    def _read_doctor_schedule(self):
        sql = '''
            SELECT * FROM doctor_schedule
            ORDER BY Room, FIELD(Period, {0})
        '''.format(str(nhi_utils.PERIOD)[1:-1])
        self.table_widget_doctor_schedule.set_db_data(sql, self._set_doctor_schedule_data)

    def _set_doctor_schedule_data(self, row_no, row):
        doctor_schedule_row = [
            string_utils.xstr(row['DoctorScheduleKey']),
            string_utils.xstr(row['Room']),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['Monday']),
            string_utils.xstr(row['Tuesday']),
            string_utils.xstr(row['Wednesday']),
            string_utils.xstr(row['Thursday']),
            string_utils.xstr(row['Friday']),
            string_utils.xstr(row['Saturday']),
            string_utils.xstr(row['Sunday']),
        ]

        for column in range(len(doctor_schedule_row)):
            self.ui.tableWidget_doctor_schedule.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(doctor_schedule_row[column])
            )

            align = QtCore.Qt.AlignLeft
            if column in [1, 2]:
                align = QtCore.Qt.AlignCenter

            self.ui.tableWidget_doctor_schedule.item(
                row_no, column).setTextAlignment(
                align | QtCore.Qt.AlignVCenter
            )

    def _add_schedule(self):
        dialog = dialog_doctor_schedule.DialogDoctorSchedule(
            self, self.database, self.system_settings, None,
        )
        if dialog.exec_():
            self._read_doctor_schedule()

        dialog.deleteLater()

    def _edit_schedule(self):
        dialog = dialog_doctor_schedule.DialogDoctorSchedule(
            self, self.database, self.system_settings,
            self.table_widget_doctor_schedule.field_value(0),
        )
        if dialog.exec_():
            self._read_doctor_schedule()

        dialog.deleteLater()

    def _remove_schedule(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除班表資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此筆班表資料?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        doctor_schedule_key = self.table_widget_doctor_schedule.field_value(0)
        self.database.delete_record('doctor_schedule', 'DoctorScheduleKey', doctor_schedule_key)

        self._read_doctor_schedule()

    def _close_doctor_schedule(self):
        self.close_all()
        self.close_tab()

