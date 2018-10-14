#!/usr/bin/env python3
#coding: utf-8

from libs import printer_utils


# 列印掛號收據 2018.02.26
class PrintRegistration:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        try:
            self.printable = args[3]
        except IndexError:
            self.printable = None

        self.ui = None

        self._set_ui()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        pass

    def print(self):
        self._ready_to_print('print')

    def preview(self):
        self._ready_to_print('preview')

    def _ready_to_print(self, print_type):
        printer_utils.print_registration(
            self, self.database, self.system_settings,
            self.case_key, print_type, self.printable
        )
