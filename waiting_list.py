#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtChart import *

import datetime

from classes import table_widget
from libs import ui_utils
from libs import date_utils
from libs import string_utils
from libs import nhi_utils
from libs import case_utils
from libs import statistics_utils
from libs import personnel_utils
from libs import patient_utils
from printer import print_prescription
from printer import print_receipt


# 候診名單 2018.01.31
class WaitingList(QtWidgets.QMainWindow):
    program_name = '醫師看診作業'

    # 初始化
    def __init__(self, parent=None, *args):
        super(WaitingList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.statistics_dicts = args[2]
        self.ui = None

        self.tab_name = '候診名單'
        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()

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
        self.table_widget_reservation_list = table_widget.TableWidget(
            self.ui.tableWidget_reservation_list, self.database)
        self.table_widget_reservation_list.set_column_hidden([0])
        self.ui.tabWidget_waiting_list.setCurrentIndex(0)
        self.ui.tabWidget_waiting_list.currentChanged.connect(self._waiting_list_tab_changed)                   # 切換分頁
        self.table_widget_wait_completed = table_widget.TableWidget(self.ui.tableWidget_wait_completed, self.database)
        self.table_widget_wait_completed.set_column_hidden([0, 1])
        self.table_widget_statistics_list = table_widget.TableWidget(
            self.ui.tableWidget_statistics_list, self.database)
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_waiting_list.doubleClicked.connect(self.open_medical_record)
        self.ui.tableWidget_wait_completed.doubleClicked.connect(self.open_medical_record)
        self.ui.action_medical_record.triggered.connect(self.open_medical_record)
        self.ui.action_close.triggered.connect(self.close_waiting_list)
        self.ui.tableWidget_reservation_list.itemSelectionChanged.connect(self._show_last_medical_record)
        self.ui.toolButton_print_prescript.clicked.connect(self._print_prescript)
        self.ui.toolButton_print_receipt.clicked.connect(self._print_receipt)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, self.program_name, '病歷登錄', self.user_name) != 'Y':
            self.ui.action_medical_record.setEnabled(False)

    def _set_table_width(self):
        width = [70, 70,
                 70, 80, 40, 90, 40, 60, 60, 70, 50,
                 80, 80, 80, 60, 80, 40, 80, 220]
        self.table_widget_waiting_list.set_table_heading_width(width)

    def _get_room_script(self, table_name):
        if self.system_settings.field('候診名單顯示診別') == '指定診別':
            room = 'AND {table_name}.Room = {value}'.format(
                table_name=table_name,
                value=self.system_settings.field('診療室'),
            )
        elif self.system_settings.field('候診名單顯示診別') == '醫師診別':
            room = 'AND {table_name}.Doctor = "{value}"'.format(
                table_name=table_name,
                value=self.system_settings.field('使用者'),
            )
        else:
            room = ''  # 預設顯示診別為全部

        return room

    def read_wait(self):
        sort = 'ORDER BY FIELD(Period, {0}), RegistNo'.format(str(nhi_utils.PERIOD)[1:-1])  # 預設為診號排序

        room = self._get_room_script('wait')

        if self.system_settings.field('看診排序') == '時間排序':
            sort = 'ORDER BY CaseDate'

        sql = '''
            SELECT wait.*, patient.Gender, patient.Birthday FROM wait 
                LEFT JOIN patient ON wait.PatientKey = patient.PatientKey 
            WHERE 
                DoctorDone = "False" 
                {0}
                {1}
        '''.format(room, sort)

        self.table_widget_waiting_list.set_db_data(sql, self._set_table_data)

        row_count = self.table_widget_waiting_list.row_count()
        if row_count > 0:
            self._set_tool_button(True)
        else:
            self._set_tool_button(False)

        self._read_reservation()
        self._set_statistics_list()

    def _set_tool_button(self, enabled):
        self.ui.action_medical_record.setEnabled(enabled)
        self._set_permission()

    def _set_table_data(self, row_no, row):
        registration_time = row['CaseDate'].strftime('%H:%M')

        time_delta = datetime.datetime.now() - row['CaseDate']
        wait_seconds = datetime.timedelta(seconds=time_delta.total_seconds())
        wait_time = '{0}分'.format(wait_seconds.seconds // 60)

        age_year, age_month = date_utils.get_age(row['Birthday'], row['CaseDate'])
        if age_year is None:
            age = 'N/A'
        else:
            age = '{0}歲{1}月'.format(age_year, age_month)

        wait_row = [
                    string_utils.xstr(row['WaitKey']),
                    string_utils.xstr(row['CaseKey']),
                    row['PatientKey'],
                    string_utils.xstr(row['Name']),
                    string_utils.xstr(row['Gender']),
                    age,
                    row['Room'],
                    row['RegistNo'],
                    registration_time,
                    wait_time,
                    string_utils.xstr(row['InsType']),
                    string_utils.xstr(row['RegistType']),
                    string_utils.xstr(row['Share']),
                    string_utils.xstr(row['TreatType']),
                    string_utils.xstr(row['Visit']),
                    string_utils.xstr(row['Card']),
                    row['Continuance'],
                    string_utils.xstr(row['Massager']),
                    string_utils.xstr(row['Remark']),
        ]

        for col_no in range(len(wait_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, wait_row[col_no])
            self.ui.tableWidget_waiting_list.setItem(
                row_no, col_no, item,
            )
            if col_no in [2, 5, 6, 7, 9, 16]:
                self.ui.tableWidget_waiting_list.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [4, 14]:
                self.ui.tableWidget_waiting_list.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if row['InsType'] == '自費':
                self.ui.tableWidget_waiting_list.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('blue')
                )

    def open_medical_record(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, self.program_name, '病歷登錄', self.user_name) != 'Y'):
            return

        self.tab_name = self.ui.tabWidget_waiting_list.tabText(
            self.ui.tabWidget_waiting_list.currentIndex())

        if self.tab_name == '候診名單':
            case_key = self.table_widget_waiting_list.field_value(1)
            call_from = '醫師看診作業'
        else:
            case_key = self.table_widget_wait_completed.field_value(1)
            call_from = '醫師看診作業-查詢'

        self.parent.open_medical_record(case_key, call_from)

    def _read_reservation(self):
        start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')

        room = self._get_room_script('reserve')

        sql = '''
            SELECT 
                reserve.*, 
                patient.Birthday, patient.Gender, patient.Cellphone, patient.Telephone 
            FROM reserve
                LEFT JOIN patient ON patient.PatientKey = reserve.PatientKey
            WHERE
                ReserveDate BETWEEN "{0}" AND "{1}" AND
                Arrival = "False"
                {2}
            ORDER BY ReserveDate, FIELD(Period, {3}), ReserveNo
        '''.format(
            start_date, end_date,
            room,
            str(nhi_utils.PERIOD)[1:-1]
        )

        self.table_widget_reservation_list.set_db_data(sql, self._set_reservation_data)

    def _set_reservation_data(self, row_no, row):
        reserve_key = string_utils.xstr(row['ReserveKey'])
        reserve_date = string_utils.xstr(row['ReserveDate'].time().strftime('%H:%M'))
        period = string_utils.xstr(row['Period'])
        room = row['Room']
        reserve_no = row['ReserveNo']
        patient_key = row['PatientKey']
        name = string_utils.xstr(row['Name'])
        gender = string_utils.xstr(row['Gender'])

        if string_utils.xstr(row['Cellphone']) != '':
            phone = string_utils.xstr(row['Cellphone'])
        else:
            phone = string_utils.xstr(row['Telephone'])

        if string_utils.xstr(row['Source']) == '網路初診預約':
            sql = '''
                SELECT * FROM temp_patient
                WHERE
                    TempPatientKey = {0}
            '''.format(
                patient_key
            )
            rows = self.database.select_record(sql)
            if len(rows) > 0:
                row = rows[0]
                id = string_utils.xstr(row['ID'])
                if id != '':
                    gender = patient_utils.get_gender(id[1])
            else:
                gender = ''

            patient_key = '網路初診'

        age_year, age_month = date_utils.get_age(
            row['Birthday'], datetime.datetime.now())
        if age_year is None:
            age = ''
        else:
            age = '{0}歲'.format(age_year)

        reservation_row = [
            reserve_key,
            reserve_date,
            period,
            room,
            reserve_no,
            patient_key,
            name,
            gender,
            age,
            phone,
        ]

        for col_no in range(len(reservation_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, reservation_row[col_no])
            self.ui.tableWidget_reservation_list.setItem(
                row_no, col_no, item,
            )

            if col_no in [3, 4, 5]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [1, 2, 7, 8]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _show_last_medical_record(self):
        self.ui.textEdit_medical_record.setHtml(None)

        try:
            patient_key = self.table_widget_reservation_list.field_value(5)
            if patient_key is None:
                return

            if patient_key in ['', '網路初診']:
                return

            sql = '''
                SELECT * FROM cases 
                WHERE
                    PatientKey = {0}
                ORDER BY CaseDate DESC LIMIT 1
            '''.format(patient_key)
            rows = self.database.select_record(sql)
            if len(rows) <= 0:
                self.ui.textEdit_medical_record.setHtml(
                    '<br><br><br><center>無過去病歷</center>'
                )

                return

            case_key = rows[0]['CaseKey']
            if case_key is None:
                return

            html = case_utils.get_medical_record_html(self.database, self.system_settings, case_key)
            self.ui.textEdit_medical_record.setHtml(html)
        except:
            pass

    def _waiting_list_tab_changed(self, i):
        self.tab_name = self.ui.tabWidget_waiting_list.tabText(i)
        if self.tab_name == '候診名單':
            self.read_wait()
        else:
            self._read_wait_completed()

    def _read_wait_completed(self):
        sort = 'ORDER BY FIELD(cases.Period, {0}), cases.RegistNo'.format(str(nhi_utils.PERIOD)[1:-1])  # 預設為診號排序

        room = self._get_room_script('cases')

        if self.system_settings.field('看診排序') == '時間排序':
            sort = 'ORDER BY cases.CaseDate'

        sql = '''
            SELECT wait.*, patient.Gender, patient.Birthday, cases.* FROM wait 
                LEFT JOIN patient ON wait.PatientKey = patient.PatientKey 
                LEFT JOIN cases ON wait.CaseKey = cases.CaseKey 
            WHERE 
                cases.DoctorDone = "True" {0}
                {1}
        '''.format(room, sort)

        self.table_widget_wait_completed.set_db_data(sql, self._set_wait_completed_data)

    def _set_wait_completed_data(self, row_no, row):
        pres_days = case_utils.get_pres_days(self.database, row['CaseKey'])

        age_year, age_month = date_utils.get_age(row['Birthday'], row['CaseDate'])
        if age_year is None:
            age = 'N/A'
        else:
            age = '{0}歲{1}月'.format(age_year, age_month)

        disease_name = string_utils.xstr(row['DiseaseName1'])
        if disease_name != '':
            disease_name = disease_name[:8]  # 只取前8個字元

        wait_row = [
            string_utils.xstr(row['WaitKey']),
            string_utils.xstr(row['CaseKey']),
            row['PatientKey'],
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            age,
            row['Room'],
            row['RegistNo'],
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['RegistType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Visit']),
            string_utils.xstr(row['Card']),
            row['Continuance'],
            disease_name,
            pres_days,
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['Massager']),
        ]

        for col_no in range(len(wait_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, wait_row[col_no])
            self.ui.tableWidget_wait_completed.setItem(
                row_no, col_no, item,
            )
            if col_no in [2, 5, 6, 7, 9, 16]:
                self.ui.tableWidget_wait_completed.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [4, 14]:
                self.ui.tableWidget_wait_completed.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if row['InsType'] == '自費':
                self.ui.tableWidget_wait_completed.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('blue')
                )

    def _set_statistics_list(self):
        statistics_list = dict()

        statistics_list['本日健保內科人數'] = statistics_utils.get_count_by_treat_type(
            self.database, 'wait', '當日', ['內科', '一般'],
        )
        statistics_list['本日健保針灸人數'] = statistics_utils.get_count_by_treat_type(
            self.database, 'wait', '當日', nhi_utils.ACUPUNCTURE_TREAT,
        )
        statistics_list['本日健保傷科人數'] = statistics_utils.get_count_by_treat_type(
            self.database, 'wait', '當日', nhi_utils.MASSAGE_TREAT + nhi_utils.DISLOCATE_TREAT
        )
        statistics_list['本日健保首次人數'] = statistics_utils.get_first_course(
            self.database, 'wait', '當日'
        )

        statistics_list['本月健保內科人數'] = (
            self.statistics_dicts['本月健保內科人數'] +
            statistics_list['本日健保內科人數']
        )
        statistics_list['本月健保針灸人數'] = (
                self.statistics_dicts['本月健保針灸人數'] +
                statistics_list['本日健保針灸人數']
        )
        statistics_list['本月健保傷科人數'] = (
                self.statistics_dicts['本月健保傷科人數'] +
                statistics_list['本日健保傷科人數']
        )
        statistics_list['本月健保首次人數'] = (
                self.statistics_dicts['本月健保首次人數'] +
                statistics_list['本日健保首次人數']
        )
        statistics_list['本月健保看診日數'] = self.statistics_dicts['本月健保看診日數']
        statistics_list['本月健保針傷限量'] = self.statistics_dicts['本月健保針傷限量']
        statistics_list['本月健保針傷合計'] = (
            statistics_list['本月健保針灸人數'] +
            statistics_list['本月健保傷科人數']
        )

        width = [240, 80]
        self.table_widget_statistics_list.set_table_heading_width(width)
        self.table_widget_statistics_list.set_dict(statistics_list)

        self._plot_chart(statistics_list)

    def _plot_chart(self, statistics_list):
        set0 = QBarSet("內科")
        set1 = QBarSet("針灸")
        set2 = QBarSet("傷科")

        set0 << statistics_list['本月健保內科人數']
        set1 << statistics_list['本月健保針灸人數']
        set2 << statistics_list['本月健保傷科人數']

        series = QBarSeries()
        series.append(set0)
        series.append(set1)
        series.append(set2)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle('本月人數統計表')
        chart.setAnimationOptions(QChart.SeriesAnimations)

        calc_date = '{0}年{1}月'.format(
            datetime.datetime.now().year,
            datetime.datetime.now().month,
        )
        categories = [calc_date]

        axis = QBarCategoryAxis()
        axis.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis, series)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(QtCore.Qt.AlignBottom)

        self.chartView = QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        existing_widget = self.ui.verticalLayout_chart.takeAt(0)
        if existing_widget:
            existing_widget.widget().setParent(None)

        self.ui.verticalLayout_chart.addWidget(self.chartView)

    def _print_prescript(self):
        case_key = self.table_widget_wait_completed.field_value(1)
        print_prescript = print_prescription.PrintPrescription(
            self, self.database, self.system_settings, case_key, '選擇列印')
        print_prescript.print()

        del print_prescript

    def _print_receipt(self):
        case_key = self.table_widget_wait_completed.field_value(1)
        print_charge = print_receipt.PrintReceipt(
            self, self.database, self.system_settings, case_key, '選擇列印')
        print_charge.print()

        del print_charge
