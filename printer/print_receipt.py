#!/usr/bin/env python3
#coding: utf-8

from libs import printer_utils
from libs import number_utils


# 列印掛號收據 2018.02.26
class PrintReceipt:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        try:
            self.print_option = args[3]
        except IndexError:
            self.print_option = None

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
        selected_item, selected_medicine_set = printer_utils.get_medicine_set_items(
            self.database, self.case_key, '收據', self.print_option)

        if not selected_item:
            return

        if selected_item == '全部收據':
            for item in selected_medicine_set:
                if item == '健保收據':
                    printer_utils.print_ins_receipt(
                        self, self.database, self.system_settings,
                        self.case_key, print_type, self.print_option
                    )
                else:
                    medicine_set = number_utils.get_integer(item.split('自費收據')[1]) + 1
                    printer_utils.print_self_receipt(
                        self, self.database, self.system_settings,
                        self.case_key, medicine_set, print_type, self.print_option
                    )
        elif selected_item == '健保收據':
            printer_utils.print_ins_receipt(
                self, self.database, self.system_settings,
                self.case_key, print_type, self.print_option
            )
        else:
            printer_utils.print_self_receipt(
                self, self.database, self.system_settings,
                self.case_key, selected_medicine_set, print_type, self.print_option
            )

