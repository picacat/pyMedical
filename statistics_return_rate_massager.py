#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui, QtChart
from PyQt5.QtWidgets import QMessageBox, QFileDialog

import datetime

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import export_utils
from libs import system_utils


# 推拿師父回診率統計 2019.05.15
class StatisticsReturnRateMassager(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsReturnRateMassager, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.ins_type = args[4]
        self.treat_type = args[5]
        self.visit = args[6]
        self.massager = args[7]
        self.massager_return_days = args[8]
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_RETURN_RATE_MASSAGER, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_return_rate_massager = table_widget.TableWidget(
            self.ui.tableWidget_return_rate_massager, self.database)
        self._set_table_width()
        self.table_widget_return_rate_massager.set_column_hidden([0])

    def _set_table_width(self):
        width = [
            100,
            110, 70, 90, 70, 90, 200, 90, 300, 150]
        self.table_widget_return_rate_massager.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_return_rate_massager.doubleClicked.connect(self._open_medical_record)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_form(self):
        self.close_all()
        self.close_tab()

    def start_calculate(self):
        self.ui.tableWidget_return_rate_massager.setRowCount(0)
        self._calculate_data()

    def _calculate_data(self):
        self._read_data()
        self._calculate_return_rate()
        self._plot_chart()
        self._show_return_rate()

    def _read_data(self):
        self.ins_type_condition = ''
        if self.ins_type != '全部':
            self.ins_type_condition = ' AND InsType = "{0}"'.format(self.ins_type)

        self.treat_type_condition = ''
        if self.treat_type != '全部':
            self.treat_type_condition = ' AND TreatType = "{0}"'.format(self.treat_type)

        self.visit_condition = ''
        if self.visit != '全部':
            self.visit_condition = ' AND Visit = "{0}"'.format(self.visit)

        self.massager_condition = ''
        if self.massager != '全部':
            self.massager_condition = ' AND Massager = "{0}"'.format(self.massager)

        sql = '''
            SELECT  
                CaseKey, CaseDate, cases.PatientKey, cases.Name, Visit, TreatType, DiseaseName1, Doctor, Massager, 
                Telephone, Cellphone
            FROM cases
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}"  AND
                Massager IS NOT NULL
                {ins_type_condition}
                {treat_type_condition}
                {visit_condition}
                {massager_condition}
            GROUP BY PatientKey
            ORDER BY CaseDate
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            ins_type_condition=self.ins_type_condition,
            treat_type_condition=self.treat_type_condition,
            visit_condition=self.visit_condition,
            massager_condition=self.massager_condition,
        )

        self.table_widget_return_rate_massager.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        return_days_list = self._get_return_days_list(row)
        phone_list = []
        if string_utils.xstr(row['Telephone']) != '':
            phone_list.append(string_utils.xstr(row['Telephone']))
        if string_utils.xstr(row['Cellphone']) != '':
            phone_list.append(string_utils.xstr(row['Cellphone']))

        medical_record = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Visit']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['Massager']),
            ', '.join(return_days_list),
            ', '.join(phone_list),
        ]

        for column in range(len(medical_record)):
            self.ui.tableWidget_return_rate_massager.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record[column])
            )
            if column in [2]:
                self.ui.tableWidget_return_rate_massager.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [4]:
                self.ui.tableWidget_return_rate_massager.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _get_return_days_list(self, medical_row):
        start_date = medical_row['CaseDate'].date() + datetime.timedelta(days=1)
        end_date = medical_row['CaseDate'].date() + datetime.timedelta(
            days=number_utils.get_integer(self.massager_return_days)
        )

        sql = '''
            SELECT CaseDate FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                PatientKey = {patient_key}
                {massager_condition}
            GROUP BY DATE(CaseDate)
            ORDER BY CaseDate
        '''.format(
            start_date=start_date,
            end_date=end_date,
            patient_key=medical_row['PatientKey'],
            massager_condition=self.massager_condition,
        )
        rows = self.database.select_record(sql)

        return_days_list = []
        for row in rows:
            return_days_list.append(string_utils.xstr(row['CaseDate'].date()))

        return return_days_list

    def _calculate_return_rate(self):
        self.denominator = self.ui.tableWidget_return_rate_massager.rowCount()

        self.numerator = 0
        for row_no in range(self.ui.tableWidget_return_rate_massager.rowCount()):
            return_date = self.ui.tableWidget_return_rate_massager.item(row_no, 8)
            if return_date is None or return_date.text() == '':
                continue

            self.numerator += 1

    def _show_return_rate(self):
        label_return_rate = QtWidgets.QLabel()

        if self.denominator == 0:
            return_rate = 0
        else:
            return_rate = self.numerator / self.denominator * 100

        label_return_rate.setText(
            '''
                <center>
                {massager}推拿師父回診率 = 歸戶回診人數 / 歸戶總人數 <br>
                {numerator} / {denominator} = <b>{return_rate: .2f}%</b> ({massager_return_days}日內回診)
                </center>
            '''.format(
                massager=self.massager,
                numerator=self.numerator,
                denominator=self.denominator,
                return_rate = return_rate,
                massager_return_days=self.massager_return_days,
            )
        )

        self.ui.verticalLayout_chart.addWidget(label_return_rate)

    def _plot_chart(self):
        series = QtChart.QPieSeries()
        series.append('回診', self.numerator)
        series.append('未回診', self.denominator - self.numerator)

        slice = series.slices()[0]
        slice.setExploded()
        slice.setLabelVisible()

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('{massager}推拿師父回診率'.format(massager=self.massager))
        chart.legend().hide()
        chart.setAnimationOptions(QtChart.QChart.AllAnimations)

        self.chartView = QtChart.QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedWidth(450)
        self.chartView.setFixedHeight(400)
        self.ui.verticalLayout_chart.addWidget(self.chartView)

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出推拿師回診率統計表",
            '{0}至{1}{2}推拿師父回診率統計表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.massager
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_return_rate_massager,
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>推拿師父回診率統計檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def _open_medical_record(self):
        case_key = self.table_widget_return_rate_massager.field_value(0)
        if case_key is None:
            return

        self.parent.parent.open_medical_record(case_key)
