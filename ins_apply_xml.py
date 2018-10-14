#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import datetime

from libs import date_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import charge_utils
from libs import case_utils
from lxml import etree as ET


# 候診名單 2018.01.31
class InsApplyXML(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsApplyXML, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = args[2]
        self.apply_month = args[3]
        self.start_date = args[4]
        self.end_date = args[5]
        self.period = args[6]
        self.apply_type = args[7]
        self.clinic_id = args[8]
        self.ins_total_fee = args[9]

        self.ui = None
        self.apply_date = nhi_utils.get_apply_date(self.apply_year, self.apply_month)
        self.apply_type_code = nhi_utils.APPLY_TYPE_CODE[self.apply_type]
        self.start_date = self.start_date.toString("yyyy-MM-dd 00:00:00")
        self.end_date = self.end_date.toString("yyyy-MM-dd 23:59:59")
        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_app(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        pass

    # 設定信號
    def _set_signal(self):
        pass

    def create_xml_file(self):
        xml_file_name = nhi_utils.get_ins_xml_file_name(
            self.ins_total_fee['apply_type'],
            self.ins_total_fee['apply_date'],
        )

        self._write_xml_file(xml_file_name)

    def _write_xml_file(self, xml_file_name):
        rows = self._get_ins_rows()
        record_count = len(rows)
        if record_count <= 0:
            return

        progress_dialog = QtWidgets.QProgressDialog(
            '正在產生申報XML檔中, 請稍後...', '取消', 0, record_count, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        root = ET.Element('outpatient')
        self._add_tdata(root)
        for row_no, row in zip(range(record_count), rows):
            progress_dialog.setValue(row_no)
            if progress_dialog.wasCanceled():
                break

            self._add_ddata(root, row)

        progress_dialog.setValue(record_count)

        tree = ET.ElementTree(root)
        tree.write(xml_file_name, pretty_print=True, xml_declaration=True, encoding="Big5")

    def _add_tdata(self, root):
        generate_date = '{0:0>3}{1:0>2}{2:>02}'.format(
            self.ins_total_fee['ins_generate_date'].year()-1911,
            self.ins_total_fee['ins_generate_date'].month(),
            self.ins_total_fee['ins_generate_date'].day(),
            )
        start_date = '{0:0>3}{1:0>2}{2:>02}'.format(
            self.ins_total_fee['start_date'].year()-1911,
            self.ins_total_fee['start_date'].month(),
            self.ins_total_fee['start_date'].day(),
            )
        end_date = '{0:0>3}{1:0>2}{2:>02}'.format(
            self.ins_total_fee['end_date'].year()-1911,
            self.ins_total_fee['end_date'].month(),
            self.ins_total_fee['end_date'].day(),
            )

        tdata = ET.SubElement(root, 'tdata')
        t1 = ET.SubElement(tdata, 't1')
        t1.text = '10'
        t2 = ET.SubElement(tdata, 't2')
        t2.text =  self.ins_total_fee['clinic_id']             # 院所代號
        t3 = ET.SubElement(tdata, 't3')
        t3.text = self.ins_total_fee['apply_date']             # 費用年月
        t4 = ET.SubElement(tdata, 't4')
        t4.text = '3'   # 申報方式: 3=網路
        t5 = ET.SubElement(tdata, 't5')
        t5.text = self.ins_total_fee['apply_type']             # 申報類別: 1=送核, 2=補報
        t6 = ET.SubElement(tdata, 't6')
        t6.text = generate_date                                # 申報日期
        t25 = ET.SubElement(tdata, 't25')
        t25.text = string_utils.xstr(self.ins_total_fee['general_count'])         # 一般案案件件數
        t26 = ET.SubElement(tdata, 't26')
        t26.text = string_utils.xstr(self.ins_total_fee['general_amount'])        # 一般案件點數
        t27 = ET.SubElement(tdata, 't27')
        t27.text = string_utils.xstr(self.ins_total_fee['special_count'])         # 專案案件件數
        t28 = ET.SubElement(tdata, 't28')
        t28.text = string_utils.xstr(self.ins_total_fee['special_amount'])        # 專案案件點數
        t29 = ET.SubElement(tdata, 't29')
        t29.text = string_utils.xstr(self.ins_total_fee['total_count'])   # 案件件數小計
        t30 = ET.SubElement(tdata, 't30')
        t30.text = string_utils.xstr(self.ins_total_fee['total_amount'])   # 案件點數小計
        t37 = ET.SubElement(tdata, 't37')
        t37.text = string_utils.xstr(self.ins_total_fee['total_count'])   # 案件件數總計
        t38 = ET.SubElement(tdata, 't38')
        t38.text = string_utils.xstr(self.ins_total_fee['total_amount'])   # 案件點數總計
        t39 = ET.SubElement(tdata, 't39')
        t39.text = string_utils.xstr(self.ins_total_fee['share_count'])   # 部份負擔件數總計
        t40 = ET.SubElement(tdata, 't40')
        t40.text = string_utils.xstr(self.ins_total_fee['share_amount'])   # 部份負擔點數總計
        t41 = ET.SubElement(tdata, 't41')
        t41.text = start_date                                               # 連線申報起日期
        t42 = ET.SubElement(tdata, 't42')
        t42.text = end_date                                                 # 連線申報迄日期

    def _add_ddata(self, root, row):
        ddata = ET.SubElement(root, 'ddata')

        self._add_dhead(ddata, row)
        self._add_dbody(ddata, row)

    def _add_dhead(self, ddata, row):
        dhead = ET.SubElement(ddata, 'dhead')
        d1 = ET.SubElement(dhead, 'd1')
        d1.text =  string_utils.xstr(row['CaseType'])
        d2 = ET.SubElement(dhead, 'd2')
        d2.text = string_utils.xstr(row['Sequence'])

    def _add_dbody(self, ddata, row):
        dbody = ET.SubElement(ddata, 'dbody')

        for i in range(1, 5):
            special_code = string_utils.xstr(row['SpecialCode{0}'.format(i)])
            if special_code != '':
                dx = ET.SubElement(dbody, 'd{0}'.format(i+3))
                dx.text = string_utils.xstr(special_code)

        d8 = ET.SubElement(dbody, 'd8')
        d8.text = string_utils.xstr(row['Class'])
        d9 = ET.SubElement(dbody, 'd9')
        d9.text = date_utils.west_date_to_nhi_date(row['CaseDate'])

        if string_utils.xstr(row['CaseType']) == '29':
            d10 = ET.SubElement(dbody, 'd10')
            d10.text = date_utils.west_date_to_nhi_date(row['StopDate'])

        d11 = ET.SubElement(dbody, 'd11')
        d11.text = date_utils.west_date_to_nhi_date(row['Birthday'])
        d3 = ET.SubElement(dbody, 'd3')
        d3.text = string_utils.xstr(row['ID'])
        d14 = ET.SubElement(dbody, 'd14')
        d14.text = string_utils.xstr(row['Injury'])
        d15 = ET.SubElement(dbody, 'd15')
        d15.text = string_utils.xstr(row['ShareCode'])
        d17 = ET.SubElement(dbody, 'd17')
        d17.text = 'N'  # 轉診院所代號
        d18 = ET.SubElement(dbody, 'd18')
        d18.text = 'N'  # 是否轉診

        for i in range(1, 4):
            disease_code = string_utils.xstr(row['DiseaseCode{0}'.format(i)])
            if disease_code != '':
                dx = ET.SubElement(dbody, 'd{0}'.format(i+18))
                dx.text = string_utils.xstr(disease_code)

        if number_utils.get_integer(row['PresDays']) > 0:
            d27 = ET.SubElement(dbody, 'd27')
            d27.text = string_utils.xstr(row['PresDays'])

        d28 = ET.SubElement(dbody, 'd28')
        d28.text = string_utils.xstr(row['PresType'])
        d29 = ET.SubElement(dbody, 'd29')
        d29.text = string_utils.xstr(row['Card'])
        d30 = ET.SubElement(dbody, 'd30')
        d30.text = string_utils.xstr(row['DoctorID'])

        if string_utils.xstr(row['PharmacistID']) != '':
            d31 = ET.SubElement(dbody, 'd31')
            d31.text = string_utils.xstr(row['PharmacistID'])

        if number_utils.get_integer(row['DrugFee']) > 0:
            d32 = ET.SubElement(dbody, 'd32')
            d32.text = string_utils.xstr(row['DrugFee'])

        if number_utils.get_integer(row['TreatFee']) > 0:
            d33 = ET.SubElement(dbody, 'd33')
            d33.text = string_utils.xstr(row['TreatFee'])

        if string_utils.xstr(row['DiagCode']) != '':
            d35 = ET.SubElement(dbody, 'd35')
            d35.text = string_utils.xstr(row['DiagCode'])

        if number_utils.get_integer(row['DiagFee']) > 0:
            d36 = ET.SubElement(dbody, 'd36')
            d36.text = string_utils.xstr(row['DiagFee'])

        pharmacy_code = self._get_pharmacy_code(string_utils.xstr(row['PharmacyCode']))
        if string_utils.xstr(pharmacy_code) != '':
            d37 = ET.SubElement(dbody, 'd37')
            d37.text = string_utils.xstr(pharmacy_code)

        if number_utils.get_integer(row['PharmacyFee']) > 0:
            d38 = ET.SubElement(dbody, 'd38')
            d38.text = string_utils.xstr(row['PharmacyFee'])

        d39 = ET.SubElement(dbody, 'd39')
        d39.text = string_utils.xstr(number_utils.get_integer(row['InsTotalFee']))
        d40 = ET.SubElement(dbody, 'd40')
        d40.text = string_utils.xstr(number_utils.get_integer(row['ShareFee']))
        d41 = ET.SubElement(dbody, 'd41')
        d41.text = string_utils.xstr(number_utils.get_integer(row['InsApplyFee']))

        if number_utils.get_integer(row['AgentFee']) > 0:
            d43 = ET.SubElement(dbody, 'd43')
            d43.text = string_utils.xstr(row['AgentFee'])

        d49 = ET.SubElement(dbody, 'd49')
        d49.text = self._get_name(row['Name'])

        self._add_pdata(dbody, row)

    def _add_pdata(self, dbody, row):
        if string_utils.xstr(row['SpecialCode1']) in ['CA', 'JG']:  # ['腦血管疾病', '兒童鼻炎']
            self._add_special_care_cases(dbody, row)
            return

        self.sequence = 0
        for course in range(1, 7):
            case_key = number_utils.get_integer(row['CaseKey{0}'.format(course)])
            if case_key <= 0:
                continue

            case_row = self._get_case_row(case_key)
            if len(case_row) <= 0:
                continue

            if course == 1:  # 設定診察費
                self._set_diagnosis(dbody, row)
                if string_utils.xstr(row['Visit']) == '初診照護':
                    self._set_first_visit(dbody, row)

            if string_utils.xstr(case_row['TreatType']) in nhi_utils.CARE_TREAT:
                self._set_special_care(dbody, row, case_row)

            treat_code = string_utils.xstr(row['TreatCode{0}'.format(course)])
            if treat_code != '':
                self._set_treatment(dbody, row, case_row, course, treat_code)

            prescript_rows = self._get_prescript_rows(case_key)
            if len(prescript_rows) > 0:
                self._set_prescript(dbody, row, case_row, prescript_rows, case_key, course)

    def _set_diagnosis(self, dbody, row):
        pdata = ET.SubElement(dbody, 'pdata')

        self.sequence += 1
        amount = number_utils.get_integer(row['DiagFee'])
        unit_price = number_utils.get_integer(
            charge_utils.get_diag_fee_from_diag_code(
                self.database, string_utils.xstr(row['DiagCode']))
        )

        p3 = ET.SubElement(pdata, 'p3')
        p3.text = '0'  # 0=診察費
        p4 = ET.SubElement(pdata, 'p4')
        p4.text = string_utils.xstr(row['DiagCode'])
        p8 = ET.SubElement(pdata, 'p8')
        p8.text = '{0:05.2f}'.format(amount / unit_price * 100)
        p10 = ET.SubElement(pdata, 'p10')
        p10.text = '1'  # 總量
        p11 = ET.SubElement(pdata, 'p11')
        p11.text = string_utils.xstr(unit_price)  # 單價
        p12 = ET.SubElement(pdata, 'p12')
        p12.text = string_utils.xstr(amount)  # 點數
        p13 = ET.SubElement(pdata, 'p13')
        p13.text = string_utils.xstr(self.sequence)  # 序號
        p14 = ET.SubElement(pdata, 'p14')
        p14.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
        p15 = ET.SubElement(pdata, 'p15')
        p15.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
        p16 = ET.SubElement(pdata, 'p16')
        p16.text = string_utils.xstr(row['DoctorID'])
        p20 = ET.SubElement(pdata, 'p20')
        p20.text = string_utils.xstr(row['Class'])

    def _set_first_visit(self, dbody, row):
        pdata = ET.SubElement(dbody, 'pdata')

        self.sequence += 1
        ins_code = 'A90'
        amount = number_utils.get_integer(
            charge_utils.get_diag_fee_from_diag_code(self.database, ins_code)
        )
        unit_price = amount

        p3 = ET.SubElement(pdata, 'p3')
        p3.text = '2'  # 2=診療明細
        p4 = ET.SubElement(pdata, 'p4')
        p4.text = ins_code
        p8 = ET.SubElement(pdata, 'p8')
        p8.text = '{0:05.2f}'.format(amount / unit_price * 100)
        p10 = ET.SubElement(pdata, 'p10')
        p10.text = '1'  # 總量
        p11 = ET.SubElement(pdata, 'p11')
        p11.text = string_utils.xstr(unit_price)  # 單價
        p12 = ET.SubElement(pdata, 'p12')
        p12.text = string_utils.xstr(amount)  # 點數
        p13 = ET.SubElement(pdata, 'p13')
        p13.text = string_utils.xstr(self.sequence)  # 序號
        p14 = ET.SubElement(pdata, 'p14')
        p14.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
        p15 = ET.SubElement(pdata, 'p15')
        p15.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(row['CaseDate']))
        p16 = ET.SubElement(pdata, 'p16')
        p16.text = string_utils.xstr(row['DoctorID'])
        p20 = ET.SubElement(pdata, 'p20')
        p20.text = string_utils.xstr(row['Class'])

    def _set_treatment(self, dbody, row, case_row, course, treat_code):
        pdata = ET.SubElement(dbody, 'pdata')

        self.sequence += 1
        amount = number_utils.get_integer(row['TreatFee{0}'.format(course)])
        percent = number_utils.get_integer(row['Percent{0}'.format(course)])
        unit_price = number_utils.get_integer(amount / percent * 100)

        p2 = ET.SubElement(pdata, 'p2')
        p2.text = '0'  # 0=自行調劑或物理治療
        p3 = ET.SubElement(pdata, 'p3')
        p3.text = '2'  # 2=診療明細
        p4 = ET.SubElement(pdata, 'p4')
        p4.text = treat_code
        p8 = ET.SubElement(pdata, 'p8')
        p8.text = '{0:05.2f}'.format(percent)
        p10 = ET.SubElement(pdata, 'p10')
        p10.text = '1'  # 總量
        p11 = ET.SubElement(pdata, 'p11')
        p11.text = string_utils.xstr(unit_price)  # 單價
        p12 = ET.SubElement(pdata, 'p12')
        p12.text = string_utils.xstr(amount)  # 點數
        p13 = ET.SubElement(pdata, 'p13')
        p13.text = string_utils.xstr(self.sequence)  # 序號
        p14 = ET.SubElement(pdata, 'p14')
        p14.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        p15 = ET.SubElement(pdata, 'p15')
        p15.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        p16 = ET.SubElement(pdata, 'p16')
        p16.text = string_utils.xstr(row['DoctorID'])
        p17 = ET.SubElement(pdata, 'p17')
        p17.text = '2'  # 同一療程
        p20 = ET.SubElement(pdata, 'p20')
        p20.text = string_utils.xstr(row['Class'])

    def _set_prescript(self, dbody, row, case_row, prescript_rows, case_key, course):
        pres_days = case_utils.get_pres_days(self.database, case_key)
        packages = case_utils.get_packages(self.database, case_key)
        instruction = case_utils.get_instruction(self.database, case_key)
        if pres_days <= 0:
            return

        if number_utils.get_integer(row['DrugFee']) > 0:
            order_type = '1'  # 1=用藥明細
        else:
            order_type = '4'  # 4=不另計價

        self._set_A21(dbody, row, case_row, order_type, pres_days)
        if number_utils.get_integer(row['PharmacyFee']) > 0:
            self._set_pharmacy(dbody, row, case_row, pres_days, course)

        for prescript_row in prescript_rows:
            self._set_medicine(
                dbody, row, case_row, prescript_row, pres_days, packages, instruction
            )

    def _set_A21(self, dbody, row, case_row, order_type, pres_days):
        pdata = ET.SubElement(dbody, 'pdata')

        self.sequence += 1
        ins_code = 'A21'
        unit_price = number_utils.get_integer(
            charge_utils.get_diag_fee_from_diag_code(self.database, ins_code)
        )
        amount = unit_price * pres_days

        p1 = ET.SubElement(pdata, 'p1')
        p1.text = '{0}'.format(pres_days)  # 給藥日數
        p2 = ET.SubElement(pdata, 'p2')
        p2.text = '0'  # 0=自行調劑
        p3 = ET.SubElement(pdata, 'p3')
        p3.text = order_type  # 1=用藥明細 4=不另計價
        p4 = ET.SubElement(pdata, 'p4')
        p4.text = ins_code
        p5 = ET.SubElement(pdata, 'p5')
        p5.text = '{0:07.2f}'.format(pres_days)  # 用量
        p7 = ET.SubElement(pdata, 'p7')
        p7.text = 'QD'
        p8 = ET.SubElement(pdata, 'p8')
        p8.text = '{0:05.2f}'.format(100)  # 成數
        p9 = ET.SubElement(pdata, 'p9')
        p9.text = 'PO'  # 口服
        p10 = ET.SubElement(pdata, 'p10')
        p10.text = '{0:07.1f}'.format(pres_days)  # 總量
        p11 = ET.SubElement(pdata, 'p11')
        p11.text = string_utils.xstr(unit_price)  # 單價
        p12 = ET.SubElement(pdata, 'p12')
        p12.text = string_utils.xstr(amount)  # 點數
        p13 = ET.SubElement(pdata, 'p13')
        p13.text = string_utils.xstr(self.sequence)  # 序號
        p14 = ET.SubElement(pdata, 'p14')
        p14.text = '{0}0000'.format( date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        p15 = ET.SubElement(pdata, 'p15')
        p15.text = '{0}0000'.format( date_utils.west_date_to_nhi_date(
                    case_row['CaseDate'].date() + datetime.timedelta(days=pres_days-1))
        )
        p16 = ET.SubElement(pdata, 'p16')
        p16.text = string_utils.xstr(row['DoctorID'])
        p20 = ET.SubElement(pdata, 'p20')
        p20.text = string_utils.xstr(row['Class'])

    def _set_pharmacy(self, dbody, row, case_row, pres_days, course):
        if pres_days <= 0:
            return

        pharmacy_byte = string_utils.xstr(row['PharmacyCode'])[course-1]
        if pharmacy_byte in ['1', '2']:
            pharmacy_code = 'A3{0}'.format(pharmacy_byte)
        else:
            return

        pdata = ET.SubElement(dbody, 'pdata')

        self.sequence += 1
        unit_price = number_utils.get_integer(
            charge_utils.get_diag_fee_from_diag_code(self.database, pharmacy_code)
        )
        amount = unit_price

        p2 = ET.SubElement(pdata, 'p2')
        p2.text = '0'  # 0=自行調劑
        p3 = ET.SubElement(pdata, 'p3')
        p3.text = '9'  # 9=調劑費
        p4 = ET.SubElement(pdata, 'p4')
        p4.text = pharmacy_code
        p8 = ET.SubElement(pdata, 'p8')
        p8.text = '{0:05.2f}'.format(100)  # 成數
        p10 = ET.SubElement(pdata, 'p10')
        p10.text = '1'  # 總量
        p11 = ET.SubElement(pdata, 'p11')
        p11.text = string_utils.xstr(unit_price)  # 單價
        p12 = ET.SubElement(pdata, 'p12')
        p12.text = string_utils.xstr(amount)  # 點數
        p13 = ET.SubElement(pdata, 'p13')
        p13.text = string_utils.xstr(self.sequence)  # 序號
        p14 = ET.SubElement(pdata, 'p14')
        p14.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        p15 = ET.SubElement(pdata, 'p15')
        p15.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        p16 = ET.SubElement(pdata, 'p16')
        p16.text = string_utils.xstr(row['DoctorID'])
        p20 = ET.SubElement(pdata, 'p20')
        p20.text = string_utils.xstr(row['Class'])

    def _set_medicine(self, dbody, row, case_row, prescript_row, pres_days, packages, instruction):
        if pres_days <= 0 or packages <= 0:
            return

        pdata = ET.SubElement(dbody, 'pdata')

        self.sequence += 1
        unit_price = 0
        amount = unit_price

        p1 = ET.SubElement(pdata, 'p1')
        p1.text = string_utils.xstr(pres_days)  # 給藥天數
        p2 = ET.SubElement(pdata, 'p2')
        p2.text = '0'  # 0=自行調劑
        p3 = ET.SubElement(pdata, 'p3')
        p3.text = '4'  # 4=不另計價藥品
        p4 = ET.SubElement(pdata, 'p4')
        p4.text = string_utils.xstr(prescript_row['InsCode'])
        p5 = ET.SubElement(pdata, 'p5')
        p5.text = '{0:07.2f}'.format(prescript_row['Dosage'] / packages)     # 用量
        p7 = ET.SubElement(pdata, 'p7')
        p7.text = '{0}{1}'.format(nhi_utils.FREQUENCY[packages], self._get_usage(instruction))
        p8 = ET.SubElement(pdata, 'p8')
        p8.text = '{0:06.2f}'.format(100)  # 成數
        p9 = ET.SubElement(pdata, 'p9')
        p9.text = 'PO'  # 使用途徑
        p10 = ET.SubElement(pdata, 'p10')
        p10.text = '{0:07.1f}'.format(prescript_row['Dosage'] * pres_days)  # 總量
        p11 = ET.SubElement(pdata, 'p11')
        p11.text = string_utils.xstr(unit_price)  # 單價
        p12 = ET.SubElement(pdata, 'p12')
        p12.text = string_utils.xstr(amount)  # 點數
        p13 = ET.SubElement(pdata, 'p13')
        p13.text = string_utils.xstr(self.sequence)  # 序號
        p14 = ET.SubElement(pdata, 'p14')
        p14.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(case_row['CaseDate']))
        p15 = ET.SubElement(pdata, 'p15')
        p15.text = '{0}0000'.format(date_utils.west_date_to_nhi_date(
                    case_row['CaseDate'].date() + datetime.timedelta(days=pres_days-1))
        )
        p16 = ET.SubElement(pdata, 'p16')
        p16.text = string_utils.xstr(row['DoctorID'])
        p20 = ET.SubElement(pdata, 'p20')
        p20.text = string_utils.xstr(row['Class'])

    def _add_special_care_cases(self, dbody, row):
        self.sequence += 1

    def _set_special_care(self, dbody, row, case_row):
        self.sequence += 1

    def _get_pharmacy_code(self, pharmacy_code_str):
        pharmacy_count = 0
        pharmacy_code = ''
        for i in range(len(pharmacy_code_str)):
            if pharmacy_code_str[i] in ['1', '2']:
                pharmacy_code = 'A3{0}'.format(pharmacy_code_str[i])
                pharmacy_count += 1

            if pharmacy_count >= 2:
                pharmacy_code = ''
                break

        return pharmacy_code

    def _get_usage(self, instruction):
        if '飯前' in instruction:
            usage = 'AC'
        elif '飯後' in instruction:
            usage = 'PC'
        else:
            usage = 'PC'

        return usage

    def _get_name(self, in_name):
        name = ''
        for ch in in_name:
            try:
                name += str(ch).encode('big5').decode('big5')
            except:
                name += '◇'

        return name

    def _get_ins_rows(self):
        sql = '''
            SELECT *
            FROM insapply
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}"
                ORDER BY CaseType, Sequence
        '''.format(
            self.apply_date, self.apply_type_code, self.period, self.clinic_id,
        )
        rows = self.database.select_record(sql)

        return rows

    def _get_case_row(self, case_key):
        sql = '''
            SELECT *
            FROM cases
            WHERE
                CaseKey = "{0}"
        '''.format(case_key)

        rows = self.database.select_record(sql)

        return rows[0]

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

