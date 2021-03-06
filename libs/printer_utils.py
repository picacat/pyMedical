import sys
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtPrintSupport import QPrinterInfo

from libs import dialog_utils

from printer.print_registration_form1 import *
from printer.print_registration_form2 import *
from printer.print_registration_form3 import *
from printer.print_registration_form4 import *
from printer.print_registration_form5 import *
from printer.print_registration_form6 import *

from printer.print_prescription_ins_form1 import *
from printer.print_prescription_ins_form2 import *
from printer.print_prescription_ins_form3 import *
from printer.print_prescription_ins_form4 import *
from printer.print_prescription_ins_form5 import *
from printer.print_prescription_ins_form6 import *

from printer.print_prescription_self_form1 import *
from printer.print_prescription_self_form2 import *
from printer.print_prescription_self_form3 import *
from printer.print_prescription_self_form4 import *
from printer.print_prescription_self_form5 import *
from printer.print_prescription_self_form6 import *

from printer.print_receipt_ins_form1 import *
from printer.print_receipt_ins_form2 import *
from printer.print_receipt_ins_form3 import *
from printer.print_receipt_ins_form4 import *
from printer.print_receipt_ins_form5 import *
from printer.print_receipt_ins_form6 import *
from printer.print_receipt_ins_form7 import *

from printer.print_receipt_self_form1 import *
from printer.print_receipt_self_form2 import *
from printer.print_receipt_self_form3 import *
from printer.print_receipt_self_form4 import *
from printer.print_receipt_self_form5 import *
from printer.print_receipt_self_form6 import *
from printer.print_receipt_self_form7 import *

from printer.print_misc_form5 import *

from printer.print_reservation_form5 import *

from printer.print_ins_apply_total_fee import *
from printer.print_ins_apply_order import *
from printer.print_ins_apply_schedule_table import *
from printer.print_html import *

from printer.print_medical_records import *
from printer.print_medical_fees import *
from printer.print_medical_chart import *

from printer.print_certificate_diagnosis import *
from printer.print_certificate_payment import *
from printer.print_certificate_payment_total import *
from printer.print_certificate_payment_prescript import *

PRINT_MODE = ['不印', '列印', '藥品', '詢問', '預覽']
PRINT_REGISTRATION_FORM = {
    '01-熱感紙掛號單': PrintRegistrationForm1,
    '02-11"中二刀空白掛號單': PrintRegistrationForm2,
    '03-3"套表掛號單': PrintRegistrationForm3,
    '04-2.5x3"熱感掛號單': PrintRegistrationForm4,
    '05-3"套表掛號單': PrintRegistrationForm5,
    '06-3"套表掛號單': PrintRegistrationForm6,
}

PRINT_PRESCRIPTION_INS_FORM = {
    '01-11"中二刀健保處方箋': PrintPrescriptionInsForm1,
    '02-2"健保處方箋': PrintPrescriptionInsForm2,
    '03-3"健保處方箋': PrintPrescriptionInsForm3,
    '04-4"健保處方箋': PrintPrescriptionInsForm4,
    '05-2.5"健保處方箋': PrintPrescriptionInsForm5,
    '06-A6健保處方箋': PrintPrescriptionInsForm6,
}

PRINT_PRESCRIPTION_SELF_FORM = {
    '01-11"中二刀自費處方箋': PrintPrescriptionSelfForm1,
    '02-2"自費處方箋': PrintPrescriptionSelfForm2,
    '03-3"自費處方箋': PrintPrescriptionSelfForm3,
    '04-4"自費處方箋': PrintPrescriptionSelfForm4,
    '05-2.5"自費處方箋': PrintPrescriptionSelfForm5,
    '06-A6健保處方箋': PrintPrescriptionSelfForm6,
}

PRINT_RECEIPT_INS_FORM = {
    '01-11"中二刀健保醫療收據': PrintReceiptInsForm1,
    '02-2"健保醫療收據': PrintReceiptInsForm2,
    '03-3"健保醫療收據': PrintReceiptInsForm3,
    '04-4"健保醫療收據': PrintReceiptInsForm4,
    '05-2.5"健保醫療收據': PrintReceiptInsForm5,
    '06-3"友杏格式健保醫療收據': PrintReceiptInsForm6,
    '07-A6健保醫療收據': PrintReceiptInsForm7,
}

PRINT_RECEIPT_SELF_FORM = {
    '01-11"中二刀自費醫療收據': PrintReceiptSelfForm1,
    '02-2"自費醫療收據': PrintReceiptSelfForm2,
    '03-3"自費醫療收據': PrintReceiptSelfForm3,
    '04-4"自費醫療收據': PrintReceiptSelfForm4,
    '05-2.5"自費醫療收據': PrintReceiptSelfForm5,
    '06-3"友杏格式自費醫療收據': PrintReceiptSelfForm6,
    '07-A6自費醫療收據': PrintReceiptSelfForm7,
}

PRINT_MISC_FORM = {
    '05-2.5"醫療費用收據': PrintMiscForm5,
}

PRINT_RESERVATION_FORM = {
    '05-2.5"預約單': PrintReservationForm5,
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


# 處方箋格式1,2使用
def get_case_html_1(database, case_key, ins_type, background_color=None):
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
          <td colspan="2">生日:{birthday}</td>
        </tr> 
    '''.format(
        case_date=row['CaseDate'].strftime('%Y-%m-%d'),
        patient_key=string_utils.xstr(row['PatientKey']),
        name=string_utils.xstr(row['Name']),
        gender=string_utils.xstr(row['Gender']),
        id=string_utils.xstr(id),
        birthday=string_utils.xstr(birthday),
        color=color,
    )

    if ins_type == '健保':
        html += '''
            <tr>
              <td>保險別:{ins_type}</td>
              <td>負擔別:{share_type}</td>
              <td>卡序:{card}</td>
              <td>就診號:{regist_no}</td>
            </tr>
        '''.format(
            ins_type=ins_type,
            share_type=string_utils.xstr(row['Share']),
            card=card,
            regist_no=string_utils.xstr(row['RegistNo']),
        )
    elif ins_type == '全部':
        pass
    else:
        html += '''
            <tr>
              <td>保險別:{ins_type}</td>
              <td>就診號:{regist_no}</td>
            </tr>
        '''.format(
            ins_type=ins_type,
            regist_no=string_utils.xstr(row['RegistNo']),
        )

    return html


# 處方箋格式3使用
def get_case_html_2(database, case_key, ins_type, background_color=None):
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
        birthday = birthday.strftime('%Y-*-*')
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
          <td{color} width="30%">門診日:{case_date}</td>
          <td width="20%">病歷號:{patient_key}</td>
          <td width="28%">姓名:{name}({gender})</td>
          <td width="22%">生日:{birthday}</td>
        </tr> 
    '''.format(
        case_date=row['CaseDate'].strftime('%Y-%m-%d'),
        patient_key=string_utils.xstr(row['PatientKey']),
        name=string_utils.xstr(row['Name']),
        gender=string_utils.xstr(row['Gender']),
        birthday=string_utils.xstr(birthday),
        color=color,
    )

    if ins_type == '健保':
        html += '''
            <tr>
              <td>身分證:{id}</td>
              <td>保險別:{ins_type}</td>
              <td>負擔:{share_type}</td>
              <td>卡序:{card}</td>
            </tr>
        '''.format(
            id=string_utils.xstr(id),
            ins_type=ins_type,
            share_type=string_utils.xstr(row['Share']),
            card=card,
        )
    else:
        html += '''
            <tr>
              <td>身分證:{id}</td>
              <td>保險別:{ins_type}</td>
            </tr>
        '''.format(
            id=string_utils.xstr(id),
            ins_type=ins_type,
        )

    return html


# 處方箋格式6使用
def get_case_html_3(database, case_key, ins_type, medicine_set, background_color=None):
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
    if birthday is not None:
        birthday = birthday.strftime('%Y-*-*')
    else:
        birthday = ''

    patient_id = row['ID']
    if patient_id is not None:
        patient_id = patient_id[:6] + '****'

    if background_color is not None:
        color = ' style="background-color: {0}"'.format(background_color)
    else:
        color = ''

    if ins_type == '健保':
        html = '''
            <tr>
              <td width="33%">姓名:{name} ({gender})</td>
              <td width="34%">出生日:{birthday}</td>
              <td width="33%">健保卡序:{card}</td>
            </tr> 
        '''.format(
            name=string_utils.xstr(row['Name']),
            gender=string_utils.xstr(row['Gender']),
            birthday=string_utils.xstr(birthday),
            color=color,
            card=card,
        )
    else:
        html = '''
            <tr>
              <td width="33%">姓名:{name} ({gender})</td>
              <td width="34%">出生日:{birthday}</td>
              <td width="33%">保險別:{ins_type} ({medicine_set})</td>
            </tr> 
        '''.format(
            name=string_utils.xstr(row['Name']),
            gender=string_utils.xstr(row['Gender']),
            birthday=string_utils.xstr(birthday),
            color=color,
            ins_type=ins_type,
            medicine_set=medicine_set-1,
        )

    html += '''
        <tr>
          <td width="30%">病歷號:{patient_key}</td>
          <td width="30%">身分證:{patient_id}</td>
          <td width="40%">就診日:{case_date}</td>
        </tr>
    '''.format(
            patient_key=string_utils.xstr(row['PatientKey']),
            patient_id=string_utils.xstr(patient_id),
            case_date=row['CaseDate'].strftime('%Y-%m-%d'),
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


def get_self_prescript_html(database, system_setting, case_key):
    sql = '''
        SELECT * FROM prescript 
        WHERE 
            CaseKey = {case_key} AND
            MedicineSet = 2
        ORDER BY MedicineSet, PrescriptNo, PrescriptKey
    '''.format(
        case_key=case_key,
    )

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    prescript_line = ''
    for row in rows:
        try:
            unit_price = '{0:.1f}'.format(row['Price'])
        except:
            unit_price = '0.0'

        try:
            dosage = '{0:.1f}'.format(row['Dosage'])
        except:
            dosage = '0.0'

        try:
            total_amount = '{0:.1f}'.format(row['Amount'])
        except:
            total_amount = '0.0'

        prescript_line += '''
            <tr>
                <td align="left" width="40%">{medicine_name}</td>
                <td align="right" width="10%">{unit_price}</td>
                <td align="right" width="10%">{dosage}{unit}</td>
                <td align="right" width="10%">{total_amount}</td>
                <td width="20%"></td>
            </tr>
        '''.format(
            medicine_name=string_utils.xstr(row['MedicineName']),
            unit=string_utils.xstr(row['Unit']),
            unit_price=unit_price,
            dosage=dosage,
            total_amount=total_amount,
        )

    prescript = '''
        <tr>
            <th align="left">處方名稱</th>
            <th align="right">單價</th>
            <th align="right">數量</th>
            <th align="right">金額</th>
        </tr>
        {prescript_line}
    '''.format(
        prescript_line=prescript_line,
    )
    return prescript


def get_instruction_condition(case_key, medicine_set, instruction=None):
    instruction_condition = ''

    if medicine_set == 1:
        instruction_condition = '''
            AND (
                prescript.Instruction IS NULL OR
                TRIM(prescript.Instruction) NOT IN("+", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10")
            )
        '''
        if instruction == '健保另包':
            instruction_condition = '''
                AND (
                    prescript.Instruction IS NOT NULL AND 
                    TRIM(prescript.Instruction) = "+"
                )
            '''

    elif medicine_set >= 2:
        instruction_condition = '''
            OR (
                CaseKey = {case_key} AND
                MedicineSet = 1 AND
                TRIM(prescript.Instruction) = "{medicine_set}"
            )
        '''.format(
            case_key=case_key,
            medicine_set=medicine_set-1,
        )

    return instruction_condition


def is_additional_prescript(database, case_key):
    sql = '''
        SELECT PrescriptKey FROM prescript
        WHERE
            CaseKey = {case_key} AND
            MedicineSet = 1 AND
            Instruction = "+"
    '''.format(
        case_key=case_key,
    )
    rows = database.select_record(sql)

    if len(rows) > 0:
        return True
    else:
        return False


def get_prescript_html(database, system_setting, case_key, medicine_set,
                       print_type, print_alias, print_total_dosage, blocks, instruction=None):
    if medicine_set is None:
        prescript = '''
            <tr>
              <td>無處方</td>
            </tr>
            <hr>
        '''
        return prescript

    pres_days = case_utils.get_pres_days(database, case_key, medicine_set)
    if pres_days <= 0 and instruction == '健保另包':
        return ''

    sql = '''
        SELECT Treatment FROM cases
        WHERE
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    treatment = rows[0]['Treatment']

    treat_condition = ''
    if print_type == '費用收據' and system_setting.field('列印穴道處置') == 'N' and medicine_set == 1:  # 健保才過濾
        treat_condition = ' AND (prescript.MedicineType NOT IN ("穴道")) '

    sql = '''
        SELECT prescript.*, medicine.Location, medicine.MedicineAlias FROM prescript 
            LEFT JOIN medicine ON medicine.MedicineKey = prescript.MedicineKey
        WHERE 
            CaseKey = {case_key} AND
            MedicineSet = {medicine_set} AND
            (prescript.MedicineName IS NOT NULL AND LENGTH(prescript.MedicineName) > 0)
            {treat_condition}
            {instruction_condition}
        ORDER BY PrescriptNo, PrescriptKey
    '''.format(
        case_key=case_key,
        medicine_set=medicine_set,
        treat_condition=treat_condition,
        instruction_condition=get_instruction_condition(case_key, medicine_set, instruction),
    )

    rows = database.select_record(sql)
    if medicine_set == 1 and treatment in nhi_utils.INS_TREAT and instruction != '健保另包':
        if treatment in nhi_utils.ACUPUNCTURE_TREAT:
            medicine_type = '穴道'
        else:
            medicine_type = '處置'

        rows.insert(
            0,
            {
                'MedicineName': treatment,
                'MedicineAlias': treatment,
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

    block_width = {
        3: {'medicine_name_width': 20,
            'dosage_width': 5,
            'total_dosage_width': 4,
            'separator_width': 1},
        2: {'medicine_name_width': 30,
            'dosage_width': 10,
            'total_dosage_width': 8,
            'separator_width': 1},
        1: {'medicine_name_width': 50,
            'dosage_width': 20,
            'total_dosage_width': 10,
            'separator_width': 4},
    }

    prescript = ''
    row_count = int((len(rows)-1) / blocks) + 1
    for row_no in range(1, row_count+1):
        separator = ''
        prescript_line = ''
        for i in range(blocks):
            prescript_block = get_medicine_detail(
                medicine_set,
                rows, (row_no-1)*blocks + i, pres_days, print_alias)

            medicine_name = string_utils.xstr(prescript_block[0])
            location=string_utils.xstr(prescript_block[1])
            if system_setting.field('列印藥品存放位置') != 'Y':
                location = ''

            total_dosage=string_utils.xstr(prescript_block[4])
            if (system_setting.field('列印藥品總量') != 'Y' or
                    medicine_name in ['優待'] or
                    not print_total_dosage):
                total_dosage = ''

            prescript_line += '''
                <td align="left" width="{medicine_name_width}%">{medicine_name} {location}</td>
                <td align="right" width="{dosage_width}%">{dosage}{unit}</td>
                <td align="right" width="{total_dosage_width}%">{total_dosage}</td>
                <td width="{separator_width}%">{separator}</td> 
            '''.format(
                medicine_name=medicine_name,
                location=location,
                dosage=string_utils.xstr(prescript_block[2]),
                unit=string_utils.xstr(prescript_block[3]),
                total_dosage=total_dosage,
                separator=string_utils.xstr(separator),
                medicine_name_width=block_width[blocks]['medicine_name_width'],
                dosage_width=block_width[blocks]['dosage_width'],
                total_dosage_width=block_width[blocks]['total_dosage_width'],
                separator_width=block_width[blocks]['separator_width'],
            )

        prescript += '''
            <tr>
              {prescript_line}
            </tr>
        '''.format(
            prescript_line=prescript_line
        )

    return prescript


def get_prescript_html2(database, system_setting, case_key, medicine_set,
                       print_type, print_alias, print_total_dosage, blocks, instruction=None):
    if medicine_set is None:
        prescript = '''
            <tr>
              <td>無處方</td>
            </tr>
            <hr>
        '''
        return prescript

    pres_days = case_utils.get_pres_days(database, case_key, medicine_set)

    sql = '''
        SELECT Treatment FROM cases
        WHERE
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    treatment = rows[0]['Treatment']

    treat_condition = ''
    if print_type == '費用收據' and system_setting.field('列印穴道處置') == 'N' and medicine_set == 1:  # 健保才過濾
        treat_condition = ' AND (prescript.MedicineType NOT IN ("穴道")) '

    sql = '''
        SELECT prescript.*, medicine.Location, medicine.MedicineAlias FROM prescript 
            LEFT JOIN medicine ON medicine.MedicineKey = prescript.MedicineKey
        WHERE 
            CaseKey = {case_key} AND
            MedicineSet = {medicine_set} AND
            (prescript.MedicineName IS NOT NULL AND LENGTH(prescript.MedicineName) > 0)
            {treat_condition}
            {instruction_condition}
        ORDER BY PrescriptNo, PrescriptKey
    '''.format(
        case_key=case_key,
        medicine_set=medicine_set,
        treat_condition=treat_condition,
        instruction_condition=get_instruction_condition(case_key, medicine_set, instruction),
    )

    rows = database.select_record(sql)
    if medicine_set == 1 and treatment in nhi_utils.INS_TREAT and instruction != '健保另包':
        if treatment in nhi_utils.ACUPUNCTURE_TREAT:
            medicine_type = '穴道'
        else:
            medicine_type = '處置'

        rows.insert(
            0,
            {
                'MedicineName': treatment,
                'MedicineAlias': treatment,
                'MedicineType': medicine_type,
                'Dosage': 1,
                'Unit': '次',
                'Location': ''
            }
        )

    if len(rows) <= 0:
        return '<br><br><br><br><br><br><br>'

    if pres_days is None or pres_days <= 0:
        pres_days = 1

    block_width = {
        3: {'medicine_name_width': 35,
            'total_dosage_width': 14,
            'separator_width': 1},
        2: {'medicine_name_width': 35,
            'total_dosage_width': 14,
            'separator_width': 1},
    }

    prescript = ''
    row_count = int((len(rows)-1) / blocks) + 1
    for row_no in range(1, row_count+1):
        separator = ''
        prescript_line = ''
        for i in range(blocks):
            prescript_block = get_medicine_detail(
                medicine_set,
                rows, (row_no-1)*blocks + i, pres_days, print_alias)

            medicine_name = string_utils.xstr(prescript_block[0])
            location=string_utils.xstr(prescript_block[1])
            if system_setting.field('列印藥品存放位置') != 'Y':
                location = ''

            total_dosage=string_utils.xstr(prescript_block[4])

            prescript_line += '''
                <td align="left" width="{medicine_name_width}%">{medicine_name} {location}</td>
                <td align="right" width="{total_dosage_width}%">{total_dosage}{unit}</td>
                <td width="{separator_width}%">{separator}</td> 
            '''.format(
                medicine_name=medicine_name,
                location=location,
                dosage=string_utils.xstr(prescript_block[2]),
                unit=string_utils.xstr(prescript_block[3]),
                total_dosage=total_dosage,
                separator=string_utils.xstr(separator),
                medicine_name_width=block_width[blocks]['medicine_name_width'],
                total_dosage_width=block_width[blocks]['total_dosage_width'],
                separator_width=block_width[blocks]['separator_width'],
            )

        prescript += '''
            <tr>
              {prescript_line}
            </tr>
        '''.format(
            prescript_line=prescript_line
        )

    lines = int(len(rows) / 2)
    if len(rows) % 2 > 0:
        lines += 1

    br_lines = 6 - lines
    if br_lines > 0:
        prescript += '<br>' * br_lines

    return prescript


# 明醫
def get_prescript_block3_html(
        database, system_setting, case_key, medicine_set, print_type,
        print_alias, print_total_dosage, blocks=3, instruction=None):
    if medicine_set is None:
        prescript = '''
            <tr>
              <td>無處方</td>
            </tr>
            <hr>
        '''
        return prescript

    pres_days = case_utils.get_pres_days(database, case_key, medicine_set)

    sql = '''
        SELECT Treatment FROM cases
        WHERE
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    treatment = rows[0]['Treatment']

    treat_condition = ''
    if print_type == '費用收據' and system_setting.field('列印穴道處置') == 'N':
        treat_condition = ' AND (prescript.MedicineType NOT IN ("穴道")) '

    sql = '''
        SELECT prescript.*, medicine.Location, medicine.MedicineAlias FROM prescript 
            LEFT JOIN medicine ON medicine.MedicineKey = prescript.MedicineKey
        WHERE 
            CaseKey = {case_key} AND
            MedicineSet = {medicine_set} AND
            (prescript.MedicineName IS NOT NULL AND LENGTH(prescript.MedicineName) > 0)
            {treat_condition}
            {instruction_condition}
        ORDER BY PrescriptNo, PrescriptKey
    '''.format(
        case_key=case_key,
        medicine_set=medicine_set,
        treat_condition=treat_condition,
        instruction_condition=get_instruction_condition(case_key, medicine_set, instruction),
    )

    rows = database.select_record(sql)
    if medicine_set == 1 and treatment in nhi_utils.INS_TREAT and instruction != '健保另包':
        if treatment in nhi_utils.ACUPUNCTURE_TREAT:
            medicine_type = '穴道'
        else:
            medicine_type = '處置'

        rows.insert(
            0,
            {
                'MedicineName': treatment,
                'MedicineAlias': treatment,
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

    block_width = {
        3: {'medicine_name_width': 20,
            'dosage_width': 7,
            'total_dosage_width': 5,
            'separator_width': 1},
        2: {'medicine_name_width': 30,
            'dosage_width': 10,
            'total_dosage_width': 8,
            'separator_width': 1},
    }

    prescript = ''
    row_count = int((len(rows)-1) / blocks) + 1
    for row_no in range(1, row_count+1):
        separator = ''
        prescript_line = ''
        for i in range(blocks):
            prescript_block = get_medicine_detail(
                medicine_set,
                rows, (row_no-1)*blocks + i, pres_days, print_alias)

            location=string_utils.xstr(prescript_block[1])
            if system_setting.field('列印藥品存放位置') != 'Y':
                location = ''

            total_dosage=string_utils.xstr(prescript_block[4])
            if system_setting.field('列印藥品總量') != 'Y' or not print_total_dosage:
                total_dosage = ''

            medicine_name = string_utils.xstr(prescript_block[0])[:10]
            prescript_line += '''
                <td align="left" width="{medicine_name_width}%"><b>{medicine_name} {location}</b></td>
                <td align="right" width="{dosage_width}%"><b>{dosage}{unit}</b></td>
                <td align="right" width="{total_dosage_width}%">{total_dosage}</td>
                <td width="{separator_width}%">{separator}</td> 
            '''.format(
                medicine_name=medicine_name,
                location=location,
                dosage=string_utils.xstr(prescript_block[2]),
                unit=string_utils.xstr(prescript_block[3]),
                total_dosage=total_dosage,
                separator=string_utils.xstr(separator),
                medicine_name_width=block_width[blocks]['medicine_name_width'],
                dosage_width=block_width[blocks]['dosage_width'],
                total_dosage_width=block_width[blocks]['total_dosage_width'],
                separator_width=block_width[blocks]['separator_width'],
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
          <td>欠卡費:{deposit_fee}</td>
          <td>健保實收:{total_fee}</td>
        </tr> 
        <tr>
          <td>診察費:{diag_fee}</td>
          <td>藥費:{drug_fee}</td>
          <td>調劑費:{pharmacy_fee}</td>
          <td>處置費:{treat_fee}</td>
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
        WHERE 
            CaseKey = {0}
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]
    regist_fee = number_utils.get_integer(row['RegistFee'])
    ins_type = string_utils.xstr(row['InsType'])
    if ins_type == '健保':
        regist_fee = 0

    html = '''
        <tr>
          <td>自費掛號費:{regist_fee}</td>
          <td>自費診察費:{diag_fee}</td>
          <td>一般藥費:{drug_fee}</td>
          <td>水煎藥費:{herb_fee}</td>
          <td>高貴藥費:{expensive_fee}</td>
        </tr>
        <tr>  
          <td>針灸治療費:{acupuncture_fee}</td>
          <td>傷科處置費:{massage_fee}</td>
          <td>自費材料費:{material_fee}</td>
        </tr>
        <tr>  
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


# 自費費用
def get_fees_html(database, case_key):
    sql = '''
        SELECT * FROM cases 
        WHERE 
            CaseKey = {0}
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]
    ins_receipt_fee = (number_utils.get_integer(row['RegistFee']) +
                       number_utils.get_integer(row['SDiagShareFee']) +
                       number_utils.get_integer(row['SDrugShareFee']) +
                       number_utils.get_integer(row['DepositFee']))
    html = '''
        <tr>
          <td>掛號費:{regist_fee}</td>
          <td>門診負擔:{diag_share_fee}</td>
          <td>藥品負擔:{drug_share_fee}</td>
          <td>欠卡費:{deposit_fee}</td>
          <td>健保實收:{ins_receipt_fee}</td>
        </tr> 
        <tr>
          <td>診察費:{diag_fee}</td>
          <td>藥費:{drug_fee}</td>
          <td>調劑費:{pharmacy_fee}</td>
          <td>處置費:{treat_fee}</td>
          <td>健保申請:{ins_apply_fee}</td>
        </tr> 
        <tr>
          <td>自費診察費:{s_diag_fee}</td>
          <td>一般藥費:{s_drug_fee}</td>
          <td>水煎藥費:{herb_fee}</td>
          <td>高貴藥費:{expensive_fee}</td>
          <td>自費材料費:{material_fee}</td>
        </tr>
        <tr>  
          <td>自費針灸費:{acupuncture_fee}</td>
          <td>傷科處置費:{massage_fee}</td>
        </tr>
        <tr>  
          <td>合計金額:{self_total_fee}</td>
          <td>折扣金額:{discount_fee}</td>
          <td>自費應收:{total_fee}</td>
          <td>自費實收:{receipt_fee}</td>
          <td>合計實收:{total_receipt_fee}</td>
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
        ins_receipt_fee=string_utils.xstr(ins_receipt_fee),
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
        s_diag_fee=string_utils.xstr(number_utils.get_integer(row['SDiagFee'])),
        s_drug_fee=string_utils.xstr(number_utils.get_integer(row['SDrugFee'])),
        herb_fee=string_utils.xstr(number_utils.get_integer(row['SHerbFee'])),
        expensive_fee=string_utils.xstr(number_utils.get_integer(row['SExpensiveFee'])),
        material_fee=string_utils.xstr(number_utils.get_integer(row['SMaterialFee'])),

        acupuncture_fee=string_utils.xstr(number_utils.get_integer(row['SAcupunctureFee'])),
        massage_fee=string_utils.xstr(number_utils.get_integer(row['SMassageFee'])),
        self_total_fee=string_utils.xstr(number_utils.get_integer(row['SelfTotalFee'])),
        discount_fee=string_utils.xstr(number_utils.get_integer(row['DiscountFee'])),
        total_fee=string_utils.xstr(number_utils.get_integer(row['TotalFee'])),
        receipt_fee=string_utils.xstr(number_utils.get_integer(row['ReceiptFee'])),
        total_receipt_fee=string_utils.xstr(
            ins_receipt_fee + number_utils.get_integer(row['ReceiptFee'])
        ),
    )

    return html


def get_medicine_detail(medicine_set, rows, row_no, pres_days, print_alias=False):
    try:
        medicine_name = rows[row_no]['MedicineName']
        medicine_ailas = string_utils.xstr(rows[row_no]['MedicineAlias'])
        if print_alias and medicine_ailas != '':
            medicine_name = medicine_ailas

        medicine_type = rows[row_no]['MedicineType']
        unit = rows[row_no]['Unit']
        location = rows[row_no]['Location']
    except (IndexError, TypeError):
        medicine_name, medicine_type, unit, location = '', '', '', ''

    try:
        if medicine_set == 1 and medicine_type in ['穴道', '處置', '檢驗']:
            dosage, unit, total_dosage = '', '', ''
        else:
            dosage = rows[row_no]['Dosage']
            total_dosage = dosage * pres_days

            dosage = format(dosage, '.1f')
            total_dosage = format(total_dosage, '.1f')
    except (IndexError, TypeError):
        dosage, total_dosage = '', ''  # ascii 0->null 填補

    return medicine_name, location, dosage, unit, total_dosage


def get_instruction_html(database, system_settings, case_key, medicine_set):
    sql = '''
        SELECT * FROM cases 
        WHERE 
            CaseKey = {0}
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]

    if medicine_set is None:
        html = '''
              醫師: {doctor}
        '''.format(
            doctor=string_utils.xstr(row['Doctor']),
        )
        return html

    pres_days = case_utils.get_pres_days(database, case_key, medicine_set)
    packages = case_utils.get_packages(database, case_key, medicine_set)
    instruction = case_utils.get_instruction(database, case_key, medicine_set)

    if pres_days > 0:
        _, total_dosage = case_utils.get_prescript_html_data(
            database, system_settings, case_key, medicine_set
        )
        total_dosage *= pres_days
        total_dosage = '{0:.1f}'.format(total_dosage)

        html = '''
              醫師: {doctor} 調劑者: {doctor} 調劑日: {case_date} 指示: 一日{package}包, 共{pres_days}日份 {instruction}服用 總量: {total_dosage}
        '''.format(
            doctor=string_utils.xstr(row['Doctor']),
            case_date=row['CaseDate'].date(),
            package=string_utils.xstr(packages),
            pres_days=string_utils.xstr(pres_days),
            instruction=instruction,
            total_dosage=total_dosage,
        )
    else:
        html = '''
              主治醫師: {doctor}
        '''.format(
            doctor=string_utils.xstr(row['Doctor']),
        )

    return html


def get_instruction_html2(database, system_settings, case_key, medicine_set, additional=None):
    sql = '''
        SELECT * FROM cases 
        WHERE 
            CaseKey = {0}
    '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]

    if medicine_set is None:
        html = '''
              醫師: {doctor}
        '''.format(
            doctor=string_utils.xstr(row['Doctor']),
        )
        return html

    pres_days = case_utils.get_pres_days(database, case_key, medicine_set)
    packages = case_utils.get_packages(database, case_key, medicine_set)
    instruction = case_utils.get_instruction(database, case_key, medicine_set)
    additional_label = ''
    if additional is not None:
        additional_label = '<b>「{0}」</b>'.format(additional)

    if pres_days > 0:
        _, total_dosage = case_utils.get_prescript_html_data(
            database, system_settings, case_key, medicine_set
        )
        total_dosage *= pres_days
        total_dosage = '{0:.1f}'.format(total_dosage)

        html = '''
              藥日: {package}包 * {pres_days}天 {instruction} 總量: {total_dosage} {additional_label}<br>
              醫師: {doctor} 調劑者: {doctor} 調劑日: {case_date}<br>
        '''.format(
            doctor=string_utils.xstr(row['Doctor']),
            package=string_utils.xstr(packages),
            pres_days=string_utils.xstr(pres_days),
            instruction=instruction,
            total_dosage=total_dosage,
            case_date=row['CaseDate'].date(),
            additional_label=additional_label,
        )
    else:
        html = '''
              主治醫師: {doctor}<br>
        '''.format(
            doctor=string_utils.xstr(row['Doctor']),
        )

    return html


# 取得列印健保或自費處方dialog
def get_medicine_set_items(database, case_key, form_type, print_type='選擇列印'):
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
    medicine_set_count = len(rows)

    try:
        medicine_set = rows[0]['MedicineSet']
    except IndexError:
        medicine_set = None

    items = ['全部{0}'.format(form_type)]
    if ins_type == '健保' and medicine_set != 1:
        if medicine_set_count == 0:
            medicine_set_count = 1
            medicine_set = 1
        else:
            medicine_set_count += 1
            items.append('健保{0}'.format(form_type))

    if medicine_set_count <= 0:
        return '{0}{1}'.format(ins_type, form_type), None
    elif medicine_set_count == 1:
        if medicine_set == 1:
            item = '健保{0}'.format(form_type)
        else:
            item = '自費{0}'.format(form_type)

        return item, medicine_set

    for row in rows:
        medicine_set = row['MedicineSet']
        if medicine_set == 1:
            items.append('健保{0}'.format(form_type))
        else:
            items.append('自費{0}{1}'.format(form_type, medicine_set-1))

    if print_type == '選擇列印':
        input_dialog = dialog_utils.get_dialog(
            '多重{0}'.format(form_type), '請選擇欲列印的{0}'.format(form_type),
            None, QInputDialog.TextInput, 320, 200)
        input_dialog.setComboBoxItems(items)
        ok = input_dialog.exec_()

        if not ok:
            return False, None

        item = input_dialog.textValue()
    else:
        item = '全部{0}'.format(form_type)

    if item == '全部{0}'.format(form_type):
        del items[0]
        return item, items
    elif item == '健保{0}'.format(form_type):
        medicine_set = 1
    else:
        medicine_set = number_utils.get_integer(item.split('自費{0}'.format(form_type))[1]) + 1
        item = '自費{0}'.format(form_type)

    return item, medicine_set


# 取得列印健保或自費收據dialog
def get_receipt_items(database, case_key, print_type='選擇列印'):
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

    if print_type == '選擇列印':
        input_dialog = dialog_utils.get_dialog(
            '多重醫療收據', '請選擇欲列印的醫療收據',
            None, QInputDialog.TextInput, 320, 200)
        input_dialog.setComboBoxItems(items)
        ok = input_dialog.exec_()

        if not ok:
            return None

        item = input_dialog.textValue()
    else:
        item = '全部醫療收據'

    if item == '全部醫療收據':
        del items[0]
        return items
    else:
        return item


# 列印門診掛號單
def print_registration(parent, database, system_settings, case_key,
                       print_type, print_option='系統設定'):
    printable = system_settings.field('列印門診掛號單')

    if print_option != '系統設定' and printable == '不印':
        printable = '列印'

    if printable == '不印':
        return
    elif system_settings.field('列印門診掛號單') == '詢問':
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
        print_registration_form.print(print_option)
    else:
        print_registration_form.preview(print_option)

    del print_registration_form


# 列印健保處方箋
def print_ins_prescript(parent, database, system_settings, case_key,
                        print_type, print_option='系統設定'):
    printable = system_settings.field('列印健保處方箋')
    if print_option != '系統設定' and printable == '不印':
        printable = '列印'

    prescript_count = get_prescript_count(database, case_key, medicine_set=1)

    if printable == '不印':
        return
    elif printable == '藥品' and prescript_count <= 0:
        return
    elif printable == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif printable == '預覽':
        print_type = 'preview'

    form = system_settings.field('健保處方箋格式')
    if form not in list(PRINT_PRESCRIPTION_INS_FORM.keys()):
        return

    print_prescription_form = PRINT_PRESCRIPTION_INS_FORM[form](
        parent, database, system_settings, case_key)

    if print_type == 'print':
        print_prescription_form.print()
        print_prescription_form.print('健保另包')
    else:
        print_prescription_form.preview()
        print_prescription_form.preview('健保另包')

    del print_prescription_form


# 列印自費處方箋
def print_self_prescript(parent, database, system_settings, case_key, medicine_set,
                         print_type, print_option='系統設定'):
    printable = system_settings.field('列印自費處方箋')
    if print_option != '系統設定' and printable == '不印':
        printable = '列印'

    prescript_count = get_prescript_count(database, case_key, medicine_set)

    if printable == '不印':
        return
    elif printable == '藥品' and prescript_count <= 0:
        return
    elif printable == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif printable == '預覽':
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
def print_ins_receipt(parent, database, system_settings, case_key,
                      print_type, print_option='系統設定'):
    printable = system_settings.field('列印健保醫療收據')
    if print_option != '系統設定' and printable == '不印':
        printable = '列印'

    if printable == '不印':
        return
    elif printable == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif printable == '預覽':
        print_type = 'preview'

    form = system_settings.field('健保醫療收據格式')
    if form not in list(PRINT_RECEIPT_INS_FORM.keys()):
        return

    print_receipt_form = PRINT_RECEIPT_INS_FORM[form](
        parent, database, system_settings, case_key)

    if print_type == 'print':
        print_receipt_form.print()
        print_receipt_form.print('健保另包')
    else:
        print_receipt_form.preview()
        print_receipt_form.preview('健保另包')

    del print_receipt_form


def get_additional_label(additional):
    additional_label = ''
    if additional is not None:
        additional_label = '<br><b>「{0}」</b>'.format(additional)

    return additional_label


# 列印自費醫療收據
def print_self_receipt(parent, database, system_settings, case_key, medicine_set,
                       print_type, print_option='系統設定'):
    printable = system_settings.field('列印自費醫療收據')

    if print_option != '系統設定' and printable == '不印':
        printable = '列印'

    if printable == '不印':
        return
    elif printable == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif printable == '預覽':
        print_type = 'preview'

    form = system_settings.field('自費醫療收據格式')
    if form not in list(PRINT_RECEIPT_SELF_FORM.keys()):
        return

    print_receipt_form = PRINT_RECEIPT_SELF_FORM[form](
        parent, database, system_settings, case_key, medicine_set)

    if print_type == 'print':
        print_receipt_form.print()
    else:
        print_receipt_form.preview()

    del print_receipt_form


# 列印其他收據
def print_misc(parent, database, system_settings, case_key,
               print_type, print_option='系統設定'):
    printable = system_settings.field('列印其他收據')
    if print_option != '系統設定' and printable == '不印':
        printable = '列印'

    if printable == '不印':
        return
    elif printable == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif printable == '預覽':
        print_type = 'preview'

    form = system_settings.field('其他收據格式')
    if form not in list(PRINT_MISC_FORM.keys()):
        return

    print_misc_form = PRINT_MISC_FORM[form](
        parent, database, system_settings, case_key)

    if print_type == 'print':
        print_misc_form.print()
    else:
        print_misc_form.preview()

    del print_misc_form


# 列印預約單
def print_reservation(parent, database, system_settings, reservation_key,
                      print_type, print_option='系統設定'):
    printable = system_settings.field('列印預約掛號單')
    if print_option != '系統設定' and printable == '不印':
        printable = '列印'

    if printable == '不印':
        return
    elif printable == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif printable == '預覽':
        print_type = 'preview'

    form = system_settings.field('預約掛號單格式')
    if form not in list(PRINT_RESERVATION_FORM.keys()):
        return

    print_reservation_form = PRINT_RESERVATION_FORM[form](
        parent, database, system_settings, reservation_key)

    if print_type == 'print':
        print_reservation_form.print()
    else:
        print_reservation_form.preview()

    del print_reservation_form


# 列印申請總表
def print_ins_apply_total_fee(parent, database, system_settings, ins_total_fee):
    print_type = 'print'

    if system_settings.field('列印報表') == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif system_settings.field('列印報表') == '預覽':
        print_type = 'preview'

    print_total_fee = PrintInsApplyTotalFee(
        parent, database, system_settings,
        ins_total_fee
    )

    if print_type == 'print':
        print_total_fee.print()
    else:
        print_total_fee.preview()

    del print_total_fee


# 列印html
def print_html(parent, database, system_settings, html, orientation):
    print_type = 'print'

    if system_settings.field('列印報表') == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif system_settings.field('列印報表') == '預覽':
        print_type = 'preview'

    print_html_form = PrintHtml(
        parent, database, system_settings, html, orientation
    )

    if print_type == 'print':
        print_html_form.print()
    else:
        print_html_form.preview()

    del print_html_form


# 列印申請總表
def print_ins_apply_schedule_table(parent, database, system_settings, html):
    print_type = 'print'

    if system_settings.field('列印報表') == '詢問':
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Rejected:
            return
    elif system_settings.field('列印報表') == '預覽':
        print_type = 'preview'

    print_schedule_table = PrintInsApplyScheduleTable(
        parent, database, system_settings, html
    )

    if print_type == 'print':
        print_schedule_table.print()
    else:
        print_schedule_table.preview()

    del print_schedule_table


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


# 列印實體病歷
def print_medical_records(parent, database, system_settings,
                          patient_key, sql, start_date, end_date, print_type=None):
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
        patient_key, sql, start_date, end_date,
    )

    if print_type == 'print':
        print_cases.print()
    elif print_type == 'preview':
        print_cases.preview()
    elif print_type == 'pdf':
        print_cases.save_to_pdf()
    elif print_type == 'pdf_by_dialog':
        print_cases.save_to_pdf_by_dialog()

    del print_cases


# 列印收費明細
def print_medical_fees(parent, database, system_settings,
                       patient_key, sql, print_type=None):
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

    print_fees = PrintMedicalFees(
        parent, database, system_settings,
        patient_key, sql,
    )

    if print_type == 'print':
        print_fees.print()
    elif print_type == 'preview':
        print_fees.preview()
    elif print_type == 'pdf':
        print_fees.save_to_pdf()
    elif print_type == 'pdf_by_dialog':
        print_fees.save_to_pdf_by_dialog()

    del print_fees


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


# 列印診斷證明書
def print_certificate_diagnosis(parent, database, system_settings, certificate_key, print_type=None):
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

    print_certificate = PrintCertificateDiagnosis(
        parent, database, system_settings,
        certificate_key,
    )

    if print_type == 'print':
        print_certificate.print()
    elif print_type == 'preview':
        print_certificate.preview()
    elif print_type == 'pdf':
        print_certificate.save_to_pdf()

    del print_certificate


# 列印醫療費用證明書明細
def print_certificate_payment(parent, database, system_settings, certificate_key, print_type=None):
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

    print_cert_payment = PrintCertificatePayment(
        parent, database, system_settings,
        certificate_key,
    )

    if print_type == 'print':
        print_cert_payment.print()
    elif print_type == 'preview':
        print_cert_payment.preview()
    elif print_type == 'pdf':
        print_cert_payment.save_to_pdf()

    del print_cert_payment


# 列印醫療費用證明書總表
def print_certificate_total(parent, database, system_settings, certificate_key, print_type=None):
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

    print_cert_total = PrintCertificatePaymentTotal(
        parent, database, system_settings,
        certificate_key,
    )

    if print_type == 'print':
        print_cert_total.print()
    elif print_type == 'preview':
        print_cert_total.preview()
    elif print_type == 'pdf':
        print_cert_total.save_to_pdf()

    del print_cert_total


# 列印醫療費用證明書處方明細
def print_certificate_prescript(parent, database, system_settings, certificate_key, print_type=None):
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

    print_cert_prescript = PrintCertificatePaymentPrescript(
        parent, database, system_settings,
        certificate_key,
    )

    if print_type == 'print':
        print_cert_prescript.print()
    elif print_type == 'preview':
        print_cert_prescript.preview()
    elif print_type == 'pdf':
        print_cert_prescript.save_to_pdf()

    del print_cert_prescript


def get_prescript_count(database, case_key, medicine_set):
    if medicine_set == 1:
        medicine_type_script = ' AND MedicineType NOT IN ("穴道", "處置", "檢驗") '
    else:
        medicine_type_script = ''

    sql = '''
        SELECT PrescriptKey FROM prescript
        WHERE
            CaseKey = {case_key} AND
            MedicineSet = {medicine_set}
            {medicine_type_script}
            
    '''.format(
        case_key=case_key,
        medicine_set=medicine_set,
        medicine_type_script=medicine_type_script,
    )

    try:
        rows = database.select_record(sql)
        prescript_count = len(rows)
    except:
        prescript_count = 0

    return prescript_count
