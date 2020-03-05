#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore

from libs import ui_utils
from libs import system_utils
from dialog import dialog_ins_date_doctor

import statistics_ins_performance_medical_record


# 健保申報業績 2019.12.02
class StatisticsInsPerformance(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsInsPerformance, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.dialog_setting = {
            "dialog_executed": False,
            "start_date": None,
            "end_date": None,
            "therapist": None,
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_INS_PERFORMANCE, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)

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
        dialog = dialog_ins_date_doctor.DialogInsDateDoctor(
            self, self.database, self.system_settings, '健保申報業績',
        )

        if self.dialog_setting['dialog_executed']:
            dialog.ui.dateEdit_start_date.setDate(self.dialog_setting['start_date'])
            dialog.ui.dateEdit_end_date.setDate(self.dialog_setting['end_date'])
            dialog.ui.comboBox_doctor.setCurrentText(self.dialog_setting['therapist'])

        if not dialog.exec_():
            dialog.deleteLater()
            return

        start_date = dialog.start_date()
        end_date = dialog.end_date()
        doctor = dialog.ui.comboBox_doctor.currentText()

        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['start_date'] = dialog.ui.dateEdit_start_date.date()
        self.dialog_setting['end_date'] = dialog.ui.dateEdit_end_date.date()
        self.dialog_setting['therapist'] = doctor

        dialog.deleteLater()
        self._set_tab_widget(start_date, end_date, doctor)

    def _set_tab_widget(self, start_date, end_date, doctor):
        self.ui.tabWidget_ins_performance.clear()

        self.ui.statusbar.showMessage(
            ' 統計期間: 從 {start_date} 至 {end_date} 醫師: {doctor}'.format(
                start_date=start_date[:10],
                end_date=end_date[:10],
                doctor=doctor,
            )
        )

        self._add_statistic_ins_performance_medical_record(start_date, end_date, doctor)
        # database._add_statistic_massage_income(start_date, end_date, period, ins_type, therapist)
        # database._add_statistic_massage_sale(start_date, end_date, period, therapist)

    # 醫師門診人數統計
    def _add_statistic_ins_performance_medical_record(self, start_date, end_date, doctor):
        self.tab_ins_performance_medical_record = statistics_ins_performance_medical_record.\
            StatisticsInsPerformanceMedicalRecord(
                self, self.database, self.system_settings,
                start_date, end_date, doctor,
        )
        self.tab_ins_performance_medical_record.start_calculate()
        self.ui.tabWidget_ins_performance.addTab(self.tab_ins_performance_medical_record, '健保業績-依病歷')
    #
    # # 醫師門診收入統計
    # def _add_statistic_massage_income(database, start_date, end_date, period, ins_type, therapist):
    #     database.tab_statistics_massage_income = statistics_doctor_income.StatisticsDoctorIncome(
    #         database, database.database, database.system_settings,
    #         start_date, end_date, period, ins_type, therapist,
    #     )
    #     database.tab_statistics_massage_income.start_calculate()
    #     database.ui.tabWidget_statistics_doctor.addTab(database.tab_statistics_massage_income, '門診收入統計')
    #
    # # 醫師自費銷售統計
    # def _add_statistic_massage_sale(database, start_date, end_date, period, therapist):
    #     database.tab_statistics_massage_sale = statistics_doctor_sale.StatisticsDoctorSale(
    #         database, database.database, database.system_settings,
    #         start_date, end_date, period, therapist,
    #     )
    #     database.tab_statistics_massage_sale.start_calculate()
    #     database.ui.tabWidget_statistics_doctor.addTab(database.tab_statistics_massage_sale, '自費銷售統計')

    def _export_to_excel(self):
        if self.ui.tabWidget_ins_performance.currentIndex() == 0:
            self.tab_ins_performance_medical_record.export_to_excel()
        # elif database.ui.tabWidget_statistics_doctor.currentIndex() == 1:
        #     database.tab_statistics_massage_income.export_to_excel()
        # elif database.ui.tabWidget_statistics_doctor.currentIndex() == 2:
        #     database.tab_statistics_massage_sale.export_to_excel()


