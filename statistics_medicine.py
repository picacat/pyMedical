#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets

from libs import ui_utils
from libs import system_utils
from libs import string_utils
from dialog import dialog_statistics_doctor

import statistics_medicine_sales


# 用藥統計 2019.08.02
class StatisticsMedicine(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsMedicine, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.dialog_setting = {
            "dialog_executed": False,
            "start_date": None,
            "end_date": None,
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_MEDICINE, self)
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

            dialog.ui.comboBox_doctor.setCurrentText(self.dialog_setting['doctor'])

        if not dialog.exec_():
            dialog.deleteLater()
            return

        start_date = dialog.start_date()
        end_date = dialog.end_date()
        ins_type = dialog.ins_type()
        doctor = dialog.ui.comboBox_doctor.currentText()

        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['start_date'] = dialog.ui.dateEdit_start_date.date()
        self.dialog_setting['end_date'] = dialog.ui.dateEdit_end_date.date()
        self.dialog_setting['ins_type'] = ins_type
        self.dialog_setting['doctor'] = doctor

        dialog.deleteLater()
        self._set_tab_widget(start_date, end_date, ins_type, doctor)

    def _set_tab_widget(self, start_date, end_date, ins_type, doctor):
        self.ui.statusbar.showMessage(
            ' 統計期間: 從 {start_date} 至 {end_date} 保險: {ins_type} 醫師: {doctor}'.format(
                start_date=start_date[:10],
                end_date=end_date[:10],
                ins_type=ins_type,
                doctor=doctor,
            )
        )

        sql = '''
            SELECT MedicineType FROM prescript
                LEFT JOIN cases ON prescript.CaseKey = cases.CaseKey
            WHERE
                cases.CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                MedicineType IS NOT NULL AND
                MedicineType NOT IN ("穴道", "處置", "檢驗")
            GROUP BY MedicineType 
            ORDER BY FIELD(MedicineType, "高貴", "外用", "水藥", "複方", "單方") DESC
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )
        rows = self.database.select_record(sql)

        self.ui.tabWidget_statistics_medicine.clear()
        for row in rows:
            self._add_statistic_medicine_sales(
                start_date, end_date, ins_type, doctor, string_utils.xstr(row['MedicineType'])
            )

    # 用藥統計內容
    def _add_statistic_medicine_sales(self, start_date, end_date, ins_type, doctor, medicine_type):
        self.tab_statistics_medicine_sales = statistics_medicine_sales.StatisticsMedicineSales(
            self, self.database, self.system_settings,
            start_date, end_date, ins_type, doctor, medicine_type,
        )
        self.tab_statistics_medicine_sales.start_calculate()
        self.ui.tabWidget_statistics_medicine.addTab(self.tab_statistics_medicine_sales, medicine_type)

    def _export_to_excel(self):
        current_index = self.ui.tabWidget_statistics_medicine.currentIndex()
        current_tab = self.ui.tabWidget_statistics_medicine.widget(current_index)

        current_tab.export_to_excel()

