#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox
import datetime

from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import personnel_utils
from libs import dialog_utils
from dialog import dialog_debt
from classes import table_widget


# 系統日誌
class EventLog(QtWidgets.QMainWindow):
    program_name = '系統日誌'

    # 初始化
    def __init__(self, parent=None, *args):
        super(EventLog, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()

        self._read_event_log()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_EVENT_LOG, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_event_log = table_widget.TableWidget(self.ui.tableWidget_event_log, self.database)
        self.table_widget_event_log.set_column_hidden([0])
        self._set_table_width()

        self.ui.dateEdit_start_date.setDate(datetime.datetime.now())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.now())

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_app)
        self.ui.action_refresh.triggered.connect(self._read_event_log)
        self.ui.dateEdit_start_date.dateChanged.connect(self._read_event_log)
        self.ui.dateEdit_end_date.dateChanged.connect(self._read_event_log)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 50, 200, 110, 150, 100, 150, 880]
        self.table_widget_event_log.set_table_heading_width(width)

    def _read_event_log(self):
        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')

        sql = '''
            SELECT * FROM event_log
            WHERE
                TimeStamp BETWEEN "{start_date}" AND "{end_date}"
            ORDER BY TimeStamp DESC
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )

        self.table_widget_event_log.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        log_type = string_utils.xstr(row['LogType'])
        user_name = string_utils.xstr(row['UserName'])
        log_row = [
            string_utils.xstr(row['LogKey']),
            None,
            string_utils.xstr(row['TimeStamp']),
            user_name,
            string_utils.xstr(row['IP']),
            log_type,
            string_utils.xstr(row['ProgramName']),
            string_utils.xstr(row['Log']),
        ]

        for col_no in range(len(log_row)):
            self.ui.tableWidget_event_log.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(log_row[col_no])
            )

        icon = None
        if log_type == '資料刪除':
            icon = './icons/software-update-urgent.png'
        elif log_type == '資料修正':
            icon = './icons/software-update-available.png'
        elif log_type == '系統登入':
            if user_name == '超級使用者':
                icon = './icons/user-info.png'
            else:
                icon = './icons/emblem-default.png'

        ui_utils.set_table_widget_field_icon(
            self.ui.tableWidget_event_log, row_no, 1, icon,
            None, None, self._do_nothing)

    def _do_nothing(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_app(self):
        self.close_all()
        self.close_tab()

