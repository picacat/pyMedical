#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtPrintSupport
from PyQt5.QtPrintSupport import QPrinter


# 列印掛號收據 2018.02.26
class PrintRegistration:
    # 初始化
    def __init__(self, case_key, *args):
        self.case_key = case_key
        self.database = args[0]
        self.system_settings = args[1]
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

    def printing(self):
        printer = QPrinter()
        printer.setPrinterName('med printer')
        printer.setPageSize(QPrinter.Letter)

        dialog = QtPrintSupport.QPrintDialog(printer)

        document = QtGui.QTextDocument()
        document.setHtml(self._get_print_content())
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return

        document.print(printer)

    def _get_print_content(self):
        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(self.case_key)
        row = self.database.select_record(sql)[0]
        html = '<b><font size="4">門診掛號單</font></b><br>'
        html += '<b>病患姓名</b>: {0}'.format(row['Name'])
        html += "<table cellspacing=0 cellpadding=2 style='border-width: 1; border-style: solid; border-color: #000000'>";
        html += "<tr>";
        html += "<td>1</td>";
        html += "<td>2</td>";
        html += "<td>3</td>";
        html += "</tr>";
        html += "<tr>";
        html += "<td>One</td>";
        html += "<td>Two</td>";
        html += "<td>Three</td>";
        html += "</tr>";
        html += "<tr>";
        html += "<td></td>";
        html += "<td></td>";
        html += "<td>Finish</td>";
        html += "</tr>";
        html += "</table></body></html>";
        return html
