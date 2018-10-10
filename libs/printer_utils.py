import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo

from libs import string_utils
from libs import number_utils
from libs import date_utils
from libs import case_utils

PRINT_REGISTRATION_FORM = ['01-熱感紙掛號單', '02-11"中二刀空白掛號單']
PRINT_PRESCRIPTION_INS_FORM = ['01-11"中二刀處方箋', ]
PRINT_MODE = ['不印', '列印', '詢問', ]


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
def get_case_html_1(database, case_key, colspan=1):
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

    html = '''
        <table cellspacing="0">
          <tbody>
            <tr>
              <td>門診日:{case_date}</td>
              <td>病歷號:{patient_key}</td>
              <td>姓名:{name} ({gender})</td>
              <td>身分證:{id}</td>
              <td colspan=2>生日:{birthday} {age}</td>
            </tr> 
            <tr>
              <td>保險別:{ins_type}</td>
              <td>負擔別:{share_type}</td>
              <td>卡序:{card}</td>
              <td>就診號:{regist_no}</td>
            </tr>
            <tr>
              <td colspan="{colspan}">
                {symptom}
              </td>
            </tr>
          </tbody>
        </table>
        {disease}
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
        symptom=symptom,
        disease=disease,
        colspan=colspan
    )

    return html


def get_prescript_html_2(database, case_key, medicine_set):
    pres_days = case_utils.get_pres_days(database, case_key, medicine_set)

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
    if len(rows) <= 0:
        return ''

    if pres_days is None or pres_days <= 0:
        pres_days = 1

    prescript = ''
    row_count = int((len(rows)-1) / 3) + 1
    for row_no in range(1, row_count+1):
        try:
            medicine_name1 = rows[(row_no-1)*3]['MedicineName']
            location1 = rows[(row_no-1)*3]['Location']
            dosage1 = rows[(row_no-1)*3]['Dosage']
            unit1 = rows[(row_no-1)*3]['Unit']
            total_dosage1 = dosage1 * pres_days
            dosage1 = format(dosage1, '.1f')
            total_dosage1 = format(total_dosage1, '.1f')
        except (IndexError, TypeError):
            medicine_name1, location1, dosage1, unit1, total_dosage1 = '', '', '', '', ''

        try:
            medicine_name2 = rows[(row_no-1)*3+1]['MedicineName']
            location2 = rows[(row_no-1)*3]['Location']
            dosage2 = rows[(row_no-1)*3+1]['Dosage']
            unit2 = rows[(row_no-1)*3+1]['Unit']
            total_dosage2 = dosage2 * pres_days
            dosage2 = format(dosage2, '.1f')
            total_dosage2 = format(total_dosage2, '.1f')
        except (IndexError, TypeError):
            medicine_name2, location2, dosage2, unit2, total_dosage2 = '', '', '', '', ''

        try:
            medicine_name3 = rows[(row_no-1)*3+2]['MedicineName']
            location3 = rows[(row_no-1)*3]['Location']
            dosage3 = rows[(row_no-1)*3+2]['Dosage']
            unit3 = rows[(row_no-1)*3+2]['Unit']
            total_dosage3 = dosage3 * pres_days
            dosage3 = format(dosage3, '.1f')
            total_dosage3 = format(total_dosage3, '.1f')
        except (IndexError, TypeError):
            medicine_name3, location3, dosage3, unit3, total_dosage3 = '', '', '', '', ''

        separator = ' '
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
            medicine_name1=string_utils.xstr(medicine_name1),
            location1=string_utils.xstr(location1),
            dosage1=string_utils.xstr(dosage1),
            unit1=string_utils.xstr(unit1),
            total_dosage1=string_utils.xstr(total_dosage1),

            medicine_name2=string_utils.xstr(medicine_name2),
            location2=string_utils.xstr(location2),
            dosage2=string_utils.xstr(dosage2),
            unit2=string_utils.xstr(unit2),
            total_dosage2=string_utils.xstr(total_dosage2),

            medicine_name3=string_utils.xstr(medicine_name3),
            location3=string_utils.xstr(location3),
            dosage3=string_utils.xstr(dosage3),
            unit3=string_utils.xstr(unit3),
            total_dosage3=string_utils.xstr(total_dosage3),

            separator=string_utils.xstr(separator),
        )

    html = '''
        <table>
          <tbody>
            {0}
          </tbody>
        </table>        
    '''.format(prescript)

    return html


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
