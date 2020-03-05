#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
import datetime

from libs import system_utils
from libs import ui_utils
from libs import number_utils


# 主視窗
class DialogInsCheck(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInsCheck, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INS_CHECK, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self._set_combo_box()
        self.ui.spinBox_diag_limit.setValue(number_utils.get_integer(self.system_settings.field('首次警告次數')))
        self.ui.spinBox_treat_limit.setValue(number_utils.get_integer(self.system_settings.field('針傷警告次數')))

        for combo_box in self.findChildren(QtWidgets.QComboBox):
            combo_box.setView(QtWidgets.QListView())

    def _set_combo_box(self):
        year_list = []
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        for i in range(current_year, current_year - 10, -1):
            year_list.append(str(i))

        ui_utils.set_combo_box(self.ui.comboBox_year, year_list)
        ui_utils.set_combo_box(
            self.ui.comboBox_month,
            [str(x) for x in range(1, 13)]
        )
        self.ui.comboBox_year.setCurrentText(str(current_year))
        self.ui.comboBox_month.setCurrentText(str(current_month))

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.toolButton_select_all.clicked.connect(self._select_all_check_box)

    def accepted_button_clicked(self):
        pass

    def _select_all_check_box(self):
        check_box_list = [
            self.ui.checkBox_check_errors,
            self.ui.checkBox_check_course,
            self.ui.checkBox_check_card,
            self.ui.checkBox_check_medical_record_count,
            self.ui.checkBox_check_prescript_days,
            self.ui.checkBox_check_ins_drug,
            self.ui.checkBox_check_ins_treat,
        ]

        for check_box in check_box_list:
            check_box.setChecked(not check_box.isChecked())
