#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtCore, QtPrintSupport, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtPrintSupport import QPrinter

from libs import printer_utils
from libs import system_utils

# 列印結帳日報表
# 2019.03.38
class PrintIncome:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.income_date = args[2]
        self.income_period = args[3]
        self.tableWidget_income_list = args[4]
        self.tableWidget_total = args[5]
        self.ui = None

        self.printer = printer_utils.get_printer(self.system_settings, '報表印表機')
        self.preview_dialog = QtPrintSupport.QPrintPreviewDialog(self.printer)
        self.current_print = None

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
        font = system_utils.get_font()
        self.font = QtGui.QFont(font, 8, QtGui.QFont.PreferQuality)

    def _set_signal(self):
        pass

    def print(self):
        self.print_html(True)

    def preview(self):
        geometry = QtWidgets.QApplication.desktop().screenGeometry()

        self.preview_dialog.paintRequested.connect(self.print_html)
        self.preview_dialog.resize(geometry.width(), geometry.height())  # for use in Linux
        self.preview_dialog.setWindowState(QtCore.Qt.WindowMaximized)
        self.preview_dialog.exec_()

    def save_to_pdf(self):
        options = QFileDialog.Options()
        pdf_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "QFileDialog.getSaveFileName()",
            '{0}-{1}-門診現金收入報表.pdf'.format(self.income_date, self.income_period),
            "pdf檔案 (*.pdf);;Text Files (*.txt)", options = options
        )
        if not pdf_file_name:
            return

        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setOutputFileName(pdf_file_name)
        self.print_html(True)

    def print_html(self, printing):
        self.current_print = self.print_html
        self.printer.setOrientation(QPrinter.Landscape)
        self.printer.setPaperSize(QPrinter.A4)

        document = printer_utils.get_document(self.printer, self.font)
        document.setDocumentMargin(5)
        document.setHtml(self._get_html())
        if printing:
            document.print(self.printer)

    def _get_html(self):
        table_income = self._get_table_income_html()
        table_total = self._get_table_total_html()

        html = '''
            <html>
                <body>
                    <h2 align=center>{clinic_name} 門診現金收入日報表</h2>
                    統計日期: {income_date} {period} 
                    {table_income}
                    <br><br>
                    {table_total}
                </body>
            </html>
        '''.format(
            clinic_name=self.system_settings.field('院所名稱'),
            table_income=table_income,
            table_total=table_total,
            income_date=self.income_date,
            period=self.income_period,
        )

        return html

    def _get_table_income_html(self):
        income_rows = ''

        for row_no in range(self.tableWidget_income_list.rowCount()):
            sequence = row_no + 1
            if self.tableWidget_income_list.item(row_no, 4).text() == '合計':
                sequence = ''

            pres_days = self.tableWidget_income_list.item(row_no, 9)
            if pres_days is not None:
                pres_days = pres_days.text()
            else:
                pres_days = '0'

            registrar = self.tableWidget_income_list.item(row_no, 20)
            if registrar is not None:
                registrar = registrar.text()
            else:
                registrar = ''

            cashier = self.tableWidget_income_list.item(row_no, 21)
            if cashier is not None:
                cashier = cashier.text()
            else:
                cashier = ''

            if row_no % 2 > 0:
                bgcolor = '#E3E3E3'
            else:
                bgcolor = 'white'

            income_rows += '''
                <tr bgcolor={bgcolor}>
                    <td align=right>{sequence}</td>
                    <td>{case_date}</td>
                    <td align=center>{period}</td>
                    <td align=right>{patient_key}</td>
                    <td align=center>{name}</td>
                    <td align=center>{ins_type}</td>
                    <td align=center>{share_type}</td>
                    <td align=center>{treat_type}</td>
                    <td>{card}</td>
                    <td align=right>{pres_days}</td>
                    <td align=right>{regist_fee}</td>
                    <td align=right>{diag_share_fee}</td>
                    <td align=right>{drug_share_fee}</td>
                    <td align=right>{deposit_fee}</td>
                    <td align=right>{refund}</td>
                    <td align=right>{repayment}</td>
                    <td align=right>{total_fee}</td>
                    <td align=right>{debt}</td>
                    <td align=right>{regist_debt}</td>
                    <td align=right>{receipt_fee}</td>
                    <td align=center>{registrar}</td>
                    <td align=center>{cashier}</td>
                </tr>
            '''.format(
                bgcolor=bgcolor,
                sequence=sequence,
                case_date=self.tableWidget_income_list.item(row_no, 1).text(),
                period=self.tableWidget_income_list.item(row_no, 2).text(),
                patient_key=self.tableWidget_income_list.item(row_no, 3).text(),
                name=self.tableWidget_income_list.item(row_no, 4).text(),
                ins_type=self.tableWidget_income_list.item(row_no, 5).text(),
                share_type=self.tableWidget_income_list.item(row_no, 6).text(),
                treat_type=self.tableWidget_income_list.item(row_no, 7).text(),
                card=self.tableWidget_income_list.item(row_no, 8).text(),
                pres_days=pres_days,
                regist_fee=self.tableWidget_income_list.item(row_no, 10).text(),
                diag_share_fee=self.tableWidget_income_list.item(row_no, 11).text(),
                drug_share_fee=self.tableWidget_income_list.item(row_no, 12).text(),
                deposit_fee=self.tableWidget_income_list.item(row_no, 13).text(),
                refund=self.tableWidget_income_list.item(row_no, 14).text(),
                repayment=self.tableWidget_income_list.item(row_no, 15).text(),
                total_fee=self.tableWidget_income_list.item(row_no, 16).text(),
                debt=self.tableWidget_income_list.item(row_no, 17).text(),
                regist_debt=self.tableWidget_income_list.item(row_no, 18).text(),
                receipt_fee=self.tableWidget_income_list.item(row_no, 19).text(),
                registrar=registrar,
                cashier=cashier,
            )

        html = '''
            <table align=center cellpadding="1" cellspacing="0" width="100%" style="border-width: 1px; border-style: solid;">
                <thead>
                    <tr bgcolor="LightGray">
                        <th>序</th>
                        <th>門診日期</th>
                        <th>班別</th>
                        <th>病歷號</th>
                        <th>姓名</th>
                        <th>保險</th>
                        <th>負擔類別</th>
                        <th>就醫類別</th>
                        <th>卡序</th>
                        <th>藥日</th>
                        <th>掛號費</th>
                        <th>門診負擔</th>
                        <th>藥品負擔</th>
                        <th>欠卡費</th>
                        <th>還卡費</th>
                        <th>自費還款</th>
                        <th>自費應收</th>
                        <th>自費欠款</th>
                        <th>掛號欠款</th>
                        <th>實收現金</th>
                        <th>掛號人員</th>
                        <th>批價人員</th>
                    </tr>
                </thead>
                <tbody>
                    {income_rows}
                </tbody>
            </table>
        '''.format(
            income_rows=income_rows,
        )

        return html

    def _get_table_total_html(self):
        html = '''
            <h2 align=center> 門診現金收入總表</h2>
            <table align=center cellpadding="1" cellspacing="0" width="100%" style="border-width: 1px; border-style: solid;">
                <thead>
                    <tr bgcolor="LightGray">
                        <th>掛號費</th>
                        <th>門診負擔</th>
                        <th>藥品負擔</th>
                        <th>欠卡費</th>
                        <th>還卡費</th>
                        <th>自費還款</th>
                        <th>自費應收</th>
                        <th>自費實收</th>
                        <th>掛號欠款</th>
                        <th>批價欠款</th>
                        <th>實收現金</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td align=right>{regist_fee}</td>
                        <td align=right>{diag_share_fee}</td>
                        <td align=right>{drug_share_fee}</td>
                        <td align=right>{deposit_fee}</td>
                        <td align=right>{refund}</td>
                        <td align=right>{repayment}</td>
                        <td align=right>{total_fee}</td>
                        <td align=right>{receipt_fee}</td>
                        <td align=right>{regist_debt}</td>
                        <td align=right>{cashier_debt}</td>
                        <td align=right>{receipt_total}</td>
                    </tr>
                </tbody>
            </table>
        
        '''.format(
            regist_fee=self.tableWidget_total.item(0, 1).text(),
            diag_share_fee=self.tableWidget_total.item(1, 1).text(),
            drug_share_fee=self.tableWidget_total.item(2, 1).text(),
            deposit_fee=self.tableWidget_total.item(3, 1).text(),
            refund=self.tableWidget_total.item(4, 1).text(),
            repayment=self.tableWidget_total.item(5, 1).text(),
            total_fee=self.tableWidget_total.item(6, 1).text(),
            receipt_fee=self.tableWidget_total.item(7, 1).text(),
            regist_debt=self.tableWidget_total.item(8, 1).text(),
            cashier_debt=self.tableWidget_total.item(9, 1).text(),
            receipt_total=self.tableWidget_total.item(10, 1).text(),
        )

        return html
