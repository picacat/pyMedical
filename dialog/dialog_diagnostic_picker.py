#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QSettings, QSize, QPoint

from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils


# 主視窗
class DialogDiagnosticPicker(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogDiagnosticPicker, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.sql = args[2]

        self.settings = QSettings('__settings.ini', QSettings.IniFormat)
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_data()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.settings.setValue("dialog_diagnostic_picker_size", self.size())
        self.settings.setValue("dialog_diagnostic_picker_pos", self.pos())

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_DIAGNOSTIC_PICKER, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)

        self.ui.resize(self.settings.value("dialog_diagnostic_picker_size", QSize(861, 479)))
        self.ui.move(self.settings.value("dialog_diagnostic_picker_pos", QPoint(846, 215)))

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_diagnostic = table_widget.TableWidget(
            self.ui.tableWidget_diagnostic, self.database)
        self.ui.tableWidget_diagnostic.resizeRowsToContents()
        self._set_table_width()
        self.table_widget_diagnostic.set_column_hidden([0])
        self.ui.tableWidget_diagnostic.setFocus()

    def _set_table_width(self):
        width = [1000, 400]
        self.table_widget_diagnostic.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.tableWidget_diagnostic.doubleClicked.connect(self._table_double_clicked)

    def _table_double_clicked(self):
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).animateClick()

    def accepted_button_clicked(self):
        self.clinic_key = self.table_widget_diagnostic.field_value(0)
        self.clinic_name = self.table_widget_diagnostic.field_value(1)
        self.close()

    def _read_data(self):
        self.table_widget_diagnostic.set_db_data(self.sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        diagnostic_row = [
            string_utils.xstr(row['ClinicKey']),
            string_utils.xstr(row['ClinicName']),
        ]

        for column in range(len(diagnostic_row)):
            self.ui.tableWidget_diagnostic.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(diagnostic_row[column])
            )
