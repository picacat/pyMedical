#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore

from libs import ui_utils
from libs import system_utils
from dialog import dialog_statistics_doctor
import statistics_doctor_count
import statistics_doctor_income
import statistics_doctor_sale


# 醫師統計 2019.05.02
class StatisticsDoctor(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsDoctor, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.dialog_setting = {
            "dialog_executed": False,
            "start_date": None,
            "end_date": None,
            "period": None,
            "ins_type": None,
            "doctor": None,
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_DOCTOR, self)
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
        dialog = dialog_statistics_doctor.DialogStatisticsDoctor(
            self, self.database, self.system_settings
        )

        if self.dialog_setting['dialog_executed']:
            dialog.ui.dateEdit_start_date.setDate(self.dialog_setting['start_date'])
            dialog.ui.dateEdit_end_date.setDate(self.dialog_setting['end_date'])

            if self.dialog_setting['ins_type'] == '全部':
                dialog.ui.radioButton_all.setChecked(True)
            elif self.dialog_setting['ins_type'] == '健保':
                dialog.ui.radioButton_ins.setChecked(True)
            elif self.dialog_setting['ins_type'] == '自費':
                dialog.ui.radioButton_self.setChecked(True)

            dialog.ui.comboBox_period.setCurrentText(self.dialog_setting['period'])
            dialog.ui.comboBox_doctor.setCurrentText(self.dialog_setting['doctor'])

        if not dialog.exec_():
            dialog.deleteLater()
            return

        start_date = dialog.start_date()
        end_date = dialog.end_date()
        period = dialog.period()
        ins_type = dialog.ins_type()
        doctor = dialog.ui.comboBox_doctor.currentText()

        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['start_date'] = dialog.ui.dateEdit_start_date.date()
        self.dialog_setting['end_date'] = dialog.ui.dateEdit_end_date.date()
        self.dialog_setting['period'] = period
        self.dialog_setting['ins_type'] = ins_type
        self.dialog_setting['doctor'] = doctor

        dialog.deleteLater()
        self._set_tab_widget(start_date, end_date, period, ins_type, doctor)

    def _set_tab_widget(self, start_date, end_date, period, ins_type, doctor):
        self.ui.tabWidget_statistics_doctor.clear()

        self.ui.statusbar.showMessage(
            ' 統計期間: 從 {start_date} 至 {end_date} {period} 保險: {ins_type} 醫師: {doctor}'.format(
                start_date=start_date[:10],
                end_date=end_date[:10],
                period=period,
                ins_type=ins_type,
                doctor=doctor,
            )
        )

        self._add_statistic_doctor_count(start_date, end_date, period, ins_type, doctor)
        self._add_statistic_doctor_income(start_date, end_date, period, ins_type, doctor)
        self._add_statistic_doctor_sale(start_date, end_date, period, doctor)

    # 醫師門診人數統計
    def _add_statistic_doctor_count(self, start_date, end_date, period, ins_type, doctor):
        self.tab_statistics_doctor_count = statistics_doctor_count.StatisticsDoctorCount(
            self, self.database, self.system_settings,
            start_date, end_date, period, ins_type, doctor,
        )
        self.tab_statistics_doctor_count.start_calculate()
        self.ui.tabWidget_statistics_doctor.addTab(self.tab_statistics_doctor_count, '門診人數統計')

    # 醫師門診收入統計
    def _add_statistic_doctor_income(self, start_date, end_date, period, ins_type, doctor):
        self.tab_statistics_doctor_income = statistics_doctor_income.StatisticsDoctorIncome(
            self, self.database, self.system_settings,
            start_date, end_date, period, ins_type, doctor,
        )
        self.tab_statistics_doctor_income.start_calculate()
        self.ui.tabWidget_statistics_doctor.addTab(self.tab_statistics_doctor_income, '門診收入統計')

    # 醫師自費銷售統計
    def _add_statistic_doctor_sale(self, start_date, end_date, period, doctor):
        self.tab_statistics_doctor_sale = statistics_doctor_sale.StatisticsDoctorSale(
            self, self.database, self.system_settings,
            start_date, end_date, period, doctor,
        )
        self.tab_statistics_doctor_sale.start_calculate()
        self.ui.tabWidget_statistics_doctor.addTab(self.tab_statistics_doctor_sale, '自費銷售統計')

    def _export_to_excel(self):
        if self.ui.tabWidget_statistics_doctor.currentIndex() == 0:
            self.tab_statistics_doctor_count.export_to_excel()
        elif self.ui.tabWidget_statistics_doctor.currentIndex() == 1:
            self.tab_statistics_doctor_income.export_to_excel()
        elif self.ui.tabWidget_statistics_doctor.currentIndex() == 2:
            self.tab_statistics_doctor_sale.export_to_excel()


