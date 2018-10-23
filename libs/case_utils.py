import xml.etree.ElementTree as ET
from xml.dom.minidom import Document
from libs import string_utils
from libs import number_utils
from libs import nhi_utils


MAX_MEDICINE_SET = 100


def get_security_xml_dict(root):
    security_xml_dict = {
        '寫卡時間': root[0].text,
        '健保卡序': root[1].text,
        '院所代號': root[2].text,
        '安全簽章': root[3].text,
        '安全模組': root[4].text,
        '同日就診': root[5].text,
        '上傳時間': root[6].text,
        '資料格式': root[7].text,
        '補卡註記': root[8].text,
        '醫令時間': root[9].text,
    }

    return security_xml_dict


def get_treat_data_xml_dict(root=None):
    security_xml_dict = {
        'registered_date': string_utils.xstr(root[0].text),
        'seq_number': string_utils.xstr(root[1].text),
        'clinic_id': string_utils.xstr(root[2].text),
        'security_signature': string_utils.xstr(root[3].text),
        'sam_id': string_utils.xstr(root[4].text),
        'register_duplicated': string_utils.xstr(root[5].text),
        'upload_time': string_utils.xstr(root[6].text),
        'upload_type': string_utils.xstr(root[7].text),
        'treat_after_check': string_utils.xstr(root[8].text),
        'prescript_sign_time': string_utils.xstr(root[9].text),
    }

    return security_xml_dict


def create_treat_data_xml_dict():
    security_xml_dict = {
        'registered_date': '',
        'seq_number': '',
        'clinic_id': '',
        'security_signature': '',
        'sam_id': '',
        'register_duplicated': '',
        'upload_time': '',
        'upload_type': '',
        'treat_after_check': '',
        'prescript_sign_time': '',
    }

    return security_xml_dict


# 產生xml檔
# treat_after_check: '1'-正常 '2'-補卡
def create_security_xml(treat_data=None):
    if treat_data is None:
        treat_data = create_treat_data_xml_dict()

    doc = Document()
    document = doc.createElement('DOCUMENT')
    document.setAttribute('content', 'cshis')

    doc.appendChild(document)
    security = doc.createElement('treat_data')
    document.appendChild(security)

    registered_date = doc.createElement('registered_date')
    registered_date_value = doc.createTextNode(
        treat_data['registered_date']
    )
    registered_date.appendChild(registered_date_value)
    security.appendChild(registered_date)

    seq_number = doc.createElement('seq_number')
    seq_number_value = doc.createTextNode(
        treat_data['seq_number']
    )
    seq_number.appendChild(seq_number_value)
    security.appendChild(seq_number)

    clinic_id = doc.createElement('clinic_id')
    clinic_id_value = doc.createTextNode(
        treat_data['clinic_id']
    )
    clinic_id.appendChild(clinic_id_value)
    security.appendChild(clinic_id)

    security_signature = doc.createElement('security_signature')
    security_signature_value = doc.createTextNode(
        treat_data['security_signature']
    )
    security_signature.appendChild(security_signature_value)
    security.appendChild(security_signature)

    sam_id = doc.createElement('sam_id')
    sam_id_value = doc.createTextNode(
        treat_data['sam_id']
    )
    sam_id.appendChild(sam_id_value)
    security.appendChild(sam_id)

    register_duplicated = doc.createElement('register_duplicated')
    register_duplicated_value = doc.createTextNode(
        treat_data['register_duplicated']
    )
    register_duplicated.appendChild(register_duplicated_value)
    security.appendChild(register_duplicated)

    upload_time = doc.createElement('upload_time')
    upload_time_value = doc.createTextNode(
        treat_data['upload_time']
    )
    upload_time.appendChild(upload_time_value)
    security.appendChild(upload_time)

    upload_type = doc.createElement('upload_type')
    upload_type_value = doc.createTextNode(
        treat_data['upload_type']
    )
    upload_type.appendChild(upload_type_value)
    security.appendChild(upload_type)

    treat_after_check = doc.createElement('treat_after_check')
    treat_after_check_value = doc.createTextNode(
        treat_data['treat_after_check']
    )
    treat_after_check.appendChild(treat_after_check_value)
    security.appendChild(treat_after_check)

    prescript_sign_time = doc.createElement('prescript_sign_time')
    prescript_sign_time_value = doc.createTextNode(
        treat_data['prescript_sign_time']
    )
    prescript_sign_time.appendChild(prescript_sign_time_value)
    security.appendChild(prescript_sign_time)

    return doc


# 取出病歷檔安全簽章XML
def extract_security_xml(xml_field, field):
    ic_card_xml = ''.join(string_utils.get_str(xml_field, 'utf-8'))
    try:
        root = ET.fromstring(ic_card_xml)[0]
    except ET.ParseError:
        return ''

    security_xml_dict = get_security_xml_dict(root)

    return security_xml_dict[field]


# 寫入病歷檔安全簽章XML
def update_xml_doc(database, xml_field, field_name, field_value):
    sql = """ 
        SELECT UPDATEXML('{0}', '{1}', '{2}')
    """.format(
        xml_field,
        '//{0}'.format(field_name),
        '<{0}>{1}</{0}>'.format(field_name, field_value)
    )
    row = database.select_record(sql, False)[0]

    return row[0]


# 寫入病歷檔安全簽章XML
def update_xml(database, table_name, field_name, xml_field, field_value, primary_key, key_value):
    sql = """ 
        UPDATE {0} SET {1} = UPDATEXML({1}, '{2}', '{3}') WHERE {4} = {5}
    """.format(
        table_name,
        field_name,
        '//{0}'.format(xml_field),
        '<{0}>{1}</{0}>'.format(xml_field, field_value),
        primary_key,
        key_value
    )
    database.exec_sql(sql)


def extract_xml(database, case_key, xml_field):
    sql = '''
            SELECT ExtractValue(Security, "//{0}") AS XMLValue
            FROM cases WHERE
                CaseKey = {1}
        '''.format(xml_field, case_key)
    row = database.select_record(sql)[0]
    xml_value =string_utils.get_str(row['XMLValue'], 'utf-8')  # 1-正常上傳 2-異常上傳 3-正常補正 4-異常補正

    return xml_value


'''
# 寫入病歷檔安全簽章XML
def update_xml_doc(xml_field, field_name, field_value):
    ic_card_xml = ''.join(string_utils.get_str(xml_field, 'utf-8'))

    root = ET.fromstring(ic_card_xml)[0]
    treat_data = get_treat_data_xml_dict(root)
    treat_data[field_name] = field_value
    doc = create_security_xml(treat_data)

    return doc.toprettyxml(indent='\t')
'''


def get_pres_days(database, case_key, medicine_set=1):
    sql = '''
        SELECT Days FROM dosage WHERE 
            CaseKey = {0} AND
            MedicineSet = {1}
    '''.format(case_key, medicine_set)
    rows = database.select_record(sql)

    if len(rows) > 0:
        pres_days = number_utils.get_integer(rows[0]['Days'])
    else:
        pres_days = 0

    return pres_days

def get_packages(database, case_key, medicine_set=1):
    sql = '''
        SELECT Packages FROM dosage WHERE 
            CaseKey = {0} AND
            MedicineSet = {1} 
    '''.format(case_key, medicine_set)
    rows = database.select_record(sql)

    if len(rows) > 0:
        package = number_utils.get_integer(rows[0]['Packages'])
    else:
        package = 0

    return package

def get_instruction(database, case_key, medicine_set=1):
    sql = '''
        SELECT Instruction FROM dosage WHERE 
            CaseKey = {0} AND
            MedicineSet = {1} 
    '''.format(case_key, medicine_set)
    rows = database.select_record(sql)

    if len(rows) > 0:
        instruction = string_utils.xstr(rows[0]['Instruction'])
    else:
        instruction = None

    return instruction


# 取得病歷html格式
def get_medical_record_html(database, case_key):
    sql = '''
        SELECT * FROM cases 
        WHERE
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return

    row = rows[0]
    if row['InsType'] == '健保':
        card = str(row['Card'])
        if number_utils.get_integer(row['Continuance']) >= 1:
            card += '-' + str(row['Continuance'])
        card = '<b>健保</b>: {0}'.format(card)
    else:
        card = '<b>自費</b>'

    medical_record = '<b>日期</b>: {0} {1} <b>醫師</b>:{2}<hr>'.format(
        string_utils.xstr(row['CaseDate'].date()),
        card,
        string_utils.xstr(row['Doctor']),
    )

    if row['Symptom'] is not None:
        medical_record += '<b>主訴</b>: {0}<hr>'.format(string_utils.get_str(row['Symptom'], 'utf8'))
    if row['Tongue'] is not None:
        medical_record += '<b>舌診</b>: {0}<hr>'.format(string_utils.get_str(row['Tongue'], 'utf8'))
    if row['Pulse'] is not None:
        medical_record += '<b>脈象</b>: {0}<hr>'.format(string_utils.get_str(row['Pulse'], 'utf8'))
    if row['Remark'] is not None:
        medical_record += '<b>備註</b>: {0}<hr>'.format(string_utils.get_str(row['Remark'], 'utf8'))
    if row['DiseaseCode1'] is not None and len(str(row['DiseaseCode1']).strip()) > 0:
        medical_record += '<b>主診斷</b>: {0} {1}<br>'.format(str(row['DiseaseCode1']), str(row['DiseaseName1']))
    if row['DiseaseCode2'] is not None and len(str(row['DiseaseCode2']).strip()) > 0:
        medical_record += '<b>次診斷1</b>: {0} {1}<br>'.format(str(row['DiseaseCode2']), str(row['DiseaseName2']))
    if row['DiseaseCode3'] is not None and len(str(row['DiseaseCode3']).strip()) > 0:
        medical_record += '<b>次診斷2</b>: {0} {1}<br>'.format(str(row['DiseaseCode3']), str(row['DiseaseName3']))

    medical_record = '''
        <div style="width: 95%;">
            {0}
        </div>
    '''.format(medical_record)

    prescript_record = _get_prescript_record(database, case_key)

    html = '''
        <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                {0}
                {1}
            </body>
        </html>
    '''.format(
        medical_record,
        prescript_record,
    )

    return html


def _get_prescript_record(database, case_key):
    sql = '''
        SELECT Treatment FROM cases
        WHERE
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    treatment = rows[0]['Treatment']

    sql = 'SELECT * FROM prescript WHERE CaseKey = {0}'.format(case_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return '<br><center>無處方</center><br>'

    all_prescript = ''
    for i in range(1, MAX_MEDICINE_SET):
        sql = '''
            SELECT * FROM prescript WHERE CaseKey = {0} AND
            MedicineSet = {1}
            ORDER BY PrescriptNo, PrescriptKey
        '''.format(case_key, i)
        rows = database.select_record(sql)
        if i == 1 and treatment in nhi_utils.INS_TREAT:
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
                    'Instruction': '',
                }
            )

        if len(rows) <= 0:
            if i == 1:
                continue
            else:
                break

        prescript_data = ''
        sequence = 0
        total_dosage = 0
        for row in rows:
            if row['MedicineName'] is None:
                continue

            sequence += 1

            if row['Dosage'] is None or row['Dosage'] == 0.00:
                dosage = ''
            else:
                dosage = string_utils.xstr(row['Dosage'])
                total_dosage += row['Dosage']

            unit = string_utils.xstr(row['Unit'])
            instruction = string_utils.xstr(row['Instruction'])

            prescript_data += '''
                <tr>
                    <td align="center" style="padding-right: 8px;">{0}</td>
                    <td style="padding-left: 8px;">{1}</td>
                    <td align="right" style="padding-right: 8px">{2} {3}</td>
                    <td style="padding-left: 8px;">{4}</td>
                </tr>
            '''.format(
                string_utils.xstr(sequence),
                string_utils.xstr(row['MedicineName']),
                dosage,
                unit,
                instruction,
            )

        sql = '''
                SELECT * FROM dosage 
                WHERE
                    CaseKey = {0} AND MedicineSet = {1}
                
            '''.format(case_key, i)
        rows = database.select_record(sql)
        dosage_row = rows[0] if len(rows) > 0 else None
        if dosage_row is not None:
            packages = number_utils.get_integer(dosage_row['Packages'])
            pres_days = number_utils.get_integer(dosage_row['Days'])
            instruction = string_utils.xstr(dosage_row['Instruction'])

            prescript_data += '''
                <tr>
                    <td style="text-align: left; padding-left: 30px;" colspan="4">
                        用法: {0}包 {1}日份 {2}服用 總量: {3}
                    </td>
                </tr>
            '''.format(
                packages, pres_days, instruction, total_dosage
            )

        if i == 1:
            medicine_title = '健保處方'
        else:
            medicine_title = '自費處方{0}'.format(i-1)

        prescript_data = '''
            <table align=center cellpadding="2" cellspacing="0" width="98%" style="border-width: 1px; border-style: solid;">
                <thead>
                    <tr bgcolor="LightGray">
                        <th style="text-align: center; padding-left: 8px" width="10%">序</th>
                        <th style="padding-left: 8px" width="50%" align="left">{0}</th>
                        <th style="padding-right: 8px" align="right" width="25%">劑量</th>
                        <th style="padding-left: 8px" align="left" width="15%">指示</th>
                    </tr>
                </thead>
                <tbody>
                    {1}
                </tbody>
            </table>
            <br>
        '''.format(medicine_title, prescript_data)
        all_prescript += prescript_data

    return all_prescript


def copy_past_medical_record(
        database, widget, case_key, copy_diagnostic, copy_remark, copy_disease, copy_prescript):
    sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return

    row = rows[0]
    ui = widget.ui
    if copy_diagnostic:
        ui.textEdit_symptom.setText(string_utils.get_str(row['Symptom'], 'utf8'))
        ui.textEdit_tongue.setText(string_utils.get_str(row['Tongue'], 'utf8'))
        ui.textEdit_pulse.setText(string_utils.get_str(row['Pulse'], 'utf8'))

    if copy_remark:
        ui.textEdit_remark.setText(string_utils.get_str(row['Remark'], 'utf8'))

    if copy_disease:
        ui.lineEdit_disease_code1.setText(string_utils.get_str(row['DiseaseCode1'], 'utf8'))
        ui.lineEdit_disease_name1.setText(string_utils.get_str(row['DiseaseName1'], 'utf8'))
        ui.lineEdit_disease_code2.setText(string_utils.get_str(row['DiseaseCode2'], 'utf8'))
        ui.lineEdit_disease_name2.setText(string_utils.get_str(row['DiseaseName2'], 'utf8'))
        ui.lineEdit_disease_code3.setText(string_utils.get_str(row['DiseaseCode3'], 'utf8'))
        ui.lineEdit_disease_name3.setText(string_utils.get_str(row['DiseaseName3'], 'utf8'))

    if copy_prescript:
        if widget.tab_list[0] is not None:
            widget.tab_list[0].copy_past_prescript(case_key)
