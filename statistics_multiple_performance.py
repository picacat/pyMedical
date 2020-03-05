#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore

from libs import ui_utils
from libs import system_utils
from dialog import dialog_date_picker
import statistics_multiple_performance_week_person
import statistics_multiple_performance_week_income
import statistics_multiple_performance_week_project
import statistics_multiple_performance_week_doctor


# 綜合業績報表 2020.02.15
class StatisticsMultiplePerformance(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsMultiplePerformance, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.dialog_setting = {
            "dialog_executed": False,
            "year": None,
            "month": None,
        }

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_MULTIPLE_PERFORMANCE, self)
        system_utils.set_css(self, self.system_settings)

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_form)
        self.ui.action_open_dialog.triggered.connect(self.open_dialog)
        self.ui.action_export_excel.triggered.connect(self._export_to_excel)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_form(self):
        self.close_all()
        self.close_tab()

    # 讀取病歷
    def open_dialog(self):
        dialog = dialog_date_picker.DialogDatePicker(self, self.database, self.system_settings)

        if self.dialog_setting['dialog_executed']:
            dialog.ui.comboBox_year.setCurrentText(self.dialog_setting['year'])
            dialog.ui.comboBox_month.setCurrentText(self.dialog_setting['month'])

        if not dialog.exec_():
            dialog.deleteLater()
            return

        year = dialog.ui.comboBox_year.currentText()
        month = dialog.ui.comboBox_month.currentText()

        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['year'] = year
        self.dialog_setting['month'] = month

        dialog.deleteLater()
        self._set_tab_widget(year, month)

    def _set_tab_widget(self, year, month):
        self.ui.tabWidget_statistics.clear()

        self.ui.statusbar.showMessage(
            ' 統計期間: {year}年 {month}月'.format(
                year=year,
                month=month,
            )
        )

        self._add_statistic_week_person(year, month)
        self._add_statistic_week_income(year, month)
        self._add_statistic_week_project(year, month)
        self._add_statistic_week_doctor(year, month)

    # 週人數統計
    def _add_statistic_week_person(self, year, month):
        self.tab_statistics_week_person = \
            statistics_multiple_performance_week_person.StatisticsMultiplePerformanceWeekPerson(
                self, self.database, self.system_settings, year, month,
            )
        self.tab_statistics_week_person.start_calculate()
        self.ui.tabWidget_statistics.addTab(self.tab_statistics_week_person, '週人數統計表')

    # 週收入統計
    def _add_statistic_week_income(self, year, month):
        self.tab_statistics_week_income = \
            statistics_multiple_performance_week_income.StatisticsMultiplePerformanceWeekIncome(
                self, self.database, self.system_settings, year, month,
            )
        self.tab_statistics_week_income.start_calculate()
        self.ui.tabWidget_statistics.addTab(self.tab_statistics_week_income, '週收入統計表')

    # 週專案統計
    def _add_statistic_week_project(self, year, month):
        self.tab_statistics_week_project = \
            statistics_multiple_performance_week_project.StatisticsMultiplePerformanceWeekProject(
                self, self.database, self.system_settings, year, month,
            )
        self.tab_statistics_week_project.start_calculate()
        self.ui.tabWidget_statistics.addTab(self.tab_statistics_week_project, '週專案統計表')

    # 週專案統計
    def _add_statistic_week_doctor(self, year, month):
        self.tab_statistics_week_doctor = \
            statistics_multiple_performance_week_doctor.StatisticsMultiplePerformanceWeekDoctor(
                self, self.database, self.system_settings, year, month,
            )
        self.tab_statistics_week_doctor.start_calculate()
        self.ui.tabWidget_statistics.addTab(self.tab_statistics_week_doctor, '週醫師統計表')

    def _export_to_excel(self):
        if self.ui.tabWidget_statistics_doctor.currentIndex() == 0:
            self.tab_statistics_doctor_count.export_to_excel()
        elif self.ui.tabWidget_statistics_doctor.currentIndex() == 1:
            self.tab_statistics_doctor_income.export_to_excel()
        elif self.ui.tabWidget_statistics_doctor.currentIndex() == 2:
            self.tab_statistics_doctor_sale.export_to_excel()


