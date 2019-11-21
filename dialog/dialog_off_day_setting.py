#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
from classes import table_widget

import datetime

from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import registration_utils


# 暫停預約設定 2019.10.25
class DialogOffDaySetting(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogOffDaySetting, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]

        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_off_day()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_OFF_DAY_SETTING, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Close).setText('關閉')
        self.ui.dateEdit_off_date.setDate(datetime.datetime.now().date())

        self.table_widget_off_day = table_widget.TableWidget(
            self.ui.tableWidget_off_day, self.database
        )
        self.table_widget_off_day.set_column_hidden([0])
        self._set_table_width()
        self._set_combo_box()

    def _set_table_width(self):
        width = [100, 130, 60, 120, 260, 60]
        self.table_widget_off_day.set_table_heading_width(width)

    def _set_combo_box(self):
        sql = '''
            SELECT * FROM person
            WHERE
                Position IN ("醫師", "支援醫師") 
        '''
        rows = self.database.select_record(sql)
        doctor_list = []
        for row in rows:
            doctor_list.append(string_utils.xstr(row['Name']))

        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD)

        period = registration_utils.get_current_period(self.system_settings)
        self.ui.comboBox_period.setCurrentText(period)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.pushButton_insert_off_day.clicked.connect(self._insert_off_day)

    def _read_off_day(self):
        self.ui.tableWidget_off_day.setRowCount(0)
        sql = '''
            SELECT * FROM off_day_list
            ORDER BY OffDate DESC, FIELD(Period, {period})
        '''.format(
            period=string_utils.xstr(nhi_utils.PERIOD)[1:-1],
        )
        self.table_widget_off_day.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        doctor = string_utils.xstr(row['Doctor'])
        remark = ''
        if doctor in ['', None]:
            remark = '全院暫停預約'

        off_day_row = [
            string_utils.xstr(row['OffDayListKey']),
            string_utils.xstr(row['OffDate']),
            string_utils.xstr(row['Period']),
            doctor,
            remark,
            None,
        ]

        for col_no in range(len(off_day_row)):
            self.ui.tableWidget_off_day.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(off_day_row[col_no])
            )
            if col_no in [2]:
                self.ui.tableWidget_off_day.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

        button = QPushButton(self.ui.tableWidget_off_day)
        button.setIcon(QtGui.QIcon('./icons/cancel.svg'))
        button.setFlat(True)
        button.clicked.connect(self._remove_off_day)
        self.ui.tableWidget_off_day.setCellWidget(row_no, 5, button)

    def _remove_off_day(self):
        off_day_list_key = self.table_widget_off_day.field_value(0)
        if off_day_list_key is None:
            return

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除休診資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此暫停預約設定?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        self.database.exec_sql('DELETE FROM off_day_list where OffDayListKey = {0}'.format(off_day_list_key))
        self.ui.tableWidget_off_day.removeRow(self.ui.tableWidget_off_day.currentRow())

    def accepted_button_clicked(self):
        self.close()

    def _insert_off_day(self):
        doctor = self.ui.comboBox_doctor.currentText()
        if doctor == '':
            doctor = None

        field = [
            'OffDate', 'Period', 'Doctor'
        ]
        data = [
            self.ui.dateEdit_off_date.date().toString('yyyy-MM-dd'),
            self.ui.comboBox_period.currentText(),
            doctor,
        ]

        self.database.insert_record('off_day_list', field, data)
        self._read_off_day()