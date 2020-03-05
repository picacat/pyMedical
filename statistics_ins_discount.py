#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore

from libs import ui_utils
from libs import system_utils
from dialog import dialog_ins_date_doctor
import statistics_ins_discount_regist_fee
import statistics_ins_discount_diag_share_fee
import statistics_ins_discount_drug_share_fee


# 醫師統計 2019.05.02
class StatisticsInsDiscount(QtWidgets.QMainWindow):
    program_name = '健保門診優惠統計'

    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsInsDiscount, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.user_name = self.system_settings.field('使用者')

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_INS_DISCOUNT, self)
        system_utils.set_css(self, self.system_settings)

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_form)
        self.ui.action_open_dialog.triggered.connect(self.open_dialog)
        self.ui.action_export_excel.triggered.connect(self._export_to_excel)
        self.ui.action_open_medical_record.triggered.connect(self._open_medical_record)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_form(self):
        self.close_all()
        self.close_tab()

    # 讀取病歷
    def open_dialog(self):
        dialog = dialog_ins_date_doctor.DialogInsDateDoctor(
            self, self.database, self.system_settings, '健保門診優惠統計',
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
        self.ui.tabWidget_statistics_ins_discount.clear()

        self.ui.statusbar.showMessage(
            ' 統計期間: 從 {start_date} 至 {end_date} 醫師: {doctor}'.format(
                start_date=start_date[:10],
                end_date=end_date[:10],
                doctor=doctor,
            )
        )

        self._add_statistic_ins_discount_regist_fee(start_date, end_date, doctor)
        self._add_statistic_ins_discount_diag_share_fee(start_date, end_date, doctor)
        self._add_statistic_ins_discount_drug_share_fee(start_date, end_date, doctor)

    # 掛號費優待統計
    def _add_statistic_ins_discount_regist_fee(self, start_date, end_date, doctor):
        self.tab_statistics_ins_discount_regist_fee = statistics_ins_discount_regist_fee.StatisticsInsDiscountRegistFee(
            self, self.database, self.system_settings,
            start_date, end_date, doctor,
        )
        self.tab_statistics_ins_discount_regist_fee.start_calculate()
        self.ui.tabWidget_statistics_ins_discount.addTab(
            self.tab_statistics_ins_discount_regist_fee, '掛號費優待統計'
        )

    # 門診負擔優待統計
    def _add_statistic_ins_discount_diag_share_fee(self, start_date, end_date, doctor):
        self.tab_statistics_ins_discount_diag_share_fee = statistics_ins_discount_diag_share_fee.StatisticsInsDiscountDiagShareFee(
            self, self.database, self.system_settings,
            start_date, end_date, doctor,
        )
        self.tab_statistics_ins_discount_diag_share_fee.start_calculate()
        self.ui.tabWidget_statistics_ins_discount.addTab(
            self.tab_statistics_ins_discount_diag_share_fee, '免收門診負擔統計'
        )

    # 藥品負擔優待統計
    def _add_statistic_ins_discount_drug_share_fee(self, start_date, end_date, doctor):
        self.tab_statistics_ins_discount_drug_share_fee = statistics_ins_discount_drug_share_fee.StatisticsInsDiscountDrugShareFee(
            self, self.database, self.system_settings,
            start_date, end_date, doctor,
        )
        self.tab_statistics_ins_discount_drug_share_fee.start_calculate()
        self.ui.tabWidget_statistics_ins_discount.addTab(
            self.tab_statistics_ins_discount_drug_share_fee, '免收藥品負擔統計'
        )

    def _export_to_excel(self):
        if self.ui.tabWidget_statistics_ins_discount.currentIndex() == 0:
            self.tab_statistics_ins_discount_regist_fee.export_to_excel()
        elif self.ui.tabWidget_statistics_ins_discount.currentIndex() == 1:
            self.tab_statistics_ins_discount_diag_share_fee.export_to_excel()
        elif self.ui.tabWidget_statistics_ins_discount.currentIndex() == 2:
            self.tab_statistics_ins_discount_drug_share_fee.export_to_excel()

    def _open_medical_record(self):
        if self.ui.tabWidget_statistics_ins_discount.currentIndex() == 0:
            tab_widget = self.tab_statistics_ins_discount_regist_fee
        elif self.ui.tabWidget_statistics_ins_discount.currentIndex() == 1:
            tab_widget = self.tab_statistics_ins_discount_diag_share_fee
        elif self.ui.tabWidget_statistics_ins_discount.currentIndex() == 2:
            tab_widget = self.tab_statistics_ins_discount_drug_share_fee
        else:
            return

        tab_widget.open_medical_record()


