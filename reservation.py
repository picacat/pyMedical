#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton, QFileDialog
import datetime
import calendar

from libs import ui_utils
from libs import date_utils
from libs import nhi_utils
from libs import string_utils
from libs import number_utils
from libs import patient_utils
from libs import registration_utils
from libs import export_utils
from libs import system_utils
from libs import personnel_utils
from classes import table_widget
from dialog import dialog_reservation_booking
from dialog import dialog_reservation_modify
from dialog import dialog_reservation_query
from dialog import dialog_off_day_setting

from printer import print_reservation


# 主視窗
class Reservation(QtWidgets.QMainWindow):
    program_name = '預約掛號'

    # 初始化
    def __init__(self, parent=None, *args):
        super(Reservation, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.reserve_key = args[2]
        self.patient_key = args[3]
        self.doctor = args[4]
        self.ui = None
        self.max_reservation_table_times = 4
        self.max_reservation_table_rows = 20
        self.table_header = ['時間', '診號', '姓名', 'reserve_key']
        self.table_header_width = [70, 50, 100, 60]
        self.tab_name = '預約一覽表'

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()
        self.read_reservation()

        if self.patient_key is not None:  # 醫師預約
            self._set_reservation_by_doctor()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_RESERVATION, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_reservation = table_widget.TableWidget(
            self.ui.tableWidget_reservation, self.database
        )
        self.table_widget_reservation_list = table_widget.TableWidget(
            self.ui.tableWidget_reservation_list, self.database
        )

        self.ui.dateEdit_reservation_date.setDate(datetime.datetime.today())
        self._set_week_day()

        self.ui.dateEdit_start_date.setDate(datetime.datetime.today())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.today())

        self.table_widget_reservation_list.set_column_hidden([0])
        self.ui.tabWidget_reservation.setCurrentIndex(0)

        period = registration_utils.get_current_period(self.system_settings)
        self._set_radio_button_period(period)

        self.ui.action_add_reservation.setEnabled(False)
        self.ui.action_cancel_reservation.setEnabled(False)
        self.ui.action_modify_reservation.setEnabled(False)
        self.ui.action_print_reservation.setEnabled(False)
        # self.ui.action_reservation_arrival.setEnabled(False)

        self._set_permission()
        self._set_combo_box_doctor()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_reservation)
        self.ui.action_save_general_table.triggered.connect(self._save_general_table)
        self.ui.action_save_assigned_table.triggered.connect(self._save_assigned_table)
        self.ui.action_remove_assigned_table.triggered.connect(self._remove_assigned_table)
        self.ui.action_modify_reservation.triggered.connect(self._modify_reservation)
        self.ui.action_cancel_reservation.triggered.connect(self._cancel_reservation)
        self.ui.action_print_reservation.triggered.connect(self._print_reservation)
        self.ui.action_reservation_arrival.triggered.connect(self.reservation_arrival)
        self.ui.action_reservation_query.triggered.connect(self._reservation_query)
        self.ui.action_export_reservation_excel.triggered.connect(self._export_reservation_excel)
        self.ui.action_off_day_setting.triggered.connect(self._off_day_setting)

        self.ui.dateEdit_reservation_date.dateChanged.connect(self.read_reservation)
        self.ui.radioButton_period1.clicked.connect(self.read_reservation)
        self.ui.radioButton_period2.clicked.connect(self.read_reservation)
        self.ui.radioButton_period3.clicked.connect(self.read_reservation)

        self.ui.tableWidget_reservation.doubleClicked.connect(self._booking_reservation)
        self.ui.tableWidget_reservation_list.doubleClicked.connect(self.reservation_arrival)
        self.ui.action_add_reservation.triggered.connect(self._booking_reservation)

        self.ui.tabWidget_reservation.currentChanged.connect(self._tab_changed)                   # 切換分頁
        self.ui.dateEdit_start_date.dateChanged.connect(self._read_reservation_list)
        self.ui.dateEdit_end_date.dateChanged.connect(self._read_reservation_list)
        self.ui.radioButton_arrival1.clicked.connect(self._read_reservation_list)
        self.ui.radioButton_arrival2.clicked.connect(self._read_reservation_list)
        self.ui.radioButton_arrival3.clicked.connect(self._read_reservation_list)
        self.ui.tableWidget_reservation.itemSelectionChanged.connect(self._reservation_table_item_changed)
        self.ui.tableWidget_reservation_list.itemSelectionChanged.connect(self._reservation_list_changed)

        self.ui.comboBox_doctor.currentTextChanged.connect(self.read_reservation)

        self.ui.dateEdit_reservation_date.dateChanged.connect(self._set_week_day)

        self.ui.tableWidget_calendar.cellClicked.connect(self._calendar_changed)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, self.program_name, '新增預約', self.user_name) != 'Y':
            self.ui.action_add_reservation.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '更改預約', self.user_name) != 'Y':
            self.ui.action_modify_reservation.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '刪除預約', self.user_name) != 'Y':
            self.ui.action_cancel_reservation.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '預約報到', self.user_name) != 'Y':
            self.ui.action_reservation_arrival.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '查詢預約', self.user_name) != 'Y':
            self.ui.action_reservation_query.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '匯出預約名單', self.user_name) != 'Y':
            self.ui.action_export_reservation_excel.setEnabled(False)
        if personnel_utils.get_permission(self.database, self.program_name, '班表設定', self.user_name) != 'Y':
            self.ui.menu_reservation_table.setEnabled(False)

    # 設定欄位寬度
    def _set_table_width(self):
        width = self.table_header_width * self.max_reservation_table_times
        self.table_widget_reservation.set_table_heading_width(width)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_reservation(self):
        self.close_all()
        self.close_tab()

    def _set_week_day(self):
        week_day_name = self._get_week_day_name()
        self.ui.label_weekday_name.setText(week_day_name)

    def _get_week_day_name(self):
        current_week_day = datetime.datetime(
            self.ui.dateEdit_reservation_date.date().year(),
            self.ui.dateEdit_reservation_date.date().month(),
            self.ui.dateEdit_reservation_date.date().day(),
        ).weekday()

        week_day_name = date_utils.get_weekday_name(current_week_day)

        return week_day_name

    # 設定醫師
    def _set_combo_box_doctor(self):
        script = '''
            SELECT * FROM person 
            WHERE 
                Position IN ("醫師", "支援醫師") AND
                ID IS NOT NULL
        '''
        rows = self.database.select_record(script)

        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list)

        if self.doctor is not None:  # 醫師預約不設定
            return

        room = self.system_settings.field('診療室')  # 取得預設診療室
        period = registration_utils.get_current_period(self.system_settings)
        doctor = registration_utils.get_doctor_schedule(self.database, room, period)
        if doctor is None or doctor == '':
            for i in range(1, 20):
                room = string_utils.xstr(i)
                doctor = registration_utils.get_doctor_schedule(self.database, room, period)
                if doctor is not None and doctor != '':
                    break

        self.ui.comboBox_doctor.setCurrentText(doctor)

    def _set_radio_button_period(self, period):
        if period == '早班':
            self.ui.radioButton_period1.setChecked(True)
        elif period == '午班':
            self.ui.radioButton_period2.setChecked(True)
        elif period == '晚班':
            self.ui.radioButton_period3.setChecked(True)

    def read_reservation(self):
        self._set_reservation_table()
        self._set_reservation_data()
        self._set_calendar()

    def _clear_reservation_table(self):
        self.ui.tableWidget_reservation.clear()

        max_reservation_table_columns = len(self.table_header) * self.max_reservation_table_times
        self.ui.tableWidget_reservation.setColumnCount(max_reservation_table_columns)
        self.ui.tableWidget_reservation.setRowCount(self.max_reservation_table_rows)
        self.ui.tableWidget_reservation.setHorizontalHeaderLabels(
            self.table_header * self.max_reservation_table_times
        )
        self._set_table_width()

        hidden_columns = [i * len(self.table_header) - 1 for i in range(1, self.max_reservation_table_times + 1)]
        self.table_widget_reservation.set_column_hidden(hidden_columns)

    def _set_reservation_table(self):
        self._clear_reservation_table()

        reservation_table_rows = self._get_reservation_table_rows()

        for row in reservation_table_rows:
            self.ui.tableWidget_reservation.setItem(
                number_utils.get_integer(row['RowNo']),
                number_utils.get_integer(row['ColumnNo']),
                QtWidgets.QTableWidgetItem(string_utils.xstr(row['Time']))
            )
            self.ui.tableWidget_reservation.setItem(
                number_utils.get_integer(row['RowNo']),
                number_utils.get_integer(row['ColumnNo']+1),
                QtWidgets.QTableWidgetItem(string_utils.xstr(row['ReserveNo']))
            )
            self.ui.tableWidget_reservation.item(
                number_utils.get_integer(row['RowNo']),
                number_utils.get_integer(row['ColumnNo'])).setTextAlignment(
                QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
            )
            self.ui.tableWidget_reservation.item(
                number_utils.get_integer(row['RowNo']),
                number_utils.get_integer(row['ColumnNo']+1)).setTextAlignment(
                QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
            )

    def _get_reservation_table_rows(self):
        doctor = self.ui.comboBox_doctor.currentText()
        period = self._get_period()
        weekday_name = self._get_week_day_name()

        sql = '''
            SELECT * FROM reservation_table
            WHERE
                (Doctor="{doctor}") AND
                (Period = "{period}") AND
                (Weekday = "{weekday_name}")
            ORDER BY RowNo, ColumnNo
        '''.format(
            doctor=doctor,
            period=period,
            weekday_name=weekday_name,
        )
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            sql = '''
                SELECT * FROM reservation_table
                WHERE
                    (Doctor="{doctor}") AND
                    (Period = "{period}") AND
                    (Weekday IS NULL)
                ORDER BY RowNo, ColumnNo
            '''.format(
                doctor=doctor,
                period=period,
            )
            rows = self.database.select_record(sql)

        return rows

    def _set_reservation_data(self):
        reservation_date = self.ui.dateEdit_reservation_date.date().toString('yyyy-MM-dd')
        period = self._get_period()
        doctor = self.ui.comboBox_doctor.currentText()
        start_date = '{reservation_date} 00:00:00'.format(reservation_date=reservation_date)
        end_date = '{reservation_date} 23:59:59'.format(reservation_date=reservation_date)
        if self._get_off_day_list(reservation_date, period, doctor):
            self._clear_reservation_table()
            return

        for row_no in range(self.ui.tableWidget_reservation.rowCount()):
            for i in range(1, self.max_reservation_table_times+1):
                col_no = (i-1) * len(self.table_header)
                time = self.ui.tableWidget_reservation.item(row_no, col_no)
                if time is None:
                    continue

                reserve_no = self.ui.tableWidget_reservation.item(row_no, col_no+1)
                if reserve_no.text() == '':
                    continue

                sql = '''
                    SELECT * FROM reserve 
                    WHERE
                        ReserveDate BETWEEN "{start_date}" AND "{end_date}" AND
                        Period = "{period}" AND
                        Doctor = "{doctor}" AND
                        ReserveNo = {reserve_no}
                '''.format(
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    doctor=doctor,
                    reserve_no=reserve_no.text(),
                )
                rows = self.database.select_record(sql)
                if len(rows) <= 0:
                    continue

                self.ui.tableWidget_reservation.setItem(
                    row_no, col_no+2,
                    QtWidgets.QTableWidgetItem(string_utils.xstr(rows[0]['Name']))
                )
                self.ui.tableWidget_reservation.setItem(
                    row_no, col_no+3,
                    QtWidgets.QTableWidgetItem(string_utils.xstr(rows[0]['ReserveKey']))
                )

                if rows[0]['Arrival'] == 'True':
                    color = 'gray'
                elif string_utils.xstr(rows[0]['Source']) == '網路預約':
                    color = 'blue'
                elif string_utils.xstr(rows[0]['Source']) in ['初診預約', '網路初診預約']:
                    color = 'green'
                else:
                    color = 'black'

                for i in range(3):
                    self.ui.tableWidget_reservation.item(
                        row_no, col_no+i).setForeground(
                        QtGui.QColor(color)
                    )

    def _save_general_table(self):
        self._save_table()

    def _save_assigned_table(self):
        weekday_name = self._get_week_day_name()
        self._save_table(weekday_name)

    def _remove_assigned_table(self):
        doctor = self.ui.comboBox_doctor.currentText()
        period = self._get_period()
        weekday_name = self._get_week_day_name()

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除掛號資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除{doctor}醫師 {weekday_name}{period}的預約班表表格?</b></font>"
                        .format(doctor=doctor, weekday_name=weekday_name, period=period))
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        self._remove_reservation_table(doctor, period, weekday_name)
        self.read_reservation()

    def _save_table(self, weekday=None):
        doctor = self.ui.comboBox_doctor.currentText()
        period = self._get_period()

        self._remove_reservation_table(doctor, period, weekday)

        for row_no in range(self.ui.tableWidget_reservation.rowCount()):
            for i in range(1, self.max_reservation_table_times+1):
                col_no = (i-1) * len(self.table_header)
                time = self.ui.tableWidget_reservation.item(row_no, col_no)
                reserve_no = self.ui.tableWidget_reservation.item(row_no, col_no+1)
                if time is not None and reserve_no is not None:
                    self._insert_reservation_table(
                        period, weekday, doctor, row_no, col_no,
                        time.text(), reserve_no.text()
                    )

    def _remove_reservation_table(self, doctor, period, weekday):
        sql = '''
            DELETE FROM reservation_table
            WHERE
                Doctor = "{doctor}" AND 
                Period = "{period}" AND
                Weekday = "{weekday}"
        '''.format(
            doctor=doctor,
            period=period,
            weekday=weekday,
        )
        self.database.exec_sql(sql)

    def _insert_reservation_table(self, period, weekday, doctor, row_no, col_no, time, reserve_no):
        fields = [
            'Period', 'Weekday', 'Doctor', 'RowNo', 'ColumnNo', 'Time', 'ReserveNo'
        ]

        data = [
            period, weekday, doctor, row_no, col_no, time, reserve_no
        ]

        self.database.insert_record('reservation_table', fields, data)

    def _get_period(self):
        period = None
        if self.ui.radioButton_period1.isChecked():
            period = '早班'
        elif self.ui.radioButton_period2.isChecked():
            period = '午班'
        elif self.ui.radioButton_period3.isChecked():
            period = '晚班'

        return period

    def _booking_reservation(self):
        current_column = self.ui.tableWidget_reservation.currentColumn()
        current_row = self.ui.tableWidget_reservation.currentRow()

        header = self.ui.tableWidget_reservation.horizontalHeaderItem(current_column)
        if header is None:
            return

        if header.text() != '姓名':
            return

        name = self.ui.tableWidget_reservation.item(current_row, current_column)
        if name is not None:  # 已被預約, 呼叫報到程序
            self.reservation_arrival()
            return

        time = self.ui.tableWidget_reservation.item(current_row, current_column-2)
        reserve_no = self.ui.tableWidget_reservation.item(current_row, current_column-1)
        if time is not None:
            time = time.text()
        else:
            time = ''

        if reserve_no is not None:
            reserve_no = reserve_no.text()
        else:
            reserve_no = ''

        if time == '' and reserve_no == '':
            return

        doctor = self.ui.comboBox_doctor.currentText()
        period = self._get_period()
        reservation_date = '{0} {1}'.format(
            self.ui.dateEdit_reservation_date.date().toString('yyyy-MM-dd'),
            time
        )

        dialog = dialog_reservation_booking.DialogReservationBooking(
            self, self.database, self.system_settings,
            reservation_date, period, doctor, reserve_no, self.patient_key,
        )

        dialog.exec_()
        self.read_reservation()

        dialog.deleteLater()

    def _tab_changed(self, i):
        self.tab_name = self.ui.tabWidget_reservation.tabText(i)

        if self.tab_name == '預約一覽表':
            self.ui.action_save_general_table.setEnabled(True)
            self.ui.action_save_assigned_table.setEnabled(True)
            self.ui.action_remove_assigned_table.setEnabled(True)

            self.read_reservation()
            self.ui.tableWidget_reservation.setCurrentCell(0, 0)
            self.ui.tableWidget_reservation.setFocus()

            self._reservation_table_item_changed()
        else:
            self._read_reservation_list()

            self.ui.action_add_reservation.setEnabled(False)
            self.ui.action_save_general_table.setEnabled(False)
            self.ui.action_save_assigned_table.setEnabled(False)
            self.ui.action_remove_assigned_table.setEnabled(False)
            # self.ui.action_reservation_arrival.setEnabled(False)

            if self.table_widget_reservation_list.row_count() > 0:
                enabled = True
            else:
                enabled = False

            self.ui.action_cancel_reservation.setEnabled(enabled)
            self.ui.action_modify_reservation.setEnabled(enabled)
            self.ui.action_print_reservation.setEnabled(enabled)
            self._set_permission()

    def _read_reservation_list(self):
        self.ui.tableWidget_reservation_list.setRowCount(1)

        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')

        arrival = ''
        if self.ui.radioButton_arrival1.isChecked():
            arrival = 'AND Arrival = "False"'
        elif self.ui.radioButton_arrival2.isChecked():
            arrival = 'AND Arrival = "True"'

        sql = '''
            SELECT reserve.*, patient.Telephone, patient.Cellphone FROM reserve
                LEFT JOIN patient ON patient.PatientKey = reserve.PatientKey
            WHERE
                ReserveDate BETWEEN "{0}" AND "{1}"
                {2}
            ORDER BY ReserveDate, FIELD(Period, {3}), ReserveNo
        '''.format(
            start_date,
            end_date,
            arrival,
            string_utils.xstr(nhi_utils.PERIOD)[1:-1]
        )

        self.table_widget_reservation_list.set_db_data(sql, self._set_table_data)
        if self.table_widget_reservation_list.row_count() > 0:
            self.ui.action_reservation_arrival.setEnabled(True)
        else:
            self.ui.action_reservation_arrival.setEnabled(True)

        self._set_permission()

    def _set_table_data(self, row_no, row_data):
        if string_utils.xstr(row_data['Arrival']) == 'True':
            arrival = '已報到'
        else:
            arrival = '未報到'

        patient_key = string_utils.xstr(row_data['PatientKey'])
        if string_utils.xstr(row_data['Source']) == '網路初診預約':
            patient_key = '網路初診'

        reservation_list_data = [
            string_utils.xstr(row_data['ReserveKey']),
            string_utils.xstr(row_data['ReserveDate']),
            string_utils.xstr(row_data['Period']),
            patient_key,
            string_utils.xstr(row_data['Name']),
            string_utils.xstr(row_data['Doctor']),
            string_utils.xstr(row_data['ReserveNo']),
            arrival,
            string_utils.xstr(row_data['Source']),
            string_utils.xstr(row_data['Registrar']),
            string_utils.xstr(row_data['Telephone']),
            string_utils.xstr(row_data['Cellphone']),
        ]

        for column in range(len(reservation_list_data)):
            self.ui.tableWidget_reservation_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(reservation_list_data[column])
            )
            if column in [3, 6]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [2]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

        if string_utils.xstr(row_data['Source']) == '網路預約':
            color = 'blue'
        elif string_utils.xstr(row_data['Source']) in ['初診預約', '網路初診預約']:
            color = 'green'
        else:
            color = 'black'

        for col_no in range(self.ui.tableWidget_reservation_list.columnCount()):
            self.ui.tableWidget_reservation_list.item(
                row_no, col_no).setForeground(
                QtGui.QColor(color)
            )

    def _get_reserve_key_by_table(self, row_no, col_no, warning=False):
        header = self.ui.tableWidget_reservation.horizontalHeaderItem(col_no)
        if header is None:
            return None

        header = header.text()
        if header != '姓名':
            return None

        name = self.ui.tableWidget_reservation.item(row_no, col_no)
        if name is None:
            return None

        reserve_key = self.ui.tableWidget_reservation.item(row_no, col_no + 1)
        if reserve_key is None:
            return None

        arrival = self._check_reservation_arrival(reserve_key.text())
        if arrival:  # 已報到
            return None

        reserve_key = reserve_key.text()

        return reserve_key

    def _get_name_by_table(self, row_no, col_no):
        header = self.ui.tableWidget_reservation.horizontalHeaderItem(col_no)
        if header is None:
            return None

        header = header.text()
        if header != '姓名':
            return None

        name = self.ui.tableWidget_reservation.item(row_no, col_no)
        if name is None:
            return None

        return name.text()

    def _cancel_reservation(self):
        if self.tab_name == '預約一覽表':
            self._cancel_reservation_by_table()
        else:
            self._cancel_reservation_by_list()

    def _cancel_reservation_by_table(self):
        current_row = self.ui.tableWidget_reservation.currentRow()
        current_column = self.ui.tableWidget_reservation.currentColumn()

        reserve_key = self._get_reserve_key_by_table(current_row, current_column, True)
        if reserve_key is None:
            return

        name = self._get_name_by_table(current_row, current_column)
        if self._delete_reserve_record(reserve_key, name):
            self.read_reservation()

    def _cancel_reservation_by_list(self):
        reserve_key = self.table_widget_reservation_list.field_value(0)
        name = self.table_widget_reservation_list.field_value(4)
        if self._delete_reserve_record(reserve_key, name):
            self._read_reservation_list()

    def _modify_reservation(self):
        if self.tab_name == '預約一覽表':
            i = 0
            current_row = self.ui.tableWidget_reservation.currentRow()
            current_column = self.ui.tableWidget_reservation.currentColumn()
            reserve_key = self._get_reserve_key_by_table(current_row, current_column, True)
        else:
            i = 1
            reserve_key = self.table_widget_reservation_list.field_value(0)

        if reserve_key is None:
            return

        if self._modify_reserve_record(reserve_key):
            self._tab_changed(i)

    def _modify_reserve_record(self, reserve_key):
        dialog = dialog_reservation_modify.DialogReservationModify(
            self, self.database, self.system_settings, reserve_key
        )
        if not dialog.exec_():
            dialog.deleteLater()
            return False

        dialog.deleteLater()

        return True

    def _delete_reserve_record(self, reserve_key, name):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('取消預約掛號')
        msg_box.setText(
            "<font size='4' color='red'><b>確定取消{0}的預約掛號?</b></font>".format(
                name)
        )
        msg_box.setInformativeText("注意！預約掛號取消後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        cancel_reservation = msg_box.exec_()
        if not cancel_reservation:
            return False

        self.database.exec_sql('DELETE FROM reserve WHERE ReserveKey = {0}'.format(reserve_key))

        return True

    def _reservation_table_item_changed(self):
        current_row = self.ui.tableWidget_reservation.currentRow()
        current_column = self.ui.tableWidget_reservation.currentColumn()

        reserve_key = self._get_reserve_key_by_table(current_row, current_column)
        if reserve_key is None:
            enabled = False
        else:
            enabled = True

        self.ui.action_cancel_reservation.setEnabled(enabled)
        self.ui.action_modify_reservation.setEnabled(enabled)
        self.ui.action_print_reservation.setEnabled(enabled)
        self.ui.action_reservation_arrival.setEnabled(enabled)

        self._set_action_add_reservation()

        reserve_date = self.ui.dateEdit_reservation_date.date()
        if reserve_date != datetime.datetime.today():
            self.ui.action_reservation_arrival.setEnabled(False)

        self._set_permission()

    def _set_action_add_reservation(self):
        current_row = self.ui.tableWidget_reservation.currentRow()
        current_column = self.ui.tableWidget_reservation.currentColumn()

        self.ui.action_add_reservation.setEnabled(False)
        header = self.ui.tableWidget_reservation.horizontalHeaderItem(current_column).text()
        if header == '姓名':
            time = self.ui.tableWidget_reservation.item(current_row, current_column-2)
            reservation_no = self.ui.tableWidget_reservation.item(current_row, current_column-1)
            name = self.ui.tableWidget_reservation.item(current_row, current_column)

            if time is not None:
                time = time.text()
            else:
                time = ''

            if reservation_no is not None:
                reservation_no = reservation_no.text()
            else:
                reservation_no = ''

            if name is not None:
                name = name.text()
            else:
                name = ''

            if time != '' and reservation_no != '' and name == '':
                self.ui.action_add_reservation.setEnabled(True)

        self._set_permission()

    def reservation_arrival(self):
        if self.doctor is not None:  # 醫師預約不可報到
            return

        if self.tab_name == '預約一覽表':
            self._arrival_by_table()
        else:
            self._arrival_by_list()

    # 預約一覽表報到
    def _arrival_by_table(self):
        current_column = self.ui.tableWidget_reservation.currentColumn()
        header = self.ui.tableWidget_reservation.horizontalHeaderItem(current_column)
        if header is None or header.text() != '姓名':
            return

        current_row = self.ui.tableWidget_reservation.currentRow()
        name = self.ui.tableWidget_reservation.item(current_row, current_column)
        if name is None:
            return

        reserve_key_item = self.ui.tableWidget_reservation.item(current_row, current_column+1)
        if reserve_key_item is None:
            return

        reserve_key = reserve_key_item.text()
        name = name.text()

        self._ready_to_arrival(reserve_key, name)

    # 預約名單報到
    def _arrival_by_list(self):
        if not self.ui.action_reservation_arrival.isEnabled():
            return

        current_row = self.ui.tableWidget_reservation_list.currentRow()
        reserve_key_item = self.ui.tableWidget_reservation_list.item(current_row, 0)
        if reserve_key_item is None:
            return

        name_item = self.ui.tableWidget_reservation_list.item(current_row, 4)
        if name_item is None:
            return

        reserve_key = reserve_key_item.text()
        name = name_item.text()

        arrival = self._check_reservation_arrival(reserve_key)
        if arrival:  # 已報到
            return

        self._ready_to_arrival(reserve_key, name)

    def _ready_to_arrival(self, reserve_key, name):
        arrival = self._check_reservation_arrival(reserve_key)
        if arrival:  # 已報到
            return

        first_reserve_row = self._check_reservation_first_visit(reserve_key)  # 檢查是否為初診預約報到
        if first_reserve_row is not None:
            self._first_visit_arrival(first_reserve_row)
        else:
            self._normal_arrival(reserve_key, name)

    def _check_reservation_first_visit(self, reserve_key):
        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveKey = {reserve_key}
        '''.format(
            reserve_key=reserve_key,
        )
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return None

        row = rows[0]

        reservation_source = string_utils.xstr(row['Source'])
        if reservation_source in ['初診預約', '網路初診預約']:
            return row
        else:
            return None

    def _normal_arrival(self, reserve_key, name):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('預約掛號報到')
        msg_box.setText(
            "<font size='4' color='blue'><b>{0}確定預約掛號報到?</b></font>".format(
                name)
        )
        msg_box.setInformativeText("注意！預約掛號報到後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        arrival = msg_box.exec_()
        if not arrival:
            return

        self.parent.registration_arrival(reserve_key)

    def _first_visit_arrival(self, first_reserve_row):
        sql = '''
            SELECT * FROM temp_patient
            WHERE
                TempPatientKey = {temp_patient_key}
        '''.format(
            temp_patient_key=first_reserve_row['PatientKey'],
        )
        temp_patient_rows = self.database.select_record(sql)
        if len(temp_patient_rows) <= 0:
            return

        temp_patient_row = temp_patient_rows[0]

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('網路初診預約掛號報到')
        msg_box.setText(
            '''
                <font size="4" color="blue"><b>{name}確定初診預約掛號報到?</b></font><br>
                請確認以下的初診預約資料是否正確:<br><br>
                病患姓名: {name}<br>
                身分證號: {id}<br>
                出生日期: {birthday}<br>
                聯絡電話: {phone_no}<br>
            '''.format(
                name=string_utils.xstr(first_reserve_row['Name']),
                id=string_utils.xstr(temp_patient_row['ID']),
                birthday=string_utils.xstr(temp_patient_row['Birthday']),
                phone_no=string_utils.xstr(temp_patient_row['PhoneNo']),
            )
        )
        msg_box.setInformativeText("注意！初診預約掛號報到後, 將會新增一筆正式的病患基本資料!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        arrival = msg_box.exec_()
        if not arrival:
            return

        new_patient_key = self._update_new_patient(temp_patient_row)
        reserve_key = first_reserve_row['ReserveKey']
        sql = '''
            UPDATE reserve
            SET
                PatientKey = {new_patient_key}
            WHERE
                ReserveKey = {reserve_key}
        '''.format(
            new_patient_key=new_patient_key,
            reserve_key=reserve_key,
        )
        self.database.exec_sql(sql)
        self.parent.registration_arrival(reserve_key)

    def _update_new_patient(self, temp_patient_row):
        patient_id = string_utils.xstr(temp_patient_row['ID'])
        if patient_id != '':
            gender_code = patient_id[1]
            gender = patient_utils.get_gender(gender_code)
        else:
            gender = None

        field = [
            'Name', 'ID', 'Gender', 'Birthday', 'Telephone',
        ]
        data = [
            string_utils.xstr(temp_patient_row['Name']),
            patient_id,
            gender,
            string_utils.xstr(temp_patient_row['Birthday']),
            string_utils.xstr(temp_patient_row['PhoneNo']),
        ]
        new_patient_key = self.database.insert_record('patient', field, data)

        return new_patient_key

    def _check_reservation_arrival(self, reserve_key):
        arrival = False

        sql = '''
            SELECT * FROM reserve 
            WHERE
                ReserveKey = {0}
        '''.format(reserve_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return arrival

        if rows[0]['Arrival'] == 'True':
            arrival = True

        return arrival

    def set_reservation_arrival(self, reserve_key=None):
        # if reserve_key is None:
        #     reserve_key = self.reserve_key

        sql = '''
            SELECT * FROM reserve 
            WHERE
                ReserveKey = {0}
        '''.format(reserve_key)
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return

        row = rows[0]

        self.ui.dateEdit_reservation_date.setDate(datetime.datetime.today())
        period = string_utils.xstr(row['Period'])
        self._set_radio_button_period(period)
        self.ui.comboBox_doctor.setCurrentText(string_utils.xstr(row['Doctor']))
        self.read_reservation()

        current_row, current_col = 0, 0
        for row_no in range(self.ui.tableWidget_reservation.rowCount()):
            for col_no in range(self.ui.tableWidget_reservation.columnCount()):
                reservation_key = self.ui.tableWidget_reservation.item(row_no, col_no)
                if reservation_key is not None and reservation_key.text() == string_utils.xstr(reserve_key):
                    current_row = row_no
                    current_col = col_no - 1
                    break

        self.ui.tableWidget_reservation.setCurrentCell(current_row, current_col)
        self.ui.tableWidget_reservation.setFocus()

    def _reservation_list_changed(self):
        reserve_key = self.table_widget_reservation_list.field_value(0)
        if reserve_key is None:
            return

        arrival = self._check_reservation_arrival(reserve_key)
        if arrival:  # 已報到
            enabled = False
        else:
            enabled = True

        self.ui.action_cancel_reservation.setEnabled(enabled)
        self.ui.action_modify_reservation.setEnabled(enabled)
        self.ui.action_print_reservation.setEnabled(enabled)
        self._set_permission()

        enabled = True
        reserve_date = self.ui.tableWidget_reservation_list.item(
            self.ui.tableWidget_reservation_list.currentRow(), 1
        )

        if reserve_date is None:
            enabled = False

        reserve_date = reserve_date.text()[:10]
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        if reserve_date != today:
            enabled = False

        self.ui.action_reservation_arrival.setEnabled(enabled)
        self._set_permission()

    def _reservation_query(self):
        dialog = dialog_reservation_query.DialogReservationQuery(self, self.database, self.system_settings)
        dialog.exec()
        dialog.deleteLater()

    def _set_calendar(self):
        for i in range(0, self.ui.tableWidget_calendar.columnCount()):
            self.ui.tableWidget_calendar.setColumnWidth(i, 100)

        for i in range(0, self.ui.tableWidget_calendar.rowCount()):
            self.ui.tableWidget_calendar.setRowHeight(i, 110)

        calendar_list = {
            0:  [0, 0], 1:  [0, 1], 2:  [0, 2], 3:  [0, 3], 4:  [0, 4], 5:  [0, 5], 6:  [0, 6],
            7:  [1, 0], 8:  [1, 1], 9:  [1, 2], 10: [1, 3], 11: [1, 4], 12: [1, 5], 13: [1, 6],
            14: [2, 0], 15: [2, 1], 16: [2, 2], 17: [2, 3], 18: [2, 4], 19: [2, 5], 20: [2, 6],
            21: [3, 0], 22: [3, 1], 23: [3, 2], 24: [3, 3], 25: [3, 4], 26: [3, 5], 27: [3, 6],
            28: [4, 0], 29: [4, 1], 30: [4, 2], 31: [4, 3], 32: [4, 4], 33: [4, 5], 34: [4, 6],
            35: [5, 0], 36: [5, 1], 37: [5, 2], 38: [5, 3], 39: [5, 4], 40: [5, 5], 41: [5, 6],
        }

        year = self.ui.dateEdit_reservation_date.date().year()
        month = self.ui.dateEdit_reservation_date.date().month()
        doctor = self.ui.comboBox_doctor.currentText()

        self.ui.label_calendar.setText(
            '<b>{doctor}</b>醫師 <b>{year}</b>年<b>{month}</b>月份 預約狀況一覽表'.format(
                year=year,
                month=month,
                doctor=doctor,
            )
        )

        start_day = datetime.datetime(year, month, 1).weekday()
        if start_day == 6:
            start_day = 0
        else:
            start_day += 1

        week_list = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
        period_list = ['日期', '早班', '午班', '晚班']

        self.ui.tableWidget_calendar.clear()
        for i in range(len(week_list)):
            self.ui.tableWidget_calendar.setHorizontalHeaderItem(
                i, QtWidgets.QTableWidgetItem(week_list[i])
            )
        for i in range(self.ui.tableWidget_calendar.rowCount()):
            self.ui.tableWidget_calendar.setVerticalHeaderItem(
                i, QtWidgets.QTableWidgetItem('\n'.join(period_list))
            )

        last_day = calendar.monthrange(year, month)[1]
        current_month = datetime.date.today().month
        today = datetime.date.today().day

        for i in range(0, last_day):
            day = i + 1
            reservation_date = '{0}-{1}-{2}'.format(year, month, day)
            reservation1 = self._get_reservation_status(reservation_date, '早班', doctor)
            reservation2 = self._get_reservation_status(reservation_date, '午班', doctor)
            reservation3 = self._get_reservation_status(reservation_date, '晚班', doctor)

            row_no = calendar_list[start_day + i][0]
            col_no = calendar_list[start_day + i][1]
            content = '{day}\n{reservation1}\n{reservation2}\n{reservation3}'.format(
                day=day,
                reservation1=reservation1,
                reservation2=reservation2,
                reservation3=reservation3,
            )
            self.ui.tableWidget_calendar.setItem(
                row_no, col_no, QtWidgets.QTableWidgetItem(content)
            )

            # widget = QtWidgets.QWidget()
            # label = QtWidgets.QLabel()
            # label.setText(
            #     str(day) + '\n' +
            #     reservation1 + '\n' +
            #     reservation2 + '\n' +
            #     reservation3
            # )
            #
            # button1 = QtWidgets.QPushButton(self.ui.tableWidget_calendar)
            # button1.setFlat(True)
            # button1.setText(reservation1)
            # button2 = QtWidgets.QPushButton(self.ui.tableWidget_calendar)
            # button2.setFlat(True)
            # button2.setText(reservation2)
            # button3 = QtWidgets.QPushButton(self.ui.tableWidget_calendar)
            # button3.setFlat(True)
            # button3.setText(reservation3)
            #
            # layout = QtWidgets.QVBoxLayout()
            # layout.addWidget(label)
            # layout.addWidget(button1)
            # layout.addWidget(button2)
            # layout.addWidget(button3)
            # widget.setLayout(layout)
            # self.ui.tableWidget_calendar.setCellWidget(row_no, col_no, widget)

            color = 'white'
            if current_month == month and i == today - 1:
                color = 'lightSteelBlue'
            elif calendar_list[start_day+i][1] == 0:
                color = 'mistyrose'

            self.ui.tableWidget_calendar.item(row_no, col_no).setBackground(QtGui.QColor(color))

    def _get_off_day_list(self, reservation_date, period, doctor):
        start_date = '{0} 00:00:00'.format(reservation_date)
        end_date = '{0} 23:59:59'.format(reservation_date)

        sql = '''
            SELECT * FROM off_day_list
            WHERE
                (OffDate BETWEEN "{start_date}" AND "{end_date}") AND
                (Period = "{period}")
        '''.format(
            start_date=start_date,
            end_date=end_date,
            period=period,
        )
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return False

        row = rows[0]
        off_doctor = string_utils.xstr(row['Doctor'])
        if off_doctor in ['', doctor]:
            return True

        return False

    def _get_reservation_status(self, reservation_date, period, doctor):
        status = ''

        if self._get_off_day_list(reservation_date, period, doctor):
            return '暫停預約'

        start_date = '{0} 00:00:00'.format(reservation_date)
        end_date = '{0} 23:59:59'.format(reservation_date)

        sql = '''
            SELECT * FROM off_day_list
            WHERE
                (OffDate BETWEEN "{start_date}" AND "{end_date}") AND
                (Period = "{period}")
        '''.format(
            start_date=start_date,
            end_date=end_date,
            period=period,
        )
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            pass
        else:
            row = rows[0]
            off_doctor = string_utils.xstr(row['Doctor'])
            if off_doctor in ['', doctor]:
                status = '暫停預約'
                return status

        sql = '''
            SELECT ReserveKey FROM reserve
            WHERE
                (ReserveDate BETWEEN "{start_date}" AND "{end_date}") AND
                (Doctor="{doctor}") AND
                (Period = "{period}")
        '''.format(
            start_date=start_date,
            end_date=end_date,
            doctor=doctor,
            period=period,
        )
        rows = self.database.select_record(sql)
        reservation_count = len(rows)

        if reservation_count > 0:
            status = '預約: {0}人'.format(reservation_count)

        return status

    def _calendar_changed(self):
        current_row = self.ui.tableWidget_calendar.currentRow()
        current_column = self.ui.tableWidget_calendar.currentColumn()
        item = self.ui.tableWidget_calendar.item(
            current_row, current_column
        )

        if item is None:
            return

        year = int(self.ui.dateEdit_reservation_date.date().year())
        month = int(self.ui.dateEdit_reservation_date.date().month())
        day = int(item.text().split('\n')[0])
        self.ui.dateEdit_reservation_date.setDate(QtCore.QDate(year, month, day))

    def _export_reservation_excel(self):
        if self.ui.tabWidget_reservation.currentIndex != 1:
            self.ui.tabWidget_reservation.setCurrentIndex(1)

        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "QFileDialog.getSaveFileName()",
            '預約門診資料.xlsx',
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(excel_file_name, self.ui.tableWidget_reservation_list, [0])

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>預約資料檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def _print_reservation(self):
        if self.tab_name == '預約一覽表':
            i = 0
            current_row = self.ui.tableWidget_reservation.currentRow()
            current_column = self.ui.tableWidget_reservation.currentColumn()
            reservation_key = self._get_reserve_key_by_table(current_row, current_column, True)
        else:
            i = 1
            reservation_key = self.table_widget_reservation_list.field_value(0)

        if reservation_key is None:
            return

        self.print_reservation_form('系統設定', reservation_key)

    # 列印收據
    def print_reservation_form(self, printable, reservation_key=False):
        if not reservation_key:
            reservation_key = self.table_widget_wait.field_value(1)

        print_reserve = print_reservation.PrintReservation(
            self, self.database, self.system_settings, reservation_key, printable)
        print_reserve.print()

        del print_reserve

    # 由醫師預約
    def _set_reservation_by_doctor(self):
        self.ui.action_reservation_arrival.setEnabled(False)
        self.ui.comboBox_doctor.setEnabled(False)

        if self.doctor is not None:
            self.ui.comboBox_doctor.setCurrentText(self.doctor)

    def _off_day_setting(self):
        dialog = dialog_off_day_setting.DialogOffDaySetting(
            self, self.database, self.system_settings,
        )

        dialog.exec_()
        dialog.deleteLater()
        self.read_reservation()


