#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5 import QtPrintSupport
from libs import string_utils
from libs import printer_utils
from printer import print_registration_form1
from printer import print_registration_form2


# 列印掛號收據 2018.02.26
class PrintRegistration:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.ui = None

        self._set_ui()
        self.registration_form_dict = {
            '01': print_registration_form1.PrintRegistrationForm1,
            '02': print_registration_form2.PrintRegistrationForm2,
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
        if self.system_settings.field('列印門診掛號單') == '不印':
            return

        if self.system_settings.field('列印門診掛號單') == '詢問':
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec() == QtWidgets.QDialog.Rejected:
                return

        form = self.system_settings.field('門診掛號單格式')
        if form not in printer_utils.PRINT_REGISTRATION_FORM:
            return

        form = string_utils.xstr(form).split('-')[0]
        print_registration_form = self.registration_form_dict[form](
            self, self.database, self.system_settings, self.case_key)
        print_registration_form.print()

        del print_registration_form

    def preview(self):
        form = self.system_settings.field('門診掛號單格式')
        if form not in printer_utils.PRINT_REGISTRATION_FORM:
            return

        form = string_utils.xstr(form).split('-')[0]
        print_registration_form = self.registration_form_dict[form](
            self, self.database, self.system_settings, self.case_key)
        print_registration_form.preview()

        del print_registration_form
