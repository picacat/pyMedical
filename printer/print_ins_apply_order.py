#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtCore, QtPrintSupport, QtWidgets
from PyQt5.QtPrintSupport import QPrinter
import datetime
import os

from libs import printer_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import case_utils
from libs import number_utils
from libs import charge_utils
from libs import date_utils
from libs import personnel_utils


# 掛號收據格式1 80mm * 80mm 熱感紙
# 2018.07.09
class PrintInsApplyOrder:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_type = args[2]
        self.ins_apply_key = args[3]
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
        sql = '''
            SELECT * FROM insapply
            WHERE
                InsApplyKey = {0}
        '''.format(self.ins_apply_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return None

        row = rows[0]
        # 14: 中醫 A:病歷本文 案件類別 流水號6碼
        export_dir = '{0}/emr{1}'.format(nhi_utils.XML_OUT_PATH, row['ApplyDate'])
        if not os.path.exists(export_dir):
            os.mkdir(export_dir)

        pdf_file_name = '{0}/ins_order_{1}{2:0>6}.pdf'.format(
            export_dir,
            string_utils.xstr(row['CaseType']),
            string_utils.xstr(row['Sequence']),
        )
        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setOutputFileName(pdf_file_name)
        self.print_html(True)

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
        document.setHtml(self._get_html(self.ins_apply_key))
        if printing:
            document.print(self.printer)

    def _get_html(self, ins_apply_key):
        sql = '''
            SELECT * FROM insapply
            WHERE
                InsApplyKey = {0}
        '''.format(ins_apply_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return None

        row = rows[0]
        case_record = self._get_case_record(row)
        prescript_record = self._get_prescript_record(row)
        fees_record = self._get_fees_record(row)

        html = '''
        <html>
        <body>
            <h3 style="text-align: center">特 約 醫 事 服 務 機 構 門 診 醫 療 服 務 點 數 及 醫 令 清 單</h3>
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: solid;">
                <tbody>
                    <tr>
                        <td>
                            {case_record}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            {prescript_record}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            {fees_record}
                        </td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        '''.format(
            case_record=case_record,
            prescript_record=prescript_record,
            fees_record=fees_record,
        )

        return html

    # 醫令病歷資料
    def _get_case_record(self, row):
        if self.apply_type == '申報':
            apply_type = '送核'
        else:
            apply_type = self.apply_type

        try:
            stop_date = string_utils.xstr(
                '{0:0>3}年{1:0>2}月{2:0>2}日'.format(
                    row['StopDate'].year-1911,
                    row['StopDate'].month,
                    row['StopDate'].day,
                    )
            )
        except:
            stop_date = ''


        html = '''
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td rowspan=2 style="text-align: center;" colspan="2">d2流水編號<br>{sequence}</td>
                        <td style="text-align: center;">t1資料格式</td>
                        <td style="text-align: center;">t2服務機構</td>
                        <td style="text-align: center;">t3費用年月</td>
                        <td>t5申報類別: {apply_type}</td>
                        <td style="text-align: center;">d1案件分類</td>
                    </tr>
                    <tr>
                        <td style="text-align: center">10門診費用明細</td>
                        <td style="text-align: center">({clinic_id}) {clinic_name}</td>
                        <td style="text-align: center">{apply_date}</td>
                        <td>d12補報原因註記:</td>
                        <td style="text-align: center">{case_type}</td>
                    </tr>
                </tbody>
            </table>
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td>
                            特定治療項目代號: d4:{special_code1}, d5:{special_code2}, d6:{special_code3}, d7:{special_code4}
                        </td>
                        <td>d49姓名: {name}</td>
                        <td>d9就醫日期: {case_date}</td>
                        <td>d8就醫科別: {clinic_class}</td>
                        <td>d27給藥日份: {pres_days}</td>
                    </tr>
                </tbody>
            </table>
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td>d11出生年月日:{birthday}</td>
                        <td>d3身分證統一編號:{id}</td>
                        <td>d29就醫序號:{card}</td>
                        <td>d14給付類別:{injury}</td>
                        <td>d15部份負擔代號:{share_code}</td>
                        <td>d10治療結束日期:{stop_date}</td>
                    </tr>
                </tbody>
            </table>
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td>d42論病歷計酬代碼:</td>
                        <td>d18病患是否轉出: N</td>
                        <td>d45依附就醫新生兒出生日期:</td>
                        <td>d44慢性病連續處方箋有效期間總處方日份:</td>
                    </tr>
                </tbody>
            </table>
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td>國際疾病分類碼</td>
                        <td>d19: {disease_code1}</td>
                        <td>d20: {disease_code2}</td>
                        <td>d21: {disease_code3}</td>
                        <td>d22:</td>
                        <td>d23:</td>
                        <td>d50矯正機關代號:</td>
                        <td>d52特定地區醫療服務:</td>
                        <td>d53支援區域:</td>
                    </tr>
                </tbody>
            </table>
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td>d24主手術(處置)代碼:</td>
                        <td>傷病名稱:{disease_name}</td>
                        <td>d25次手術(處置)代碼(一):</td>
                        <td>d53實際提供醫療服務之醫事服務機構代號:</td>
                    </tr>
                </tbody>
            </table>
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td>d25次手術(處置)代碼(二):</td>
                        <td>d46急診治療起始時間:</td>
                        <td>d47急診治療結束時間:</td>
                        <td>d48山地離島地區醫療服務計畫代碼:</td>
                        <td>d51依附就醫新生兒胞胎註記:</td>
                    </tr>
                </tbody>
            </table>
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td>d16轉診(檢),代檢或處方調劑案件註記:</td>
                        <td>d17轉診(檢),代檢或處方調劑案件之服務機構代號:</td>
                        <td>d13整合式照護計畫註記:</td>
                    </tr>
                </tbody>
            </table>
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td>d28處方調劑方式: {pres_type}</td>
                    </tr>
                </tbody>
            </table>
        '''.format(
            sequence=string_utils.xstr(row['Sequence']),
            clinic_id=self.system_settings.field('院所代號'),
            clinic_name=self.system_settings.field('院所名稱'),
            apply_date='{0:0>3}年{1:0>2}月'.format(
                row['CaseDate'].year-1911,
                row['CaseDate'].month,
            ),
            apply_type=apply_type,
            case_type=string_utils.xstr(row['CaseType']),
            special_code1=string_utils.xstr(row['SpecialCode1']),
            special_code2=string_utils.xstr(row['SpecialCode2']),
            special_code3=string_utils.xstr(row['SpecialCode3']),
            special_code4=string_utils.xstr(row['SpecialCode4']),
            name=string_utils.xstr(row['Name']),
            case_date=string_utils.xstr(
                '{0:0>3}年{1:0>2}月{2:0>2}日'.format(
                    row['CaseDate'].year-1911,
                    row['CaseDate'].month,
                    row['CaseDate'].day,
                    )
            ),
            clinic_class= nhi_utils.INS_CLASS,
            pres_days=string_utils.xstr(row['PresDays']),
            birthday=string_utils.xstr(
                '{0:0>3}年{1:0>2}月{2:0>2}日'.format(
                    row['Birthday'].year-1911,
                    row['Birthday'].month,
                    row['Birthday'].day,
                    )
            ),
            id=string_utils.xstr(row['ID']),
            card=string_utils.xstr(row['Card']),
            injury=string_utils.xstr(row['Injury']),
            share_code=string_utils.xstr(row['ShareCode']),
            stop_date=stop_date,
            disease_code1=string_utils.xstr(row['DiseaseCode1']),
            disease_code2=string_utils.xstr(row['DiseaseCode2']),
            disease_code3=string_utils.xstr(row['DiseaseCode3']),
            disease_name = case_utils.get_disease_name(self.database, row['DiseaseCode1']),
            pres_type=nhi_utils.PHARMACY_TYPE_DICT[row['PresType']],
        )

        return html

    # 醫令點數資料
    def _get_fees_record(self, row):
        pharmacy_code = nhi_utils.extract_pharmacy_code(row['PharmacyCode'])

        html = '''
            <table align=center cellpadding="1" cellspacing="0" width="95%" style="border-width: 1px; border-style: dotted;">
                <tbody>
                    <tr>
                        <td colspan="4">d32用藥明細點數小計: {drug_fee}</td>
                        <td colspan="4">d33診療明細點數小計: {treat_fee}</td>
                        <td colspan="4">d34特殊材料明細點數小計:</td>
                    </tr>
                    <tr>
                        <td colspan="4">d30診治醫事人員代號: {doctor_id}</td>
                        <td colspan="4">d31藥師代號: {pharmacist_id}</td>
                        <td style="text-align: center">項目代號</td>
                        <td style="text-align: center">項目名稱</td>
                        <td style="text-align: center">點數</td>
                        <td style="text-align: center">審查欄</td>
                    </tr>
                    <tr>
                        <td colspan="4" rowspan="6">診療醫師人員簽章:</td>
                        <td colspan="4" rowspan="6">藥師簽章:</td>
                        <td>d35: {diag_code}</td>
                        <td>診察費</td>
                        <td>d36: {diag_fee}</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td>d37: {pharmacy_code}</td>
                        <td>藥事服務費</td>
                        <td>d38: {pharmacy_fee}</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td></td>
                        <td>行政協助項目部分負擔</td>
                        <td>d43: {agent_fee}</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td colspan="2" style="text-align: center">d39合計點數</td>
                        <td style="text-align: right">{ins_total_fee}</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td colspan="2" style="text-align: center">d40部分負擔點數</td>
                        <td style="text-align: right">{share_fee}</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td colspan="2" style="text-align: center">d41申請點數<br>(扣除部分負擔後淨額)</td>
                        <td style="text-align: right; vertical-align: middle">{ins_apply_fee}</td>
                        <td></td>
                    </tr>
                </tbody>
            </table>
        '''.format(
            drug_fee=string_utils.xstr(row['DrugFee']),
            treat_fee=string_utils.xstr(row['TreatFee']),
            doctor_id=string_utils.xstr(row['DoctorID']),
            pharmacist_id=string_utils.xstr(row['PharmacistID']),
            diag_code=string_utils.xstr(row['DiagCode']),
            diag_fee=string_utils.xstr(row['DiagFee']),
            pharmacy_code=pharmacy_code,
            pharmacy_fee=string_utils.xstr(row['PharmacyFee']),
            agent_fee=string_utils.xstr(row['AgentFee']),
            ins_total_fee=string_utils.xstr(row['InsTotalFee']),
            share_fee=string_utils.xstr(row['ShareFee']),
            ins_apply_fee=string_utils.xstr(row['InsApplyFee']),
        )

        return html

    # 取得醫令藥品處置資料
    def _get_prescript_record(self, row):
        prescript_rows = self._get_order_rows(row)

        html = '''
            <table align=center cellpadding="0" cellspacing="0" width="95%" style="font-size: 10px; border-width: 1px; border-style: dotted;">
                <thead>
                    <tr>
                        <th style="text-align: center; vertical-align: middle">p13<br>醫令<br>序</th>
                        <th style="text-align: center; vertical-align: middle">p20<br>就醫<br>科別</th>
                        <th style="text-align: center; vertical-align: middle">p17<br>慢性病連續處方箋註記 </th>
                        <th style="text-align: center; vertical-align: middle">p2<br>醫令<br>調劑<br>方式</th>
                        <th style="text-align: center; vertical-align: middle">p3<br>醫令<br>類別</th>
                        <th style="text-align: center; vertical-align: middle">p1<br>藥品<br>給藥<br>日份</th>
                        <th style="text-align: center; vertical-align: middle">p4<br>藥品項目<br>代號</th>
                        <th colspan="3" style="text-align: center; vertical-align: middle">診療項目或<br>藥品材料<br>名稱規格</th>
                        <th style="text-align: center; vertical-align: middle">p21<br>自費<br>特材<br>群組<br>序號</th>
                        <th style="text-align: center; vertical-align: middle">p14<br>執行時<br>間-起</th>
                        <th style="text-align: center; vertical-align: middle">p15<br>執行時<br>間-迄</th>
                        <th style="text-align: center; vertical-align: middle">p16<br>執行醫事<br>人員代號</th>
                        <th style="text-align: center; vertical-align: middle">p19<br>事前<br>審查<br>受理<br>編號</th>
                        <th style="text-align: center; vertical-align: middle">p18<br>影像<br>來源</th>
                        <th style="text-align: center; vertical-align: middle">p5<br>藥品<br>用量<br>p6<br>診療<br>部位</th>
                        <th style="text-align: center; vertical-align: middle">p7<br>藥品使用<br>頻率<br>p8<br>支付成數</th>
                        <th style="text-align: center; vertical-align: middle">p9<br>給藥<br>途徑<br>作用<br>部位</th>
                        <th style="text-align: center; vertical-align: middle">p10<br>總量</th>
                        <th style="text-align: center; vertical-align: middle">p11<br>單價</th>
                        <th style="text-align: center; vertical-align: middle">p12<br>點數</th>
                        <th style="text-align: center; vertical-align: middle">p12<br>審查欄</th>
                    </tr>
                </thead>            
                <tbody>
                    {prescript_rows}
                </tbody>
            </table>
        '''.format(
            prescript_rows=prescript_rows,
        )

        return html

    def _get_order_rows(self, row):
        self.sequence = 0

        if string_utils.xstr(row['CaseType']) == '30':  # 腦血管疾病, 小兒氣喘, 小兒腦麻
            html = self._set_auxiliary_case(row)
            return html

        html = ''
        max_course = 6
        for course in range(1, max_course+1):
            case_key = number_utils.get_integer(row['CaseKey{0}'.format(course)])
            if case_key <= 0:
                continue

            rows = self._get_case_row(case_key)
            if len(rows) <= 0:
                continue

            case_row = rows[0]

            if course == 1:  # 設定診察費
                html += self._set_diagnosis(row)
                if string_utils.xstr(row['Visit']) == '初診照護':
                    html += self._set_first_visit(row)

            if string_utils.xstr(case_row['TreatType']) in nhi_utils.CARE_TREAT:
                html += self._set_special_care(row, case_row)

            treat_code = string_utils.xstr(row['TreatCode{0}'.format(course)])
            if treat_code != '':
                html += self._set_treatment(row, case_row, course, treat_code)

            prescript_rows = self._get_prescript_rows(case_key)
            if len(prescript_rows) > 0:
                html += self._set_prescript(row, case_row, prescript_rows, case_key, course)

        return html

    def _set_auxiliary_case(self, row):
        treat_code = string_utils.xstr(row['TreatCode1'])
        amount = number_utils.get_integer(row['TreatFee1'])
        percent = number_utils.get_integer(row['Percent1'])
        unit_price = number_utils.get_integer(amount / percent * 100)

        self.sequence += 1
        order_row = {}
        order_row['sequence'] = string_utils.xstr(self.sequence)
        order_row['clinic_class'] = string_utils.xstr(row['Class'])
        order_row['course_type'] = '2' # 2=同一療程
        order_row['pres_type'] = '0'
        order_row['order_type'] = '2'  # 2=診療明細
        order_row['pres_days'] = ''
        order_row['ins_code'] = treat_code
        order_row['order_name'] = charge_utils.get_item_name_from_ins_code(self.database, treat_code)
        order_row['start_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
        order_row['stop_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['StopDate']))
        order_row['doctor_id'] = string_utils.xstr(row['DoctorID'])
        order_row['dosage'] = '1'
        order_row['percent'] = '{0:05.2f}'.format(amount / unit_price * 100)
        order_row['usage'] = ''
        order_row['total_dosage'] = '1'
        order_row['unit_price'] = string_utils.xstr(unit_price)
        order_row['amount'] = string_utils.xstr(amount)

        html = self._get_html_order_row(order_row)

        return html

    def _set_diagnosis(self, row):
        amount = number_utils.get_integer(row['DiagFee'])
        unit_price = number_utils.get_integer(
            charge_utils.get_ins_fee_from_ins_code(
                self.database, string_utils.xstr(row['DiagCode']))
        )

        if unit_price <= 0:
            return ''

        self.sequence += 1
        order_row = {}
        order_row['sequence'] = string_utils.xstr(self.sequence)
        order_row['clinic_class'] = string_utils.xstr(row['Class'])
        order_row['course_type'] = ''
        order_row['pres_type'] = ''
        order_row['order_type'] = '0'  # 0=診察費
        order_row['pres_days'] = ''
        order_row['ins_code'] = string_utils.xstr(row['DiagCode'])
        order_row['order_name'] = '診察費'
        order_row['start_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
        order_row['stop_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
        order_row['doctor_id'] = string_utils.xstr(row['DoctorID'])
        order_row['dosage'] = '1'
        order_row['percent'] = '{0:05.2f}'.format(amount / unit_price * 100)
        order_row['usage'] = ''
        order_row['total_dosage'] = '1'
        order_row['unit_price'] = string_utils.xstr(unit_price)
        order_row['amount'] = string_utils.xstr(amount)

        html = self._get_html_order_row(order_row)

        return html

    # 初診照護
    def _set_first_visit(self, row):
        ins_code = 'A90'

        amount = number_utils.get_integer(
            charge_utils.get_ins_fee_from_ins_code(self.database, ins_code)
        )
        unit_price = amount

        if unit_price <= 0:
            return

        self.sequence += 1

        order_row = {}
        order_row['sequence'] = string_utils.xstr(self.sequence)
        order_row['clinic_class'] = string_utils.xstr(row['Class'])
        order_row['course_type'] = ''
        order_row['pres_type'] = ''
        order_row['order_type'] = '2'  # 2=診療明細
        order_row['pres_days'] = ''
        order_row['ins_code'] = ins_code
        order_row['order_name'] = '初診診察費加計'
        order_row['start_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
        order_row['stop_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
        order_row['doctor_id'] = string_utils.xstr(row['DoctorID'])
        order_row['dosage'] = '1'
        order_row['percent'] = '{0:05.2f}'.format(amount / unit_price * 100)
        order_row['usage'] = ''
        order_row['total_dosage'] = '1'
        order_row['unit_price'] = string_utils.xstr(unit_price)
        order_row['amount'] = string_utils.xstr(amount)

        html = self._get_html_order_row(order_row)

        return html

    # 加強照護
    def _set_special_care(self, row, case_row):
        sql = '''
            SELECT * FROM prescript
            WHERE
                CaseKey = {0} AND
                MedicineSet = 11 AND
                MedicineType = "照護"
            ORDER BY PrescriptKey
        '''.format(case_row['CaseKey'])
        rows = self.database.select_record(sql)

        html = ''
        for care_row in rows:
            self.sequence += 1
            amount = number_utils.get_integer(care_row['Price'])
            percent = 100
            unit_price = number_utils.get_integer(amount / percent * 100)
            ins_code = string_utils.xstr(care_row['InsCode'])

            order_row = {}
            order_row['sequence'] = string_utils.xstr(self.sequence)
            order_row['clinic_class'] = string_utils.xstr(row['Class'])
            order_row['course_type'] = ''
            order_row['pres_type'] = '0'
            order_row['order_type'] = '2'  # 2=診療明細
            order_row['pres_days'] = ''
            order_row['ins_code'] = ins_code
            order_row['order_name'] = string_utils.xstr(care_row['MedicineName'])
            order_row['start_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
            order_row['stop_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
            order_row['doctor_id'] = string_utils.xstr(row['DoctorID'])
            order_row['dosage'] = '1'
            order_row['percent'] = '{0:05.2f}'.format(amount / unit_price * 100)
            order_row['usage'] = ''
            order_row['total_dosage'] = '1'
            order_row['unit_price'] = string_utils.xstr(unit_price)
            order_row['amount'] = string_utils.xstr(amount)

            html += self._get_html_order_row(order_row)

        return html

    def _set_treatment(self, row, case_row, course, treat_code):
        amount = number_utils.get_integer(row['TreatFee{0}'.format(course)])
        percent = number_utils.get_integer(row['Percent{0}'.format(course)])
        unit_price = number_utils.get_integer(amount / percent * 100)

        self.sequence += 1
        order_row = {}
        order_row['sequence'] = string_utils.xstr(self.sequence)
        order_row['clinic_class'] = string_utils.xstr(row['Class'])
        order_row['course_type'] = '2' # 2=同一療程
        order_row['pres_type'] = '0'
        order_row['order_type'] = '2'  # 2=診療明細
        order_row['pres_days'] = ''
        order_row['ins_code'] = treat_code
        order_row['order_name'] = nhi_utils.TREAT_NAME_DICT[treat_code]
        order_row['start_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        order_row['stop_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        order_row['doctor_id'] = personnel_utils.get_personnel_id(
            self.database, string_utils.xstr(case_row['Doctor'])
        )
        order_row['dosage'] = '1'
        order_row['percent'] = '{0:05.2f}'.format(amount / unit_price * 100)
        order_row['usage'] = ''
        order_row['total_dosage'] = '1'
        order_row['unit_price'] = string_utils.xstr(unit_price)
        order_row['amount'] = string_utils.xstr(amount)

        html = self._get_html_order_row(order_row)

        return html

    def _set_prescript(self, row, case_row, prescript_rows, case_key, course):
        html = ''

        pres_days = case_utils.get_pres_days(self.database, case_key)
        packages = case_utils.get_packages(self.database, case_key)
        instruction = case_utils.get_instruction(self.database, case_key)
        if pres_days <= 0:
            return html

        if number_utils.get_integer(row['DrugFee']) > 0:
            order_type = '1'  # 1=用藥明細
        else:
            order_type = '4'  # 4=不另計價

        html += self._set_A21(row, case_row, order_type, pres_days)
        if number_utils.get_integer(row['PharmacyFee']) > 0:
            html += self._set_pharmacy(row, case_row, pres_days, course)

        for prescript_row in prescript_rows:
            html += self._set_medicine(
                row, case_row, prescript_row, pres_days, packages, instruction
            )

        return html

    def _set_A21(self, row, case_row, order_type, pres_days):
        ins_code = 'A21'
        unit_price = number_utils.get_integer(
            charge_utils.get_ins_fee_from_ins_code(self.database, ins_code)
        )
        amount = unit_price * pres_days
        if order_type == '4':  # 不另計價
            unit_price = 0
            amount = unit_price

        self.sequence += 1
        order_row = {}
        order_row['sequence'] = string_utils.xstr(self.sequence)
        order_row['clinic_class'] = string_utils.xstr(row['Class'])
        order_row['course_type'] = '' # 2=同一療程
        order_row['pres_type'] = '0'
        order_row['order_type'] = order_type
        order_row['pres_days'] = pres_days
        order_row['ins_code'] = ins_code
        order_row['order_name'] = charge_utils.get_item_name_from_ins_code(self.database, ins_code)
        order_row['start_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        order_row['stop_date'] = '{0}0000'.format( date_utils.west_date_to_nhi_date(
            case_row['CaseDate'].date() + datetime.timedelta(days=pres_days-1))
        )
        order_row['doctor_id'] = personnel_utils.get_personnel_id(
            self.database, string_utils.xstr(case_row['Doctor'])
        )
        order_row['dosage'] = '{0:7.2f}'.format(pres_days)
        order_row['percent'] = '{0:05.2f}'.format(100)
        order_row['usage'] = 'PO'
        order_row['total_dosage'] = '{0:7.1f}'.format(pres_days)
        order_row['unit_price'] = string_utils.xstr(unit_price)
        order_row['amount'] = string_utils.xstr(amount)

        html = self._get_html_order_row(order_row)

        return html

    def _set_pharmacy(self, row, case_row, pres_days, course):
        html = ''
        if pres_days <= 0:
            return html

        pharmacy_byte = string_utils.xstr(row['PharmacyCode'])[course-1]
        if pharmacy_byte in ['1', '2']:
            pharmacy_code = 'A3{0}'.format(pharmacy_byte)
        else:
            return html

        self.sequence += 1
        unit_price = number_utils.get_integer(
            charge_utils.get_diag_ins_from_ins_code(self.database, pharmacy_code)
        )
        amount = unit_price

        self.sequence += 1
        order_row = {}
        order_row['sequence'] = string_utils.xstr(self.sequence)
        order_row['clinic_class'] = string_utils.xstr(row['Class'])
        order_row['course_type'] = '' # 2=同一療程
        order_row['pres_type'] = '0'
        order_row['order_type'] = '9'  # 9=調劑費
        order_row['pres_days'] = pres_days
        order_row['ins_code'] = pharmacy_code
        order_row['order_name'] = charge_utils.get_item_name_from_ins_code(self.database, pharmacy_code)
        order_row['start_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        order_row['stop_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        order_row['doctor_id'] = personnel_utils.get_personnel_id(
            self.database, string_utils.xstr(case_row['Doctor'])
        )
        order_row['dosage'] = '1'
        order_row['percent'] = '{0:05.2f}'.format(100)
        order_row['usage'] = ''
        order_row['total_dosage'] = '1'
        order_row['unit_price'] = string_utils.xstr(unit_price)
        order_row['amount'] = string_utils.xstr(amount)

        html = self._get_html_order_row(order_row)

        return html


    def _set_medicine(self, row, case_row, prescript_row, pres_days, packages, instruction):
        unit_price = 0
        amount = unit_price
        ins_code = string_utils.xstr(prescript_row['InsCode'])

        order_name = case_utils.get_drug_name(self.database, ins_code)
        if order_name == '':
            order_name = case_utils.get_medicine_name(self.database, ins_code)

        self.sequence += 1
        order_row = {}
        order_row['sequence'] = string_utils.xstr(self.sequence)
        order_row['clinic_class'] = string_utils.xstr(row['Class'])
        order_row['course_type'] = '' # 2=同一療程
        order_row['pres_type'] = '0'
        order_row['order_type'] = '4'
        order_row['pres_days'] = pres_days
        order_row['ins_code'] = ins_code
        order_row['order_name'] = order_name
        order_row['start_date'] = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        order_row['stop_date'] = '{0}0000'.format( date_utils.west_date_to_nhi_date(
            case_row['CaseDate'].date() + datetime.timedelta(days=pres_days-1))
        )
        order_row['doctor_id'] = ''
        order_row['dosage'] = '{0:7.2f}'.format(prescript_row['Dosage'] / packages)
        order_row['percent'] = '{0}{1}'.format(nhi_utils.FREQUENCY[packages], nhi_utils.get_usage(instruction))
        order_row['usage'] = 'PO'
        order_row['total_dosage'] = '{0:7.1f}'.format(prescript_row['Dosage'] * pres_days)
        order_row['unit_price'] = string_utils.xstr(unit_price)
        order_row['amount'] = string_utils.xstr(amount)

        html = self._get_html_order_row(order_row)

        return html

    def _get_case_row(self, case_key):
        sql = '''
                SELECT *
                FROM cases
                WHERE
                    CaseKey = "{0}"
            '''.format(case_key)

        rows = self.database.select_record(sql)

        return rows

    def _get_prescript_rows(self, case_key):
        sql = '''
            SELECT *
            FROM prescript
            WHERE
                CaseKey = "{0}" AND
                MedicineSet = 1 AND
                InsCode IS NOT NULL AND
                LENGTH(InsCode) > 0
            ORDER BY PrescriptNo, PrescriptKey
        '''.format(case_key)

        rows = self.database.select_record(sql)

        return rows

    # 取得醫令列
    def _get_html_order_row(self, row):
        html = '''
            <tr>
                <td style="text-align: center; vertical-align: middle">{sequence}</td>
                <td style="text-align: center; vertical-align: middle">{clinic_class}</td>
                <td style="text-align: center; vertical-align: middle">{course_type}</td>
                <td style="text-align: center; vertical-align: middle">{pres_type}</td>
                <td style="text-align: center; vertical-align: middle">{order_type}</td>
                <td style="text-align: right; vertical-align: middle">{pres_days}</td>
                <td style="text-align: center; vertical-align: middle">{ins_code}</td>
                <td colspan="3" style="text-align: center; vertical-align: middle">{order_name}</td>
                <td></td>
                <td style="text-align: center; vertical-align: middle; font-size:7px">{start_date}</td>
                <td style="text-align: center; vertical-align: middle; font-size:7px">{stop_date}</td>
                <td style="text-align: center; vertical-align: middle; font-size:7px">{doctor_id}</td>
                <td></td>
                <td></td>
                <td style="text-align: right; vertical-align: middle">{dosage}</td>
                <td style="text-align: right; vertical-align: middle">{percent}</td>
                <td style="text-align: center; vertical-align: middle">{usage}</td>
                <td style="text-align: right; vertical-align: middle">{total_dosage}</td>
                <td style="text-align: right; vertical-align: middle">{unit_price}</td>
                <td style="text-align: right; vertical-align: middle">{amount}</td>
                <td></td> 
            </tr>
        '''.format(
            sequence=row['sequence'],
            clinic_class=row['clinic_class'],
            course_type=row['course_type'],
            pres_type=row['pres_type'],
            order_type=row['order_type'],
            pres_days=row['pres_days'],
            ins_code=row['ins_code'],
            order_name=row['order_name'],
            start_date=row['start_date'],
            stop_date=row['stop_date'],
            doctor_id=row['doctor_id'],
            dosage=row['dosage'],
            percent=row['percent'],
            usage=row['usage'],
            total_dosage=row['total_dosage'],
            unit_price=row['unit_price'],
            amount=row['amount'],
        )

        return html

