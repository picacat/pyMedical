#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtChart, QtCore
import datetime

from classes import table_widget
from libs import ui_utils
from libs import examination_util
from libs import string_utils
from libs import personnel_utils
from libs import case_utils
from libs import system_utils
from libs import date_utils
from libs import number_utils


# 病歷檢驗資料 2019.08/14
class MedicalRecordExamination(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MedicalRecordExamination, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.patient_key = args[2]

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MEDICAL_RECORD_EXAMINATION, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_examination_item = table_widget.TableWidget(
            self.ui.tableWidget_examination_item, self.database
        )
        self.table_widget_test_result = table_widget.TableWidget(
            self.ui.tableWidget_test_result, self.database
        )
        self._set_table_width()
        self._set_examination_groups()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_groups.itemSelectionChanged.connect(self._groups_changed)
        self.ui.tableWidget_examination_item.itemSelectionChanged.connect(self._examination_item_changed)

    def _set_table_width(self):
        width = [152, 152]
        self.table_widget_examination_item.set_table_heading_width(width)

        width = [150, 150]
        self.table_widget_test_result.set_table_heading_width(width)

    def _set_examination_groups(self):
        examination_groups = []
        for row in examination_util.EXAMINATION_LIST:
            groups = row[0]
            if groups not in examination_groups:
                examination_groups.append(groups)

        row_count = len(examination_groups)
        self.ui.tableWidget_groups.setRowCount(0)

        column_count = self.ui.tableWidget_groups.columnCount()
        total_row = int(row_count / column_count)
        if row_count % column_count > 0:
            total_row += 1

        for row_no in range(0, total_row):
            self.ui.tableWidget_groups.setRowCount(
                self.ui.tableWidget_groups.rowCount() + 1
            )
            for col_no in range(0, column_count):
                index = (row_no * column_count) + col_no
                if index >= row_count:
                    break

                self.ui.tableWidget_groups.setItem(
                    row_no, col_no, QtWidgets.QTableWidgetItem(examination_groups[index])
                )

        self.ui.tableWidget_groups.resizeRowsToContents()
        self.ui.tableWidget_groups.setCurrentCell(0, 0)
        groups = self.ui.tableWidget_groups.selectedItems()[0].text()
        self._set_examination_items(groups)

    def _groups_changed(self):
        if not self.ui.tableWidget_groups.selectedItems():
            return

        groups = self.ui.tableWidget_groups.selectedItems()[0].text()
        self._set_examination_items(groups)

    def _set_examination_items(self, groups):
        examination_item_list = []
        for row in examination_util.EXAMINATION_LIST:
            if row[0] == groups:
                examination_item_list.append([row[1], row[2]])

        row_count = len(examination_item_list)
        self.ui.tableWidget_examination_item.setRowCount(row_count)
        for row_no, row in zip(range(len(examination_item_list)), examination_item_list):
            for col_no in range(len(row)):
                self.ui.tableWidget_examination_item.setItem(
                    row_no, col_no,
                    QtWidgets.QTableWidgetItem(row[col_no])
                )

        self.ui.tableWidget_examination_item.resizeRowsToContents()
        self.ui.tableWidget_examination_item.setCurrentCell(0, 0)
        self.ui.tableWidget_examination_item.setFocus(True)
        self._examination_item_changed()

    def _examination_item_changed(self):
        current_row = self.ui.tableWidget_examination_item.currentRow()
        item_name = self.ui.tableWidget_examination_item.item(current_row, 1)
        if item_name is None:
            return

        item_name = item_name.text()
        self._read_examination_item(item_name)

    def _read_examination_item(self, item_name):
        sql = '''
            SELECT * FROM examination_item
            WHERE
                PatientKey = {patient_key} AND
                ExaminationItem = "{examination_item}"
            ORDER BY ExaminationDate
        '''.format(
            patient_key=self.patient_key,
            examination_item=item_name,
        )
        self.table_widget_test_result.set_db_data(sql, self._set_table_data)
        self._plot_chart()

    def _set_table_data(self, row_no, row):
        examination_item_row = [
            string_utils.xstr(row['ExaminationDate']),
            string_utils.xstr(row['TestResult']),
        ]

        for col_no in range(len(examination_item_row)):
            self.ui.tableWidget_test_result.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(examination_item_row[col_no])
            )

    def _plot_chart(self):
        while self.ui.verticalLayout_chart.count():
            item = self.ui.verticalLayout_chart.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._plot_test_result()

    def _plot_test_result(self):
        series = QtChart.QLineSeries()

        for row_no in range(self.ui.tableWidget_test_result.rowCount()):
            item = self.ui.tableWidget_test_result.item(row_no, 1)
            if item is None:
                continue

            test_result = item.text()
            try:
                series.append(row_no, number_utils.get_float(test_result))
            except:
                pass

        chart = QtChart.QChart()
        chart.legend().hide()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setTitle('檢驗結果')
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        # axis_y = QtChart.QValueAxis()
        # chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
        # series.attachAxis(axis_y)
        # axis_y.setRange(0, 200)
        #
        # axis_y = QtChart.QCategoryAxis()
        # axis_y.append('過低', 90)
        # axis_y.append('正常', 180)
        # axis_y.setLinePenColor(series.pen().color())
        # axis_y.setGridLinePen((series.pen()))
        # chart.addAxis(axis_y, QtCore.Qt.AlignRight)
        # series.attachAxis(axis_y)

        self.chartView = QtChart.QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedWidth(1000)
        self.ui.verticalLayout_chart.addWidget(self.chartView)
