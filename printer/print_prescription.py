#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QInputDialog
from PyQt5 import QtPrintSupport
from libs import string_utils
from libs import printer_utils
from libs import dialog_utils
from libs import number_utils

from printer import print_prescription_ins_form1


# 列印掛號收據 2018.02.26
class PrintPrescription:
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
        self.prescription_ins_form_dict = {
            '01': print_prescription_ins_form1.PrintPrescriptionInsForm1,
        }

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
        item, medicine_set = self._get_medicine_set_items()
        if not item:
            return

        if item == '全部處方':
            for i in medicine_set:
                if i == '健保處方':
                    self._print_ins_prescript(print_type)
                else:
                    med_set = number_utils.get_integer(i.split('自費處方')[1])
                    print('列印自費處方', med_set)
        elif item == '健保處方':
            self._print_ins_prescript(print_type)
        else:
            print('列印自費處方', medicine_set)

    def _print_ins_prescript(self, print_type):
        if self.printable is None:
            self.printable = self.system_settings.field('列印健保處方箋')

        if self.printable == '不印':
            return

        if self.system_settings.field('列印健保處方箋') == '詢問':
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec() == QtWidgets.QDialog.Rejected:
                return

        form = self.system_settings.field('健保處方箋格式')
        if form not in printer_utils.PRINT_PRESCRIPTION_INS_FORM:
            return

        form = string_utils.xstr(form).split('-')[0]
        print_prescription_form = self.prescription_ins_form_dict[form](
            self, self.database, self.system_settings, self.case_key)
        if print_type == 'print':
            print_prescription_form.print()
        else:
            print_prescription_form.preview()

        del print_prescription_form

    def _get_medicine_set_items(self):
        sql = '''
            SELECT InsType FROM cases
            WHERE
                CaseKey = {0}
        '''.format(self.case_key)
        rows = self.database.select_record(sql)
        ins_type = rows[0]['InsType']

        sql = '''
            SELECT MedicineSet FROM prescript
            WHERE
                CaseKey = {0}
            GROUP BY MedicineSet
            ORDER BY MedicineSet
        '''.format(self.case_key)

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return ('{0}處方'.format(ins_type), None)
        elif len(rows) == 1:
            medicine_set = rows[0]['MedicineSet']
            if medicine_set == 1:
                item = '健保處方'
            else:
                item = '自費處方'
                medicine_set = medicine_set - 1

            return (item, medicine_set)

        items = ['全部處方']
        for row in rows:
            medicine_set = row['MedicineSet']
            if medicine_set == 1:
                items.append('健保處方')
            else:
                items.append('自費處方{0}'.format(medicine_set-1))

        input_dialog = dialog_utils.get_dialog(
            '多重處方', '請選擇欲列印的處方箋',
            None, QInputDialog.TextInput, 320, 200)
        input_dialog.setComboBoxItems(items)
        ok = input_dialog.exec_()

        if not ok:
            return False, None

        item = input_dialog.textValue()
        if item == '全部處方':
            del items[0]
            return (item, items)
        elif item == '健保處方':
            medicine_set = 1
        else:
            medicine_set = number_utils.get_integer(item.split('自費處方')[1])
            item = '自費處方'

        return (item, medicine_set)
