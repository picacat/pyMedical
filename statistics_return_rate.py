#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets

from libs import ui_utils
from dialog import dialog_statistics_return_rate
import statistics_return_rate_doctor
import statistics_return_rate_massager


# 醫師統計 2019.05.02
class StatisticsReturnRate(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsReturnRate, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_RETURN_RATE, self)

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
        dialog = dialog_statistics_return_rate.DialogStatisticsReturnRate(
            self, self.database, self.system_settings
        )

        if not dialog.exec_():
            dialog.deleteLater()
            return

        start_date = dialog.start_date()
        end_date = dialog.end_date()
        ins_type = dialog.ins_type()
        treat_type = dialog.treat_type()
        visit = dialog.visit()
        doctor = dialog.ui.comboBox_doctor.currentText()
        massager = dialog.ui.comboBox_massager.currentText()
        doctor_return_days = dialog.ui.comboBox_doctor_return_days.currentText()
        massager_return_days = dialog.ui.comboBox_massager_return_days.currentText()

        dialog.deleteLater()
        self._set_tab_widget(
            start_date, end_date, ins_type, treat_type, visit, doctor, massager,
            doctor_return_days, massager_return_days,
        )

    def _set_tab_widget(self, start_date, end_date, ins_type, treat_type, visit, doctor, massager,
                        doctor_return_days, massager_return_days):
        self.ui.tabWidget_statistics_return_rate.clear()

        self.ui.statusbar.showMessage(
            '''統計期間: 從 {start_date} 至 {end_date}, 保險: {ins_type}, 類別: {treat_type} 
            醫師: {doctor}, 醫師回診天數: {return_days} 推拿師父: {massager}, 推拿回診天數: {massager_return_days}'''.format(
                start_date=start_date[:10],
                end_date=end_date[:10],
                ins_type=ins_type,
                treat_type=treat_type,
                doctor=doctor,
                return_days=doctor_return_days,
                massager=massager,
                massager_return_days=massager_return_days,
            )
        )

        self._add_statistic_doctor_count(
            start_date, end_date, ins_type, treat_type, visit, doctor, doctor_return_days,
        )
        self._add_statistic_massager_count(
            start_date, end_date, ins_type, treat_type, visit, massager, massager_return_days,
        )

    # 醫師回診率統計
    def _add_statistic_doctor_count(self, start_date, end_date, ins_type, treat_type, visit,
                                    doctor, doctor_return_days):
        self.tab_statistics_return_rate_doctor = statistics_return_rate_doctor.StatisticsReturnRateDoctor(
            self, self.database, self.system_settings,
            start_date, end_date, ins_type, treat_type, visit, doctor, doctor_return_days,
        )
        self.tab_statistics_return_rate_doctor.start_calculate()
        self.ui.tabWidget_statistics_return_rate.addTab(self.tab_statistics_return_rate_doctor, '醫師回診率')

    # 推拿師父回診率統計
    def _add_statistic_massager_count(self, start_date, end_date, ins_type, treat_type, visit,
                                    massager, massager_return_days):
        self.tab_statistics_return_rate_massager = statistics_return_rate_massager.StatisticsReturnRateMassager(
            self, self.database, self.system_settings,
            start_date, end_date, ins_type, treat_type, visit, massager, massager_return_days,
        )
        self.tab_statistics_return_rate_massager.start_calculate()
        self.ui.tabWidget_statistics_return_rate.addTab(self.tab_statistics_return_rate_massager, '推拿師父回診率')

    def _export_to_excel(self):
        if self.ui.tabWidget_statistics_return_rate.currentIndex() == 0:
            self.tab_statistics_return_rate_doctor.export_to_excel()
        elif self.ui.tabWidget_statistics_return_rate.currentIndex() == 1:
            self.tab_statistics_return_rate_massager.export_to_excel()


