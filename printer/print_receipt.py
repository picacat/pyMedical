#!/usr/bin/env python3
#coding: utf-8

from libs import printer_utils


# 列印掛號收據 2018.02.26
class PrintReceipt:
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
        selected_item = printer_utils.get_receipt_items(self.database, self.case_key)

        if not selected_item:
            return

        if type(selected_item) is list:
            for item in selected_item:
                if item == '健保醫療收據':
                    printer_utils.print_ins_receipt(
                        self, self.database, self.system_settings,
                        self.case_key, print_type, self.printable
                    )
                else:
                    printer_utils.print_self_receipt(
                        self, self.database, self.system_settings,
                        self.case_key, print_type, self.printable
                    )
        elif selected_item == '健保醫療收據':
            printer_utils.print_ins_receipt(
                self, self.database, self.system_settings,
                self.case_key, print_type, self.printable
            )
        else:
            printer_utils.print_self_receipt(
                self, self.database, self.system_settings,
                self.case_key, print_type, self.printable
            )

