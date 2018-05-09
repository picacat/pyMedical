#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from libs import ui_settings


# 樣板 2018.01.31
class DictDiagnostic(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictDiagnostic, self).__init__(parent)
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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DICT_DIAGNOSTIC, self)

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_template)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_template(self):
        self.close_all()
        self.close_tab()

"""
    def _set_signal(self):
        self.ui.tableWidget_regist_fee.keyPressEvent = self._table_widget_key_press

    def _table_widget_key_press(self, event):
        key = event.key()
        if key == Qt.Key_Delete:
            print('delete')
        elif key == Qt.Key_Up:
            current_row = self.ui.tableWidget_regist_fee.currentRow()
            if self.ui.tableWidget_regist_fee.item(current_row, 2).text() == '':
                self.ui.tableWidget_regist_fee.removeRow(current_row)
                return
        elif key == Qt.Key_Down:
            current_row = self.ui.tableWidget_regist_fee.currentRow()
            if current_row == self.ui.tableWidget_regist_fee.rowCount() - 1 and \
                    self.ui.tableWidget_regist_fee.item(current_row, 2).text() != '':
                self._add_row()

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_regist_fee, event)
"""


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = DictDiagnostic()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
