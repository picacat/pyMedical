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
from printer.print_ins_apply_total_fee import *
from printer.print_ins_apply_order import *
from printer.print_medical_records import *
from printer.print_medical_chart import *

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
def get_case_html_1(database, case_key, background_color=None):
    sql = '''
        SELECT cases.*, patient.Birthday, patient.ID, patient.Gender FROM cases 
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

    if background_color is not None:
        color = ' style="background-color: {0}"'.format(background_color)
    else:
        color = ''

    html = '''
        <tr>
          <td{color}>門診日:{case_date}</td>
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
        color=color,
    )

    return html


# 處方箋格式(主訴)1
def get_symptom_html(database, case_key, colspan=1):
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


def get_prescript_html(database, system_setting, case_key, medicine_set, blocks, print_total_dosage=True):
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
    row_count = int((len(rows)-1) / blocks) + 1
    for row_no in range(1, row_count+1):
        separator = ''
        prescript_line = ''
        for i in range(blocks):
            prescript_block = get_medicine_detail(rows, (row_no-1)*blocks + i, pres_days)

            location=string_utils.xstr(prescript_block[1])
            if system_setting.field('列印藥品存放位置') != 'Y':
                location = ''

            total_dosage=string_utils.xstr(prescript_block[4])
            if system_setting.field('列印藥品總量') != 'Y' or not print_total_dosage:
                total_dosage = ''

            prescript_line += '''
                <td align="left" width="20%">{medicine_name} {location}</td>
                <td align="right" width="5%">{dosage}{unit}</td>
                <td align="right" width="4%">{total_dosage}</td>
                <td width="1%">{separator}</td> 
            '''.format(
                medicine_name=string_utils.xstr(prescript_block[0]),
                location=location,
                dosage=string_utils.xstr(prescript_block[2]),
                unit=string_utils.xstr(prescript_block[3]),
                total_dosage=total_dosage,
                separator=string_utils.xstr(separator),
            )

        prescript += '''
            <tr>
              {prescript_line}
            </tr>
        '''.format(
            prescript_line=prescript_line
        )

    return prescript


# 健保費用
def get_ins_fees_html(database, case_key):
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
    html = '''
        <tr>
          <td>掛號費:{regist_fee}</td>
          <td>門診負擔:{diag_share_fee}</td>
          <td>藥品負擔:{drug_share_fee}</td>
          <td>實收負擔:{total_share_fee}</td>
          <td>欠卡費:{deposit_fee}</td>
          <td>實收金額:{total_fee}</td>
        </tr> 
        <tr>
          <td>診察費:{diag_fee}</td>
          <td>藥費:{drug_fee}</td>
          <td>調劑費:{pharmacy_fee}</td>
          <td>處置費:{treat_fee}</td>
          <td>健保合計:{ins_total_fee}</td>
          <td>健保申請:{ins_apply_fee}</td>
        </tr> 
    '''.format(
        regist_fee=string_utils.xstr(number_utils.get_integer(row['RegistFee'])),
        diag_share_fee=string_utils.xstr(number_utils.get_integer(row['SDiagShareFee'])),
        drug_share_fee=string_utils.xstr(number_utils.get_integer(row['SDrugShareFee'])),
        total_share_fee=string_utils.xstr(
            number_utils.get_integer(row['SDiagShareFee']) +
            number_utils.get_integer(row['SDrugShareFee'])
        ),
        deposit_fee=string_utils.xstr(number_utils.get_integer(row['DepositFee'])),
        total_fee=string_utils.xstr(
            number_utils.get_integer(row['RegistFee']) +
            number_utils.get_integer(row['SDiagShareFee']) +
            number_utils.get_integer(row['SDrugShareFee']) +
            number_utils.get_integer(row['DepositFee'])
        ),
        diag_fee=string_utils.xstr(number_utils.get_integer(row['DiagFee'])),
        drug_fee=string_utils.xstr(number_utils.get_integer(row['InterDrugFee'])),
        pharmacy_fee=string_utils.xstr(number_utils.get_integer(row['PharmacyFee'])),
        treat_fee=string_utils.xstr(
            number_utils.get_integer(row['AcupunctureFee']) +
            number_utils.get_integer(row['MassageFee']) +
            number_utils.get_integer(row['DislocateFee'])
        ),
        ins_total_fee=string_utils.xstr(number_utils.get_integer(row['InsTotalFee'])),
        ins_apply_fee=string_utils.xstr(number_utils.get_integer(row['InsApplyFee'])),
    )

    return html


# 自費費用
def get_self_fees_html(database, case_key):
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
    regist_fee = number_utils.get_integer(row['RegistFee'])
    if row['InsType'] == '健保':
        regist_fee = 0

    html = '''
        <tr>
          <td>掛號費:{regist_fee}</td>
          <td>診察費:{diag_fee}</td>
          <td>一般藥費:{drug_fee}</td>
          <td>水煎藥費:{herb_fee}</td>
          <td>高貴藥費:{expensive_fee}</td>
          <td>自費材料費:{material_fee}</td>
        </tr>
        <tr>  
          <td>針灸治療費:{acupuncture_fee}</td>
          <td>民俗調理費:{massage_fee}</td>
          <td>合計金額:{self_total_fee}</td>
          <td>折扣金額:{discount_fee}</td>
          <td>應收金額:{total_fee}</td>
          <td>實收金額:{receipt_fee}</td>
        </tr> 
    '''.format(
        regist_fee=string_utils.xstr(regist_fee),
        diag_fee=string_utils.xstr(number_utils.get_integer(row['SDiagFee'])),
        drug_fee=string_utils.xstr(number_utils.get_integer(row['SDrugFee'])),
        herb_fee=string_utils.xstr(number_utils.get_integer(row['SHerbFee'])),
        expensive_fee=string_utils.xstr(number_utils.get_integer(row['SExpensiveFee'])),
        material_fee=string_utils.xstr(number_utils.get_integer(row['SMaterialFee'])),

        acupuncture_fee=string_utils.xstr(number_utils.get_integer(row['SAcupunctureFee'])),
        massage_fee=string_utils.xstr(number_utils.get_integer(row['SMassageFee'])),
        self_total_fee=string_utils.xstr(number_utils.get_integer(row['SelfTotalFee'])),
        discount_fee=string_utils.xstr(number_utils.get_integer(row['DiscountFee'])),
        total_fee=string_utils.xstr(number_utils.get_integer(row['TotalFee'])),
        receipt_fee=string_utils.xstr(number_utils.get_integer(row['ReceiptFee'])),
    )

    return html
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

    if pres_days > 0:
        html = '''
              主治醫師: {doctor} 調劑者: {doctor} 用藥指示: 一日{package}包, 共{pres_days}日份 {instruction}服用
        '''.format(
            doctor=string_utils.xstr(row['Doctor']),
            package=string_utils.xstr(packages),
            pres_days=string_utils.xstr(pres_days),
            instruction=instruction,
        )
    else:
        html = '''
              主治醫師: {doctor}
        '''.format(
            doctor=string_utils.xstr(row['Doctor']),
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


# 列印申請總表
def print_ins_apply_total_fee(parent, database, system_settings, html):
    print_type = 'print'

    if system_settings.field('列印報表') == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif system_settings.field('列印報表') == '預覽':
        print_type = 'preview'

    print_total_fee = PrintInsApplyTotalFee(
        parent, database, system_settings,
        html
    )

    if print_type == 'print':
        print_total_fee.print()
    else:
        print_total_fee.preview()

    del print_total_fee


# 列印醫令明細
def print_ins_apply_order(parent, database, system_settings,
                          apply_year, apply_month, apply_type, ins_apply_key, print_type=None):
    if print_type is None:  # 如果未指定列印方式，以系統設定為主
        if system_settings.field('列印報表') == '不印':
            return
        elif system_settings.field('列印報表') == '詢問':
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec() == QtWidgets.QDialog.Rejected:
                return
        elif system_settings.field('列印報表') == '預覽':
            print_type = 'preview'
        elif system_settings.field('列印報表') == '列印':
            print_type = 'print'

    print_ins_order = PrintInsApplyOrder(
        parent, database, system_settings,
        apply_year, apply_month,
        apply_type, ins_apply_key
    )

    if print_type == 'print':
        print_ins_order.print()
    elif print_type == 'preview':
        print_ins_order.preview()
    elif print_type == 'pdf':
        print_ins_order.save_to_pdf()

    del print_ins_order


# 列印雙月病歷
def print_medical_records(parent, database, system_settings,
                          patient_key, start_date, end_date, print_type=None):
    if print_type is None:  # 如果未指定列印方式，以系統設定為主
        if system_settings.field('列印報表') == '不印':
            return
        elif system_settings.field('列印報表') == '詢問':
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec() == QtWidgets.QDialog.Rejected:
                return
        elif system_settings.field('列印報表') == '預覽':
            print_type = 'preview'
        elif system_settings.field('列印報表') == '列印':
            print_type = 'print'

    print_cases = PrintMedicalRecords(
        parent, database, system_settings,
        patient_key, start_date, end_date,
    )

    if print_type == 'print':
        print_cases.print()
    elif print_type == 'preview':
        print_cases.preview()
    elif print_type == 'pdf':
        print_cases.save_to_pdf()

    del print_cases


# 列印雙月病歷首頁
def print_medical_chart(parent, database, system_settings, patient_key, apply_date, print_type=None):
    if print_type is None:  # 如果未指定列印方式，以系統設定為主
        if system_settings.field('列印報表') == '不印':
            return
        elif system_settings.field('列印報表') == '詢問':
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec() == QtWidgets.QDialog.Rejected:
                return
        elif system_settings.field('列印報表') == '預覽':
            print_type = 'preview'
        elif system_settings.field('列印報表') == '列印':
            print_type = 'print'

    print_chart = PrintMedicalChart(
        parent, database, system_settings,
        patient_key, apply_date,
    )

    if print_type == 'print':
        print_chart.print()
    elif print_type == 'preview':
        print_chart.preview()
    elif print_type == 'pdf':
        print_chart.save_to_pdf()

    del print_chart
