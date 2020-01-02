#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore

from libs import ui_utils
from libs import system_utils
from dialog import dialog_statistics_therapist
import statistics_massage_count
import statistics_massage_income
import statistics_massage_payment
import statistics_massage_sale


# 養生館收入統計 2019.12.05
class StatisticsMassage(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsMassage, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.dialog_setting = {
            "dialog_executed": False,
            "start_date": None,
            "end_date": None,
            "period": None,
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_MASSAGE, self)
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
        dialog = dialog_statistics_therapist.DialogStatisticsTherapist(
            self, self.database, self.system_settings, '推拿師父',
        )

        if self.dialog_setting['dialog_executed']:
            dialog.ui.dateEdit_start_date.setDate(self.dialog_setting['start_date'])
            dialog.ui.dateEdit_end_date.setDate(self.dialog_setting['end_date'])
            dialog.ui.comboBox_period.setCurrentText(self.dialog_setting['period'])
            dialog.ui.comboBox_therapist.setCurrentText(self.dialog_setting['therapist'])

        if not dialog.exec_():
            dialog.deleteLater()
            return

        start_date = dialog.start_date()
        end_date = dialog.end_date()
        period = dialog.period()
        therapist = dialog.therapist()

        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['start_date'] = dialog.ui.dateEdit_start_date.date()
        self.dialog_setting['end_date'] = dialog.ui.dateEdit_end_date.date()
        self.dialog_setting['period'] = period
        self.dialog_setting['therapist'] = therapist

        dialog.deleteLater()
        self._set_tab_widget(start_date, end_date, period, therapist)

    def _set_tab_widget(self, start_date, end_date, period, massager):
        self.ui.tabWidget_statistics_massage.clear()

        self.ui.statusbar.showMessage(
            ' 統計期間: 從 {start_date} 至 {end_date} 班別: {period} 推拿師父: {massager}'.format(
                start_date=start_date[:10],
                end_date=end_date[:10],
                period=period,
                massager=massager,
            )
        )

        self._add_statistic_massager_count(start_date, end_date, period, massager)
        self._add_statistic_massage_income(start_date, end_date, period, massager)
        self._add_statistic_massage_payment(start_date, end_date, period, massager)
        self._add_statistic_massage_sale(start_date, end_date, period, massager)

    # 養生館人數統計
    def _add_statistic_massager_count(self, start_date, end_date, period, massager):
        self.tab_statistics_massage_count = statistics_massage_count.StatisticsMassageCount(
            self, self.database, self.system_settings,
            start_date, end_date, period, massager,
        )
        self.tab_statistics_massage_count.start_calculate()
        self.ui.tabWidget_statistics_massage.addTab(self.tab_statistics_massage_count, '人數統計')

    # 收入統計
    def _add_statistic_massage_income(self, start_date, end_date, period, massager):
        self.tab_statistics_massage_income = statistics_massage_income.StatisticsMassageIncome(
            self, self.database, self.system_settings,
            start_date, end_date, period, massager,
        )
        self.tab_statistics_massage_income.start_calculate()
        self.ui.tabWidget_statistics_massage.addTab(self.tab_statistics_massage_income, '收入統計')

    # 付款統計
    def _add_statistic_massage_payment(self, start_date, end_date, period, massager):
        self.tab_statistics_massage_payment = statistics_massage_payment.StatisticsMassagePayment(
            self, self.database, self.system_settings,
            start_date, end_date, period, massager,
        )
        self.tab_statistics_massage_payment.start_calculate()
        self.ui.tabWidget_statistics_massage.addTab(self.tab_statistics_massage_payment, '付款統計')

    # 醫師自費銷售統計
    def _add_statistic_massage_sale(self, start_date, end_date, period, massager):
        self.tab_statistics_massage_sale = statistics_massage_sale.StatisticsMassageSale(
            self, self.database, self.system_settings,
            start_date, end_date, period, massager,
        )
        self.tab_statistics_massage_sale.start_calculate()
        self.ui.tabWidget_statistics_massage.addTab(self.tab_statistics_massage_sale, '銷售統計')

    def _export_to_excel(self):
        if self.ui.tabWidget_statistics_massage.currentIndex() == 0:
            self.tab_statistics_massage_count.export_to_excel()
        elif self.ui.tabWidget_statistics_massage.currentIndex() == 1:
            self.tab_statistics_massage_income.export_to_excel()
        elif self.ui.tabWidget_statistics_massage.currentIndex() == 2:
            self.tab_statistics_massage_payment.export_to_excel()
        elif self.ui.tabWidget_statistics_massage.currentIndex() == 3:
            self.tab_statistics_massage_sale.export_to_excel()


