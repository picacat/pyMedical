#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton

from libs import ui_utils
from libs import number_utils
from libs import string_utils
from libs import system_utils
import ins_apply_tab
from dialog import dialog_ins_judge
import ins_upload_emr


# 健保抽審 2018.01.31
class InsJudge(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsJudge, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]

        self.apply_year = None
        self.apply_month = None
        self.clinic_id = None
        self.period = '全月'
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_app(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_JUDGE, self)

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_upload_emr.triggered.connect(self._upload_emr)
        self.ui.action_close.triggered.connect(self.close_app)

    def open_medical_record(self, case_key):
        self.parent.open_medical_record(case_key, '健保抽審')

    def open_dialog(self):
        dialog = dialog_ins_judge.DialogInsJudge(self.ui, self.database, self.system_settings)
        if self.apply_year is not None:
            dialog.ui.comboBox_year.setCurrentText(string_utils.xstr(self.apply_year))
            dialog.ui.comboBox_month.setCurrentText(string_utils.xstr(self.apply_month))
            dialog.ui.lineEdit_clinic_id.setText(self.clinic_id)
            dialog.ui.comboBox_period.setCurrentText(self.period)
            dialog.ui.dateEdit_apply.setDate(self.apply_upload_date)
            if self.apply_type == '申報':
                dialog.ui.radioButton_apply.setChecked(True)
            else:
                dialog.ui.radioButton_reapply.setChecked(True)

        if dialog.exec_():
            self.apply_year = number_utils.get_integer(dialog.ui.comboBox_year.currentText())
            self.apply_month = number_utils.get_integer(dialog.ui.comboBox_month.currentText())
            self.clinic_id = dialog.ui.lineEdit_clinic_id.text()
            self.period = dialog.ui.comboBox_period.currentText()

            if dialog.ui.radioButton_apply.isChecked():
                self.apply_type = '申報'  # 申報
            else:
                self.apply_type = '補報'  # 補報

            self.apply_date = '{0:0>3}{1:0>2}'.format(self.apply_year-1911, self.apply_month)
            self.apply_upload_date = dialog.ui.dateEdit_apply.date()
            self._add_ins_apply_tab()

        dialog.close_all()
        dialog.deleteLater()

    def _add_ins_apply_tab(self):
        self.ui.tabWidget_ins_data.clear()

        self.tab_ins_apply_tab = ins_apply_tab.InsApplyTab(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.period, self.apply_type, self.clinic_id
        )

        self.ui.tabWidget_ins_data.addTab(self.tab_ins_apply_tab, '申報資料')


    # 電子化抽審
    def _upload_emr(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('電子化抽審')
        msg_box.setText("<font size='4' color='red'><b>確定上傳電子抽審檔案?</b></font>")
        msg_box.setInformativeText("注意！資料上傳前, 請檢查病歷是否完整!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        upload_emr = msg_box.exec_()
        if not upload_emr:
            return

        ins_emr = ins_upload_emr.InsUploadEMR(
            self, self.database, self.system_settings,
            self.apply_date, self.apply_type,
            self.period, self.clinic_id,
            self.apply_upload_date,
        )

        ins_emr.upload_emr_files()
        del ins_emr

