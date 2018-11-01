#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtCore, QtPrintSupport, QtWidgets
from PyQt5.QtPrintSupport import QPrinter
from libs import printer_utils
from libs import system_utils
from libs import number_utils


# 掛號收據格式1 80mm * 80mm 熱感紙
# 2018.07.09
class PrintInsApplyTotalFee:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ins_total_fee = args[2]
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
        self.font = QtGui.QFont(font, 10, QtGui.QFont.PreferQuality)

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

    def print_painter(self):
        self.current_print = self.print_painter
        self.printer.setPaperSize(QtCore.QSizeF(80, 80), QPrinter.Millimeter)

        painter = QtGui.QPainter()
        painter.setFont(self.font)
        painter.begin(self.printer)
        painter.drawText(0, 10, 'print test line1 中文測試')
        painter.drawText(0, 30, 'print test line2 中文測試')
        painter.end()

    def print_html(self, printing):
        self.current_print = self.print_html
        self.printer.setOrientation(QPrinter.Landscape)
        self.printer.setPaperSize(QPrinter.A4)

        document = printer_utils.get_document(self.printer, self.font)
        document.setDocumentMargin(5)
        document.setHtml(self._get_html(self.ins_total_fee))
        if printing:
            document.print(self.printer)

    def _get_html(self, ins_total_fee):
        apply_date = '{0:0>3}年{1:0>2}月 {2}'.format(
            ins_total_fee['apply_year']-1911,
            ins_total_fee['apply_month'],
            ins_total_fee['apply_period']
        )
        if ins_total_fee['apply_type'] == '1':
            apply_type_name = '1送核'
        else:
            apply_type_name = '2補報'

        generate_date = '{0:0>3}年{1:0>2}月{2:0>2}日'.format(
            ins_total_fee['ins_generate_date'].year()-1911,
            ins_total_fee['ins_generate_date'].month(),
            ins_total_fee['ins_generate_date'].day(),
            )
        start_date = '{0:0>3}年{1:0>2}月{2:0>2}日'.format(
            ins_total_fee['start_date'].year()-1911,
            ins_total_fee['start_date'].month(),
            ins_total_fee['start_date'].day(),
            )
        end_date = '{0:0>3}年{1:0>2}月{2:0>2}日'.format(
            ins_total_fee['end_date'].year()-1911,
            ins_total_fee['end_date'].month(),
            ins_total_fee['end_date'].day(),
            )

        html = '''
        <html>
        <body>
            <div>
                <table align=center cellpadding="1" cellspacing="0" width="95%">
                    <tbody>
                        <tr>
                            <td width="90%" style="text-align: center;">
                                <h3>特約醫事服務機構門診醫療服務點數申報總表</h3>
                            </td>
                            <td width="10%" style="text-align: right;">
                                <h3>中醫</h3>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <br>             
                <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: solid;">
                    <tbody>
                        <tr>
                            <td style="text-align: center;" colspan="2">t1資料格式</td>
                            <td style="text-align: center;" colspan="2">t2服務機構</td>
                            <td style="text-align: center;">t3費用年月</td>
                            <td style="text-align: center;">t4申報方式</td>
                            <td style="text-align: center;">t5申報類別</td>
                            <td style="text-align: center;">t6申報日期</td>
                            <td style="text-align: center;">收文日期</td>
                        </tr>
                        <tr>
                            <td style="text-align: center;">10</td>
                            <td style="text-align: center;">門診申報總表</td>
                            <td style="text-align: center;">{0}</td>
                            <td style="text-align: center;">{1}</td>
                            <td style="text-align: center;">{2}</td>
                            <td style="text-align: center;">3網路</td>
                            <td style="text-align: center;">{15}</td>
                            <td style="text-align: center;">{3}</td>
                            <td></td>
                        </tr>
                    </tbody>
                </table>
                <br>
                <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: solid;">
                <tbody>
                    <tr>
                        <td width="15%" style="text-align: center;" colspan="2">類別</td>    
                        <td width="20%" style="text-align: center;" colspan="2">件數</td>
                        <td width="20%" style="text-align: center;" colspan="2">申請點數</td>
                        <td style="padding-left: 20%; text-align: left;" rowspan="20">
                            <br>
                            負責醫師姓名: {4}<br>
                            <br>
                            醫事服務機構地址: {5}<br>
                            <br>
                            電話: {6}<br>
                            <br>
                            印信:
                        </td>
                    </tr>
                    <tr>
                        <td rowspan="5" style="text-align: center;"><br><br>西<br><br>醫</td>    
                        <td style="text-align: center;">一般案件</td>    
                        <td style="text-align: center;">t7</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t8</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;">專案案件</td>    
                        <td style="text-align: center;">t9</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t10</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;">洗腎</td>    
                        <td style="text-align: center;">t11</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t12</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;">結核病</td>    
                        <td style="text-align: center;">t15</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t16</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;">小計</td>    
                        <td style="text-align: center;">t17</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t18</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td rowspan="3" style="text-align: center;"><br>牙<br>醫</td>    
                        <td style="text-align: center;">一般案件</td>    
                        <td style="text-align: center;">t19</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t20</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;">專案案件</td>    
                        <td style="text-align: center;">t21</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t22</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;">小計</td>    
                        <td style="text-align: center;">t23</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t24</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td rowspan="3" style="text-align: center;"><br>中<br>醫</td>    
                        <td style="text-align: center;">一般案件</td>    
                        <td style="text-align: center;">t25</td>
                        <td style="text-align: right;">{7:,}</td>    
                        <td style="text-align: center;">t26</td>    
                        <td style="text-align: right;">{8:,}</td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;">專案案件</td>    
                        <td style="text-align: center;">t27</td>
                        <td style="text-align: right;">{9:,}</td>    
                        <td style="text-align: center;">t28</td>    
                        <td style="text-align: right;">{10:,}</td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;">小計</td>    
                        <td style="text-align: center;">t29</td>
                        <td style="text-align: right;">{11:,}</td>    
                        <td style="text-align: center;">t30</td>    
                        <td style="text-align: right;">{12:,}</td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;" colspan="2">預防保健</td>    
                        <td style="text-align: center;">t31</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t32</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;" colspan="2">慢性病連續處方箋調劑</td>    
                        <td style="text-align: center;">t33</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t34</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;" colspan="2">居家照護</td>    
                        <td style="text-align: center;">t35</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t36</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;" colspan="2">精神疾病社區復健</td>    
                        <td style="text-align: center;">t13</td>
                        <td style="text-align: center;"></td>    
                        <td style="text-align: center;">t14</td>    
                        <td style="text-align: center;"></td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;" colspan="2">總計</td>    
                        <td style="text-align: center;">t37</td>
                        <td style="text-align: right;">{11:,}</td>    
                        <td style="text-align: center;">t38</td>    
                        <td style="text-align: right;">{12:,}</td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;" colspan="2">部份負擔</td>    
                        <td style="text-align: center;">t39</td>
                        <td style="text-align: right;">{13:,}</td>    
                        <td style="text-align: center;">t40</td>    
                        <td style="text-align: right;">{14:,}</td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;" colspan="2">本次連線申報起迄日期</td>    
                        <td style="text-align: center;">t41</td>
                        <td style="text-align: center;">{16}</td>    
                        <td style="text-align: center;">t42</td>    
                        <td style="text-align: center;">{17}</td>    
                    </tr>
                    <tr>
                        <td style="text-align: center;"><br><br><br>注<br>意<br>事<br>項<br></td>
                        <td colspan="5" rowspan="10">
                            一、使用本表免另行辦函，請填送一式兩份。<br>
                            二、書面申報醫療費用者，應檢附本表及醫療服務點數清單暨醫令清單。<br>
                            三、媒體申報醫療費用者，僅需填本表及送媒體(磁片或磁帶)。<br>
                            四、連線申報醫療費用者，僅需填寫本表。<br>
                            五、
                            <ul>
                                <li>一般案件係指特約診所之日劑藥費申報案件（即案件分類：01、11、21）。</li>
                                <li>西醫專案案件範圍請參閱媒體申報格式之填表說明。</li>
                            </ul>
                            六、本表各欄位請按照媒體申報格式之填表說明填寫。
                        </td>
                    </tr>
                </tbody>
                </table>
            </div> 
        </body>
        </html>
        '''.format(
            self.ins_total_fee['clinic_id'],
            self.system_settings.field('院所名稱'),
            apply_date,
            generate_date,
            self.system_settings.field('負責醫師'),
            self.system_settings.field('院所地址'),
            self.system_settings.field('院所電話'),
            ins_total_fee['general_count'],
            ins_total_fee['general_amount'],
            ins_total_fee['special_count'],
            ins_total_fee['special_amount'],
            ins_total_fee['total_count'],
            ins_total_fee['total_amount'],
            ins_total_fee['share_count'],
            ins_total_fee['share_amount'],
            apply_type_name,
            start_date,
            end_date,
        )

        return html

