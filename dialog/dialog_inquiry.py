#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui
from libs import ui_utils
from libs import system_utils
from PyQt5.QtCore import QSettings, QSize, QPoint
from dialog import dialog_symptom
from dialog import dialog_tongue
from dialog import dialog_pulse
from dialog import dialog_remark


# 主視窗
class DialogInquiry(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInquiry, self).__init__(parent)
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
        self.settings.setValue("dialog_inquiry_size", self.size())
        self.settings.setValue("dialog_inquiry_pos", self.pos())

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INQUIRY, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        system_utils.set_theme(self.ui, self.system_settings)

        self.ui.resize(self.settings.value("dialog_inquiry_size", QSize(858, 769)))
        self.ui.move(self.settings.value("dialog_inquiry_pos", QPoint(846, 215)))

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
                self.ui.tabWidget_inquiry.addTab(
                    dialog_symptom.DialogSymptom(
                        self, self.database, self.system_settings, groups_name, self.text_edit),
                    groups_name)
        elif self.dialog_type == '舌診':
            sql = 'SELECT * FROM dict_groups WHERE DictGroupsType = "舌診類別" ORDER BY DictGroupsKey'
            rows = self.database.select_record(sql)
            for row in rows:
                groups_name = row['DictGroupsName']
                self.ui.tabWidget_inquiry.addTab(
                    dialog_tongue.DialogTongue(
                        self, self.database, self.system_settings, groups_name, self.text_edit),
                    groups_name)
        elif self.dialog_type == '脈象':
            sql = 'SELECT * FROM dict_groups WHERE DictGroupsType = "脈象類別" ORDER BY DictGroupsKey'
            rows = self.database.select_record(sql)
            for row in rows:
                groups_name = row['DictGroupsName']
                self.ui.tabWidget_inquiry.addTab(
                    dialog_pulse.DialogPulse(
                        self, self.database, self.system_settings, groups_name, self.text_edit),
                    groups_name)
        elif self.dialog_type == '備註':
            sql = 'SELECT * FROM dict_groups WHERE DictGroupsType = "備註類別" ORDER BY DictGroupsKey'
            rows = self.database.select_record(sql)
            for row in rows:
                groups_name = row['DictGroupsName']
                self.ui.tabWidget_inquiry.addTab(
                    dialog_remark.DialogRemark(
                        self, self.database, self.system_settings, groups_name, self.text_edit),
                    groups_name)
