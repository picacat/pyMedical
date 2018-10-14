import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo
from PyQt5 import QtPrintSupport

from libs import string_utils
from libs import number_utils
from libs import date_utils
from libs import case_utils
from libs import dialog_utils
from libs import nhi_utils

from printer.print_registration_form1 import *
from printer.print_registration_form2 import *

from printer.print_prescription_ins_form1 import *
from printer.print_prescription_self_form1 import *
from printer.print_receipt_ins_form1 import *
from printer.print_receipt_self_form1 import *

PRINT_MODE = ['不印', '列印', '詢問', '預覽']
PRINT_REGISTRATION_FORM = {
    '01-熱感紙掛號單': PrintRegistrationForm1,
    '02-11"中二刀空白掛號單': PrintRegistrationForm2,
}

PRINT_PRESCRIPTION_INS_FORM = {
    '01-11"中二刀健保處方箋': PrintPrescriptionInsForm1,
}

PRINT_PRESCRIPTION_SELF_FORM = {
    '01-11"中二刀自費處方箋': PrintPrescriptionSelfForm1,
}

PRINT_RECEIPT_INS_FORM = {
    '01-11"中二刀健保醫療收據': PrintReceiptInsForm1,
}
PRINT_RECEIPT_SELF_FORM = {
    '01-11"中二刀自費醫療收據': PrintReceiptSelfForm1,
}


# 取得印表機列表
def get_printer_list():
    printer_info = QPrinterInfo()
    printer_list = printer_info.availablePrinterNames()

    return printer_list


# 取得 text document 邊界
def get_document_margin():
    if sys.platform == 'win32':
        return 0
    else:
        return 0  # EPSON LQ-310 (driver: EPSON 24-pin series, resolution 360 * 180, paper size: US Letter


# 取得 text document
def get_document(printer, font):
    paper_size = QtCore.QSizeF()
    paper_size.setWidth(printer.width())
    paper_size.setHeight(printer.height())

    document = QtGui.QTextDocument()
    document.setDefaultFont(font)
    document.setPageSize(paper_size)

    return document


# 取得印表機
def get_printer(system_settings, printer_name):
    printer = QPrinter(QPrinter.ScreenResolution)
    printer.setPrinterName(system_settings.field(printer_name))
    printer.setPageMargins(0.08, 0.08, 0.08, 0.08, QPrinter.Inch)  # left, right, top, bottom

    return printer


# 處方箋格式1
def get_case_html_1(database, case_key):
    sql = '''
        SELECT * FROM cases 
            LEFT JOIN patient on patient.PatientKey = cases.PatientKey
        WHERE 
            CaseKey = {0}
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]
    card = string_utils.xstr(row['Card'])
    if number_utils.get_integer(row['Continuance']) >= 1:
        card += '-' + string_utils.xstr(row['Continuance'])

    birthday = row['Birthday']
    age = ''
    if birthday is not None:
        birthday = birthday.strftime('%Y****')
        age_year, age_month = date_utils.get_age(row['Birthday'], row['CaseDate'])
        if age_year is None:
            age = ''
        else:
            age = '{0}歲'.format(age_year)

    id = row['ID']
    if id is not None:
        id = id[:6] + '****'

    html = '''
        <tr>
          <td>門診日:{case_date}</td>
          <td>病歷號:{patient_key}</td>
          <td>姓名:{name} ({gender})</td>
          <td>身分證:{id}</td>
          <td colspan="2">生日:{birthday} {age}</td>
        </tr> 
        <tr>
          <td>保險別:{ins_type}</td>
          <td>負擔別:{share_type}</td>
          <td>卡序:{card}</td>
          <td>就診號:{regist_no}</td>
        </tr>
    '''.format(
        case_date=row['CaseDate'].strftime('%Y-%m-%d'),
        patient_key=string_utils.xstr(row['PatientKey']),
        name=string_utils.xstr(row['Name']),
        gender=string_utils.xstr(row['Gender']),
        birthday=string_utils.xstr(birthday),
        age=string_utils.xstr(age),
        id=string_utils.xstr(id),
        ins_type=string_utils.xstr(row['InsType']),
        share_type=string_utils.xstr(row['Share']),
        card=card,
        regist_no=string_utils.xstr(row['RegistNo']),
    )

    return html


# 處方箋格式(主訴)1
def get_symptom(database, case_key, colspan=1):
    sql = '''
        SELECT * FROM cases 
        WHERE 
            CaseKey = {0}
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]
    symptom = ''
    if string_utils.xstr(row['Symptom']) != '':
        symptom += '主訴:' + string_utils.get_str(row['Symptom'], 'utf8')
    if string_utils.xstr(row['Tongue']) != '':
        symptom += ' 舌診:' + string_utils.get_str(row['Tongue'], 'utf8')
    if string_utils.xstr(row['Pulse']) != '':
        symptom += ' 脈象:' + string_utils.get_str(row['Pulse'], 'utf8')
    if string_utils.xstr(row['Distincts']) != '':
        symptom += ' 辨證:' + string_utils.get_str(row['Distincts'], 'utf8')
    if string_utils.xstr(row['Cure']) != '':
        symptom += ' 治則:' + string_utils.get_str(row['Cure'], 'utf8')

    html = '''
        <tr>
          <td colspan="{colspan}">
            {symptom}
          </td>
        </tr>
    '''.format(
        symptom=symptom,
        colspan=colspan
    )

    return html


# 處方箋格式(診斷碼)1
def get_disease(database, case_key):
    sql = '''
        SELECT * FROM cases 
        WHERE 
            CaseKey = {0}
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]
    disease = ''
    if string_utils.xstr(row['DiseaseCode1']) != '':
        disease +=  '主診斷: {0} {1}'.format(
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseName1']),
        )
    if string_utils.xstr(row['DiseaseCode2']) != '':
        disease +=  ' / 次診斷1: {0} {1}'.format(
            string_utils.xstr(row['DiseaseCode2']),
            string_utils.xstr(row['DiseaseName2']),
        )
    if string_utils.xstr(row['DiseaseCode3']) != '':
        disease +=  ' / 次診斷2: {0} {1}'.format(
            string_utils.xstr(row['DiseaseCode3']),
            string_utils.xstr(row['DiseaseName3']),
        )

    return disease


def get_prescript_html_2(database, case_key, medicine_set):
    pres_days = case_utils.get_pres_days(database, case_key, medicine_set)
    sql = '''
        SELECT Treatment FROM cases
        WHERE
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    treatment = rows[0]['Treatment']


    sql = '''
        SELECT prescript.*, medicine.Location FROM prescript 
            LEFT JOIN medicine ON medicine.MedicineKey = prescript.MedicineKey
        WHERE 
            CaseKey = {0} AND
            MedicineSet = {1} AND
            (prescript.MedicineName IS NOT NULL OR LENGTH(prescript.MedicineName) > 0)
        ORDER BY PrescriptNo, PrescriptKey
    '''.format(case_key, medicine_set)

    rows = database.select_record(sql)
    if medicine_set == 1 and treatment in nhi_utils.INS_TREAT:
        if treatment in nhi_utils.ACUPUNCTURE_TREAT:
            medicine_type = '穴道'
        else:
            medicine_type = '處置'

        rows.insert(
            0,
            {
                'MedicineName': treatment,
                'MedicineType': medicine_type,
                'Dosage': 1,
                'Unit': '次',
                'Location': ''
            }
        )

    if len(rows) <= 0:
        return ''

    if pres_days is None or pres_days <= 0:
        pres_days = 1

    prescript = ''
    row_count = int((len(rows)-1) / 3) + 1
    for row_no in range(1, row_count+1):
        prescript_block1 = get_medicine_detail(rows, (row_no-1)*3, pres_days)
        prescript_block2 = get_medicine_detail(rows, (row_no-1)*3+1, pres_days)
        prescript_block3 = get_medicine_detail(rows, (row_no-1)*3+2, pres_days)

        separator = ''
        prescript += '''
            <tr>
                <td align="left" width="15%">{medicine_name1} {location1}</td>
                <td align="right" width="8%">{dosage1}{unit1}</td>
                <td align="right" width="4%">{total_dosage1}</td>
                <td width="2%">{separator}</td> 
                <td align="left" width="15%">{medicine_name2} {location2}</td>
                <td align="right" width="8%">{dosage2}{unit2}</td>
                <td align="right" width="4%">{total_dosage2}</td>
                <td width="2%">{separator}</td> 
                <td align="left" width="15%">{medicine_name3} {location3}</td>
                <td align="right" width="8%">{dosage3}{unit3}</td>
                <td align="right" width="4%">{total_dosage3}</td>
            </tr>
        '''.format(
            medicine_name1=string_utils.xstr(prescript_block1[0]),
            location1=string_utils.xstr(prescript_block1[1]),
            dosage1=string_utils.xstr(prescript_block1[2]),
            unit1=string_utils.xstr(prescript_block1[3]),
            total_dosage1=string_utils.xstr(prescript_block1[4]),

            medicine_name2=string_utils.xstr(prescript_block2[0]),
            location2=string_utils.xstr(prescript_block2[1]),
            dosage2=string_utils.xstr(prescript_block2[2]),
            unit2=string_utils.xstr(prescript_block2[3]),
            total_dosage2=string_utils.xstr(prescript_block2[4]),

            medicine_name3=string_utils.xstr(prescript_block3[0]),
            location3=string_utils.xstr(prescript_block3[1]),
            dosage3=string_utils.xstr(prescript_block3[2]),
            unit3=string_utils.xstr(prescript_block3[3]),
            total_dosage3=string_utils.xstr(prescript_block3[4]),

            separator=string_utils.xstr(separator),
        )

    return prescript


def get_medicine_detail(rows, row_no, pres_days):
    try:
        medicine_name = rows[row_no]['MedicineName']
        medicine_type = rows[row_no]['MedicineType']
        location = rows[row_no]['Location']
        if medicine_type in ['穴道', '處置', '檢驗']:
            dosage, unit, total_dosage = '', '', ''
        else:
            dosage = rows[row_no]['Dosage']
            total_dosage = dosage * pres_days
            dosage = format(dosage, '.1f')
            unit = rows[row_no]['Unit']
            total_dosage = format(total_dosage, '.1f')
    except (IndexError, TypeError):
        medicine_name, location, dosage, unit, total_dosage = '', '', '', '', ''  # ascii 0->null 填補

    return medicine_name, location, dosage, unit, total_dosage


def get_instruction_html(database, case_key, medicine_set):
    pres_days = case_utils.get_pres_days(database, case_key, medicine_set)
    packages = case_utils.get_packages(database, case_key, medicine_set)
    instruction = case_utils.get_instruction(database, case_key, medicine_set)

    sql = '''
        SELECT * FROM cases 
        WHERE 
            CaseKey = {0}
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]

    html = '''
        <p>
          主治醫師: {doctor} 調劑者: {doctor} 用藥指示: 一日{package}包, 共{pres_days}日份 {instruction}服用
        </p>
    '''.format(
        doctor=string_utils.xstr(row['Doctor']),
        package=string_utils.xstr(packages),
        pres_days=string_utils.xstr(pres_days),
        instruction=instruction,
    )

    return html


# 取得列印健保或自費處方dialog
def get_medicine_set_items(database, case_key):
    sql = '''
        SELECT InsType FROM cases
        WHERE
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    ins_type = rows[0]['InsType']

    sql = '''
        SELECT MedicineSet FROM prescript
        WHERE
            CaseKey = {0}
        GROUP BY MedicineSet
        ORDER BY MedicineSet
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ('{0}處方'.format(ins_type), None)
    elif len(rows) == 1:
        medicine_set = rows[0]['MedicineSet']
        if medicine_set == 1:
            item = '健保處方'
        else:
            item = '自費處方'

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
        medicine_set = number_utils.get_integer(item.split('自費處方')[1]) + 1
        item = '自費處方'

    return (item, medicine_set)


# 取得列印健保或自費收據dialog
def get_receipt_items(database, case_key):
    sql = '''
        SELECT InsType FROM cases
        WHERE
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    ins_type = rows[0]['InsType']

    sql = '''
        SELECT MedicineSet FROM prescript
        WHERE
            CaseKey = {0}
        GROUP BY MedicineSet
        ORDER BY MedicineSet
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 1:
        return '{0}醫療收據'.format(ins_type)
    elif ins_type == '自費':  # 掛自費只印自費收據
        return '自費醫療收據'

    items = ['全部醫療收據']
    for row in rows:
        medicine_set = row['MedicineSet']
        if medicine_set == 1:
            items.append('健保醫療收據')
        else:
            items.append('自費醫療收據')

        if len(items) >= 3:
            break

    input_dialog = dialog_utils.get_dialog(
        '多重醫療收據', '請選擇欲列印的醫療收據',
        None, QInputDialog.TextInput, 320, 200)
    input_dialog.setComboBoxItems(items)
    ok = input_dialog.exec_()

    if not ok:
        return None

    item = input_dialog.textValue()
    if item == '全部醫療收據':
        del items[0]
        return items
    else:
        return item


# 列印門診掛號單
def print_registration(parent, database, system_settings, case_key, print_type, printable=None):
    if printable is None:
        printable = system_settings.field('列印門診掛號單')

    if printable == '不印':
        return

    if system_settings.field('列印門診掛號單') == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif system_settings.field('列印門診掛號單') == '預覽':
        print_type = 'preview'

    form = system_settings.field('門診掛號單格式')
    if form not in list(printer_utils.PRINT_REGISTRATION_FORM.keys()):
        return

    print_registration_form = PRINT_REGISTRATION_FORM[form](
        parent, database, system_settings, case_key)
    if print_type == 'print':
        print_registration_form.print()
    else:
        print_registration_form.preview()

    del print_registration_form


# 列印健保處方箋
def print_ins_prescript(parent, database, system_settings, case_key, print_type, printable=None):
    if printable is None:
        printable = system_settings.field('列印健保處方箋')

    if printable == '不印':
        return

    if system_settings.field('列印健保處方箋') == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif system_settings.field('列印健保處方箋') == '預覽':
        print_type = 'preview'

    form = system_settings.field('健保處方箋格式')
    if form not in list(PRINT_PRESCRIPTION_INS_FORM.keys()):
        return

    print_prescription_form = PRINT_PRESCRIPTION_INS_FORM[form](
        parent, database, system_settings, case_key)

    if print_type == 'print':
        print_prescription_form.print()
    else:
        print_prescription_form.preview()

    del print_prescription_form


# 列印自費處方箋
def print_self_prescript(parent, database, system_settings, case_key, medicine_set, print_type, printable=None):
    if printable is None:
        printable = system_settings.field('列印自費處方箋')

    if printable == '不印':
        return

    if system_settings.field('列印自費處方箋') == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif system_settings.field('列印自費處方箋') == '預覽':
        print_type = 'preview'

    form = system_settings.field('自費處方箋格式')
    if form not in list(PRINT_PRESCRIPTION_SELF_FORM.keys()):
        return

    print_prescription_form = PRINT_PRESCRIPTION_SELF_FORM[form](
        parent, database, system_settings, case_key, medicine_set)
    if print_type == 'print':
        print_prescription_form.print()
    else:
        print_prescription_form.preview()

    del print_prescription_form


# 列印健保醫療收據
def print_ins_receipt(parent, database, system_settings, case_key, print_type, printable=None):
    if printable is None:
        printable = system_settings.field('列印健保醫療收據')

    if printable == '不印':
        return

    if system_settings.field('列印健保醫療收據') == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif system_settings.field('列印健保醫療收據') == '預覽':
        print_type = 'preview'

    form = system_settings.field('健保醫療收據格式')
    if form not in list(PRINT_RECEIPT_INS_FORM.keys()):
        return

    print_receipt_form = PRINT_RECEIPT_INS_FORM[form](
        parent, database, system_settings, case_key)

    if print_type == 'print':
        print_receipt_form.print()
    else:
        print_receipt_form.preview()

    del print_receipt_form


# 列印自費醫療收據
def print_self_receipt(parent, database, system_settings, case_key, print_type, printable=None):
    if printable is None:
        printable = system_settings.field('列印自費醫療收據')

    if printable == '不印':
        return

    if system_settings.field('列印自費醫療收據') == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif system_settings.field('列印自費醫療收據') == '預覽':
        print_type = 'preview'

    form = system_settings.field('自費醫療收據格式')
    if form not in list(PRINT_RECEIPT_SELF_FORM.keys()):
        return

    print_receipt_form = PRINT_RECEIPT_SELF_FORM[form](
        parent, database, system_settings, case_key)

    if print_type == 'print':
        print_receipt_form.print()
    else:
        print_receipt_form.preview()

    del print_receipt_form
