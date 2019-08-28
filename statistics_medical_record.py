#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets

from libs import ui_utils
from libs import system_utils
from dialog import dialog_statistics_doctor
import statistics_medical_record_diag_time_length


# 病歷統計 2019.06.10
class StatisticsMedicalRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsMedicalRecord, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_MEDICAL_RECORD, self)
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
        self.ui.tabWidget_statistics_medical_record.clear()

        self.ui.statusbar.showMessage(
            ' 統計期間: 從 {start_date} 至 {end_date} 保險: {ins_type} 醫師: {doctor}'.format(
                start_date=start_date[:10],
                end_date=end_date[:10],
                ins_type=ins_type,
                doctor=doctor,
            )
        )

        self._add_statistic_medical_record_diag_time_length(start_date, end_date, ins_type, doctor)

    # 醫師門診人數統計
    def _add_statistic_medical_record_diag_time_length(self, start_date, end_date, ins_type, doctor):
        self.tab_statistics_medical_record_diag_time_length = \
            statistics_medical_record_diag_time_length.StatisticsMedicalRecordDiagTimeLength(
                self, self.database, self.system_settings,
                start_date, end_date, ins_type, doctor,
            )
        self.tab_statistics_medical_record_diag_time_length.start_calculate()
        self.ui.tabWidget_statistics_medical_record.addTab(
            self.tab_statistics_medical_record_diag_time_length, '看診時間統計'
        )

    def _export_to_excel(self):
        if self.ui.tabWidget_statistics_medical_record.currentIndex() == 0:
            self.tab_statistics_medical_record_diag_time_length.export_to_excel()


