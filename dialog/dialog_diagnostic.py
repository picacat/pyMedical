#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui
from libs import ui_settings
from libs import system
from PyQt5.QtCore import QSettings, QSize, QPoint
from dialog import dialog_symptom


# 主視窗
class DialogDiagnostic(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogDiagnostic, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.dialog_type = args[2]
        self.text_edit = args[3]

        self.settings = QSettings('__settings.ini', QSettings.IniFormat)
        self.ui = None

        self._set_ui()
        self._set_signal()
        self.read_dictionary()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.settings.setValue("dialog_diagnostic_size", self.size())
        self.settings.setValue("dialog_diagnostic_pos", self.pos())

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_DIAGNOSTIC, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system.set_css(self)
        system.set_theme(self.ui, self.system_settings)

        self.ui.resize(self.settings.value("dialog_diagnostic_size", QSize(858, 769)))
        self.ui.move(self.settings.value("dialog_diagnostic_pos", QPoint(1054, 225)))

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('關閉')

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def accepted_button_clicked(self):
        self.close()

    def read_dictionary(self):
        if self.dialog_type == '主訴':
            sql = 'SELECT * FROM dict_groups WHERE DictGroupsType = "主訴類別" ORDER BY DictGroupsKey'
            rows = self.database.select_record(sql)
            for row in rows:
                groups_name = row['DictGroupsName']
                self.ui.tabWidget_diagnostic.addTab(
                    dialog_symptom.DialogSymptom(
                        self, self.database, self.system_settings, groups_name, self.text_edit),
                    groups_name)
