#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from libs import ui_utils


# 樣板 2018.01.31
class Template(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Template, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_TEMPLATE, self)

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
    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_prescript.keyPressEvent = self._table_widget_prescript_key_press

    def _table_widget_prescript_key_press(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Delete:
            print('delete')
        elif key == QtCore.Qt.Key_Up:
            current_row = self.ui.tableWidget_prescript.currentRow()
            if self.ui.tableWidget_prescript.item(current_row, 1) is None:
                self.ui.tableWidget_prescript.removeRow(current_row)
                return
        elif key == QtCore.Qt.Key_Down:
            current_row = self.ui.tableWidget_prescript.currentRow()
            if current_row == self.ui.tableWidget_prescript.rowCount() - 1 and \
                    self.ui.tableWidget_prescript.item(current_row, 1) is not None:
                self.append_null_medicine()

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_prescript, event)
"""


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = Template()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
