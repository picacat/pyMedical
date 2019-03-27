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
from printer import print_prescription
from printer import print_receipt



# 候診名單 2018.01.31
class WaitingList(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(WaitingList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.statistics_dicts = args[2]
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
            SELECT * FROM reserve
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

    def _set_reservation_data(self, row_no, row_data):
        age_year, age_month = date_utils.get_age(
            row_data['Birthday'], row_data['ReserveDate'])
        if age_year is None:
            age = ''
        else:
            age = '{0}歲'.format(age_year)

        if string_utils.xstr(row_data['Cellphone']) != '':
            phone = string_utils.xstr(row_data['Cellphone'])
        else:
            phone = string_utils.xstr(row_data['Telephone'])

        reservation_data = [
            string_utils.xstr(row_data['ReserveKey']),
            string_utils.xstr(row_data['ReserveDate'].time().strftime('%H:%M')),
            string_utils.xstr(row_data['Period']),
            string_utils.xstr(row_data['Room']),
            string_utils.xstr(row_data['ReserveNo']),
            string_utils.xstr(row_data['PatientKey']),
            string_utils.xstr(row_data['Name']),
            string_utils.xstr(row_data['Gender']),
            age,
            phone,
        ]

        for column in range(len(reservation_data)):
            self.ui.tableWidget_reservation_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(reservation_data[column])
            )

            if column in [3, 4, 5]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [1, 2, 7, 8]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _show_last_medical_record(self):
        self.ui.textEdit_medical_record.setHtml(None)
        patient_key = self.table_widget_reservation_list.field_value(5)
        if patient_key == '':
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
        html = case_utils.get_medical_record_html(self.database, self.system_settings, case_key)
        self.ui.textEdit_medical_record.setHtml(html)

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

    def _set_wait_completed_data(self, rec_no, rec):
        pres_days = case_utils.get_pres_days(self.database, rec['CaseKey'])

        age_year, age_month = date_utils.get_age(rec['Birthday'], rec['CaseDate'])
        if age_year is None:
            age = 'N/A'
        else:
            age = '{0}歲{1}月'.format(age_year, age_month)

        disease_name = string_utils.xstr(rec['DiseaseName1'])
        if disease_name != '':
            disease_name = disease_name[:8]  # 只取前8個字元

        wait_rec = [
            string_utils.xstr(rec['WaitKey']),
            string_utils.xstr(rec['CaseKey']),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Gender']),
            age,
            string_utils.xstr(rec['Room']),
            string_utils.xstr(rec['RegistNo']),
            string_utils.xstr(rec['InsType']),
            string_utils.xstr(rec['RegistType']),
            string_utils.xstr(rec['Share']),
            string_utils.xstr(rec['TreatType']),
            string_utils.xstr(rec['Visit']),
            string_utils.xstr(rec['Card']),
            string_utils.int_to_str(rec['Continuance']).strip('0'),
            disease_name,
            string_utils.xstr(pres_days),
            string_utils.xstr(rec['Doctor']),
            string_utils.xstr(rec['Massager']),
        ]

        for column in range(len(wait_rec)):
            self.ui.tableWidget_wait_completed.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(wait_rec[column])
            )
            if column in [2, 5, 6, 7, 9, 16]:
                self.ui.tableWidget_wait_completed.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [4, 14]:
                self.ui.tableWidget_wait_completed.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if rec['InsType'] == '自費':
                self.ui.tableWidget_wait_completed.item(
                    rec_no, column).setForeground(
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
