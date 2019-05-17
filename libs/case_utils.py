from PyQt5 import QtWidgets
from lxml import etree as ET
from libs import string_utils
from libs import number_utils
from libs import prescript_utils


INJURY_LIST = [
    '扭傷', '拉傷', '挫傷', '壓傷', '壓砸傷','鈍傷', '損傷', '擦傷', '脫臼',
    '脫位', '疼痛', '關節炎', '關節痛', '撕裂傷', '骨折', '叮咬', '咬傷', '攣縮',
    '破裂', '壓迫',
]


SECURITY_XML_DICT = {
    '寫卡時間': 'registered_date',
    '健保卡序': 'seq_number',
    '院所代號': 'clinic_id',
    '安全簽章': 'security_signature',
    '安全模組': 'sam_id',
    '同日就診': 'register_duplicated',
    '上傳時間': 'upload_time',
    '資料格式': 'upload_type',
    '補卡註記': 'treat_after_check',
    '醫令時間': 'prescript_sign_time',
}


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

    root = ET.Element('DOCUMENT', content='cshis')
    treat_data_node = ET.SubElement(root, 'treat_data')

    field_list = [
        'registered_date',
        'seq_number',
        'clinic_id',
        'security_signature',
        'sam_id',
        'register_duplicated',
        'upload_time',
        'upload_type',
        'treat_after_check',
        'prescript_sign_time',
    ]

    for field_name in field_list:
        xml_field = ET.SubElement(treat_data_node, field_name)
        xml_field.text = treat_data[field_name]

    xml = ET.tostring(root)

    return xml


def get_treat_data_xml_dict(xml_string):
    ic_card_xml = ''.join(string_utils.get_str(xml_string, 'utf-8'))
    security_xml_dict = create_treat_data_xml_dict()

    root = ET.fromstring(ic_card_xml)
    doc = root.xpath('//DOCUMENT/treat_data')[0]
    for field in doc:
        field_name = field.tag
        field_value = root.xpath('//DOCUMENT/treat_data/{field_name}'.format(
            field_name=field_name))[0].text
        security_xml_dict[field_name] = field_value

    return security_xml_dict


# 取出病歷檔安全簽章XML
def extract_security_xml(xml_field, field):
    ic_card_xml = ''.join(string_utils.get_str(xml_field, 'utf-8'))
    if ic_card_xml in [None, '']:
        return None

    field_name = SECURITY_XML_DICT[field]
    try:
        root = ET.fromstring(ic_card_xml)
        field_value = root.xpath('//DOCUMENT/treat_data/{field_name}'.format(field_name=field_name))[0].text
    except:
        return None

    return field_value


# 寫入病歷檔安全簽章XML
def update_xml_doc(xml_field, field_name, field_value):
    ic_card_xml = ''.join(string_utils.get_str(xml_field, 'utf-8'))

    root = ET.fromstring(ic_card_xml)
    root.xpath('//DOCUMENT/treat_data/{field_name}'.format(
        field_name=field_name, ))[0].text = field_value

    return ET.tostring(root)


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
def get_medical_record_html(database, system_settings, case_key):
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

    prescript_record = get_prescript_record(database, system_settings, case_key)

    html = '''
        <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                {medical_record}
                {prescript_record}
            </body>
        </html>
    '''.format(
        medical_record=medical_record,
        prescript_record=prescript_record,
    )

    return html


def get_prescript_record(database, system_settings, case_key):
    sql = 'SELECT * FROM prescript WHERE CaseKey = {0}'.format(case_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return '<br><br><br><center>無開立處方</center><br>'

    html = get_prescript_medicine_record(database, system_settings, case_key, 1)
    html += get_ins_prescript_treat_record(database, system_settings, case_key)
    html += get_self_prescript_medicine_record(database, system_settings, case_key)

    return html


def get_prescript_html_data(database, system_settings, case_key, medicine_set, treatment=None):
    prescript_data = ''
    total_dosage = 0

    treatment_script = ''
    if medicine_set == 1:  # 健保才過濾處方或處置
        if treatment is None:
            treatment_script = ' AND MedicineTYPE NOT IN ("穴道", "處置", "檢驗") '
        else:
            treatment_script = ' AND MedicineTYPE IN ("穴道", "處置", "檢驗") '

    sql = '''
        SELECT * FROM prescript 
        WHERE 
            CaseKey = {case_key} AND
            MedicineSet = {medicine_set}
            {treatment_script}
        ORDER BY PrescriptNo, PrescriptKey
    '''.format(
        case_key=case_key,
        medicine_set=medicine_set,
        treatment_script=treatment_script
    )
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return prescript_data, total_dosage

    sequence = 0
    for row in rows:
        if string_utils.xstr(row['MedicineName']) == '':
            continue

        sequence += 1

        if row['Dosage'] is None or row['Dosage'] == 0.00:
            dosage = ''
        else:
            if system_settings.field('劑量模式') in ['日劑量', '總量']:
                dosage = '{0:.1f}'.format(row['Dosage'])
            elif system_settings.field('劑量模式') in ['次劑量']:
                dosage = '{0:.2f}'.format(row['Dosage'])
            else:
                dosage = string_utils.xstr(row['Dosage'])

            total_dosage += row['Dosage']

        unit = string_utils.xstr(row['Unit'])
        instruction = string_utils.xstr(row['Instruction'])

        if medicine_set >= 2:
            font_color = 'color: navy'
        else:
            font_color = ''

        prescript_data += '''
            <tr>
                <td align="center" style="padding-right: 8px; {font_color}">{sequence}</td>
                <td style="padding-left: 8px; {font_color}">{medicine_set}</td>
                <td align="right" style="padding-right: 8px; {font_color}">{dosage} {unit}</td>
                <td style="padding-left: 8px; {font_color}">{instruction}</td>
            </tr>
        '''.format(
            font_color=font_color,
            sequence=string_utils.xstr(sequence),
            medicine_set=string_utils.xstr(row['MedicineName']),
            dosage=dosage,
            unit=unit,
            instruction=instruction,
        )

    return prescript_data, total_dosage


def get_dosage_html(database, case_key, medicine_set, total_dosage):
    dosage_data = ''

    sql = '''
        SELECT * FROM dosage 
        WHERE
            CaseKey = {0} AND MedicineSet = {1} 
    '''.format(case_key, medicine_set)
    rows = database.select_record(sql)
    dosage_row = rows[0] if len(rows) > 0 else None
    if dosage_row is not None:
        packages = number_utils.get_integer(dosage_row['Packages'])
        pres_days = number_utils.get_integer(dosage_row['Days'])
        instruction = string_utils.xstr(dosage_row['Instruction'])

        if packages > 0 and pres_days > 0:
            dosage_data = '''
                <tr>
                    <td style="text-align: left; padding-left: 30px;" colspan="4">
                        用法: {0}包 {1}日份 {2}服用 總量: {3}
                    </td>
                </tr>
            '''.format(
                packages, pres_days, instruction, total_dosage
            )

    return dosage_data


def get_prescript_medicine_record(database, system_settings, case_key, medicine_set):
    prescript_data, total_dosage = get_prescript_html_data(database, system_settings, case_key, medicine_set)
    if prescript_data == '':
        return ''

    prescript_data += get_dosage_html(database, case_key, medicine_set, total_dosage)
    if medicine_set == 1:
        prescript_heading = '健保處方'
    else:
        prescript_heading = '自費處方{0}'.format(medicine_set-1)

    prescript_html = '''
        <table align=center cellpadding="2" cellspacing="0" width="98%" style="border-width: 1px; border-style: solid;">
            <thead>
                <tr bgcolor="LightGray">
                    <th style="text-align: center; padding-left: 8px" width="10%">序</th>
                    <th style="padding-left: 8px" width="50%" align="left">{prescript_heading}</th>
                    <th style="padding-right: 8px" align="right" width="25%">劑量</th>
                    <th style="padding-left: 8px" align="left" width="15%">指示</th>
                </tr>
            </thead>
            <tbody>
                {prescript_data}
            </tbody>
        </table>
        <br>
    '''.format(
        prescript_heading=prescript_heading,
        prescript_data=prescript_data,
    )

    return prescript_html


def get_ins_prescript_treat_record(database, system_settings, case_key):
    prescript_html = ''
    sql = '''
        SELECT Treatment FROM cases
        WHERE
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    treatment = string_utils.xstr(rows[0]['Treatment'])

    if treatment == '':
        return prescript_html

    treatment_data = '''
        <tr>
            <td align="center" style="padding-right: 8px;">*</td>
            <td style="padding-left: 8px;">{treatment}</td>
            <td align="right" style="padding-right: 8px">1 次</td>
            <td style="padding-left: 8px;"></td>
        </tr>
    '''.format(
        treatment=treatment,
    )
    prescript_data, _ = get_prescript_html_data(database, system_settings, case_key, 1, True)

    prescript_html = '''
        <table align=center cellpadding="2" cellspacing="0" width="98%" style="border-width: 1px; border-style: solid;">
            <thead>
                <tr bgcolor="LightGray">
                    <th style="text-align: center; padding-left: 8px" width="10%">序</th>
                    <th style="padding-left: 8px" width="50%" align="left">健保處置</th>
                    <th style="padding-right: 8px" align="right" width="25%">次數</th>
                    <th style="padding-left: 8px" align="left" width="15%">備註</th>
                </tr>
            </thead>
            <tbody>
                {treatment_data}
                {prescript_data}
            </tbody>
        </table>
        <br>
    '''.format(
        treatment_data=treatment_data,
        prescript_data=prescript_data,
    )

    return prescript_html


def get_self_prescript_medicine_record(database, system_settings, case_key):
    prescript_html = ''

    max_medicine_set = prescript_utils.get_max_medicine_set(database, case_key)
    if max_medicine_set is None:
        return prescript_html

    for medicine_set in range(2, max_medicine_set+1):
        prescript_html += get_prescript_medicine_record(database, system_settings, case_key, medicine_set)

    return prescript_html


# 拷貝過去病歷
def copy_past_medical_record(
        database, medical_record, case_key, copy_diagnostic, copy_remark, copy_disease,
        copy_ins_prescript, copy_ins_prescript_to, copy_ins_treat, copy_self_prescript):
    sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return

    row = rows[0]
    ui = medical_record.ui
    if copy_diagnostic:
        ui.textEdit_symptom.setText(string_utils.get_str(row['Symptom'], 'utf8'))
        ui.textEdit_tongue.setText(string_utils.get_str(row['Tongue'], 'utf8'))
        ui.textEdit_pulse.setText(string_utils.get_str(row['Pulse'], 'utf8'))

    if copy_remark:
        ui.textEdit_remark.setText(string_utils.get_str(row['Remark'], 'utf8'))

    if copy_disease:
        line_edit_disease = [
            [ui.lineEdit_disease_code1, ui.lineEdit_disease_name1],
            [ui.lineEdit_disease_code2, ui.lineEdit_disease_name2],
            [ui.lineEdit_disease_code3, ui.lineEdit_disease_name3],
        ]

        for i in range(3):
            disease_code = string_utils.get_str(row['DiseaseCode{0}'.format(i+1)], 'utf8')
            disease_name = string_utils.get_str(row['DiseaseName{0}'.format(i+1)], 'utf8')

            if disease_code.isdigit():
                disease_code = icd9_to_icd10(database, disease_code)

            line_edit_disease[i][0].setText(disease_code)
            line_edit_disease[i][1].setText(disease_name)

    medical_record.close_all_self_prescript_tabs()
    if copy_ins_prescript:
        if copy_ins_prescript_to == '健保處方':
            if medical_record.tab_list[0] is not None:
                medical_record.tab_list[0].copy_past_prescript(case_key, '病歷拷貝')
        else:
            if medical_record.tab_list[1] is None:
                medical_record.add_prescript_tab(2)

            medical_record.tab_list[1].copy_past_prescript(case_key, 1)

    if copy_ins_treat:
        if medical_record.tab_list[0] is not None:
            medical_record.tab_list[0].copy_past_treat(case_key, '病歷拷貝')

    if copy_self_prescript:
        sql = '''
            SELECT MedicineSet FROM prescript 
            WHERE 
                CaseKey = {0} AND
                MedicineSet >= 2
            GROUP BY MedicineSet ORDER BY MedicineSet
        '''.format(case_key)
        rows = database.select_record(sql)

        for row in rows:
            medicine_set = row['MedicineSet']

            if medicine_set == 11:
                continue

            tab_index = medicine_set - 1
            if medical_record.tab_list[tab_index] is None:
                medical_record.add_prescript_tab(medicine_set)
            else:
                if medical_record.tab_list[tab_index].tableWidget_prescript.rowCount() > 0:  # 原本的自費處方已被拷貝佔用
                    medical_record.add_prescript_tab(medicine_set+1)
                    tab_index += 1

            medical_record.tab_list[tab_index].copy_past_prescript(case_key, medicine_set)

    if medical_record.tab_list[1] is None:  # 2019.04.27 拷貝完, 清除所有自費處方後, 自動新增自費處方1
        medical_record.add_prescript_tab()
        medical_record.ui.tabWidget_prescript.setCurrentIndex(0)


def icd9_to_icd10(database, icd9_code):
    sql = '''
        SELECT * FROM icdmap 
        WHERE
            ICD9Code = "{0}"
        ORDER BY ICD10Code LIMIT 1
    '''.format(icd9_code)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return icd9_code

    return string_utils.xstr(rows[0]['ICD10Code'])

#  取得中(英)文病名
def get_disease_name(database, disease_code, field_name=None):
    disease_name = ''
    if field_name is None:
        field_name = 'ChineseName'


    sql = '''
        SELECT {0} FROM icd10
        WHERE
            ICDCode = "{1}"
    '''.format(field_name, disease_code)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return disease_name

    row = rows[0]
    disease_name = string_utils.xstr(row[field_name])

    return disease_name


def get_medicine_name(database, field_name, field_value):
    if field_name == 'MedicineKey':
        condition = '{0} = {1}'.format(field_name, field_value)
    else:
        condition = '{0} = "{1}"'.format(field_name, field_value)

    sql = '''
        SELECT MedicineName FROM medicine
        WHERE
            {condition}
    '''.format(condition=condition)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]
    medicine_name = string_utils.xstr(row['MedicineName'])

    return medicine_name


def get_drug_name(database, ins_code):

    sql = '''
        SELECT DrugName FROM drug
        WHERE
            InsCode = "{0}"
    '''.format(ins_code)

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ''

    row = rows[0]
    drug_name = string_utils.xstr(row['DrugName'])

    return drug_name


def get_disease_name_html(in_disease_name):
    if in_disease_name is None:
        return None

    for word in INJURY_LIST:
        new_word = '<font color="red">{0}</font>'.format(word)
        in_disease_name = in_disease_name.replace(word, new_word)

    word = '右側'
    new_word = '<font color="blue">{0}</font>'.format(word)
    in_disease_name = in_disease_name.replace(word, new_word)

    word = '左側'
    new_word = '<font color="green">{0}</font>'.format(word)
    in_disease_name = in_disease_name.replace(word, new_word)

    return QtWidgets.QLabel(in_disease_name)


def get_full_card(card, course):
    card = string_utils.xstr(card)
    if number_utils.get_integer(course) >= 1:
        card += '-{0}'.format(course)

    return card


def is_disease_code_neat(database, disease_code):
    is_neat = True

    sql = '''
        SELECT ICD10Key FROM icd10
        WHERE
            ICDCode LIKE "{disease_code}%"
    '''.format(
        disease_code=disease_code,
    )

    rows = database.select_record(sql)
    if len(rows) >= 2:
        is_neat = False

    return is_neat

def is_disease_code_exist(database, disease_code):
    is_exist = True

    sql = '''
        SELECT ICD10Key FROM icd10
        WHERE
            ICDCode = "{disease_code}"
    '''.format(
        disease_code=disease_code,
    )

    rows = database.select_record(sql)
    if len(rows) <= 0:
        is_exist = False

    return is_exist


def get_disease_special_code(database, disease_code):
    sql = '''
        SELECT SpecialCode FROM icd10
        WHERE
            ICDCode = "{disease_code}"
    '''.format(
        disease_code=disease_code,
    )

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return None

    return string_utils.xstr(rows[0]['SpecialCode']).strip()


# def get_security_xml_dict(root):
#     security_xml_dict = {
#         '寫卡時間': root[0].text,
#         '健保卡序': root[1].text,
#         '院所代號': root[2].text,
#         '安全簽章': root[3].text,
#         '安全模組': root[4].text,
#         '同日就診': root[5].text,
#         '上傳時間': root[6].text,
#         '資料格式': root[7].text,
#         '補卡註記': root[8].text,
#         '醫令時間': root[9].text,
#     }
#
#     return security_xml_dict


# def get_treat_data_xml_dict(xml_string):
#     security_xml_dict = create_treat_data_xml_dict()
#
#     try:
#         root = ET.fromstring(xml_string)[0]
#         for child in root:
#             security_xml_dict[child.tag] = child.text
#     except ET.ParseError:
#         pass
#
#     return security_xml_dict


# 取出病歷檔安全簽章XML
# def extract_security_xml(xml_field, field):
#     ic_card_xml = ''.join(string_utils.get_str(xml_field, 'utf-8'))
#     try:
#         root = ET.fromstring(ic_card_xml)[0]
#     except ET.ParseError:
#         return ''
#
#     security_xml_dict = get_security_xml_dict(root)
#
#     return security_xml_dict[field]


# 寫入病歷檔安全簽章XML
# def update_xml_doc(database, xml_field, field_name, field_value):
#     sql = """
#         SELECT UPDATEXML('{0}', '{1}', '{2}')
#     """.format(
#         xml_field,
#         '//{0}'.format(field_name),
#         '<{0}>{1}</{0}>'.format(field_name, field_value)
#     )
#     row = database.select_record(sql, False)[0]
#
#     return row[0]


# def extract_xml(database, case_key, xml_field):
#     sql = '''
#             SELECT ExtractValue(Security, "//{0}") AS xml_value
#             FROM cases WHERE
#                 CaseKey = {1}
#         '''.format(xml_field, case_key)
#     row = database.select_record(sql)[0]
#     xml_value =string_utils.get_str(row['xml_value'], 'utf-8')  # 1-正常上傳 2-異常上傳 3-正常補正 4-異常補正
#
#     return xml_value


# def create_security_xml(treat_data=None):
#     if treat_data is None:
#         treat_data = create_treat_data_xml_dict()
#
#     doc = Document()
#     document = doc.createElement('DOCUMENT')
#     document.setAttribute('content', 'cshis')
#
#     doc.appendChild(document)
#     security = doc.createElement('treat_data')
#     document.appendChild(security)
#
#     registered_date = doc.createElement('registered_date')
#     registered_date_value = doc.createTextNode(
#         treat_data['registered_date']
#     )
#     registered_date.appendChild(registered_date_value)
#     security.appendChild(registered_date)
#
#     seq_number = doc.createElement('seq_number')
#     seq_number_value = doc.createTextNode(
#         treat_data['seq_number']
#     )
#     seq_number.appendChild(seq_number_value)
#     security.appendChild(seq_number)
#
#     clinic_id = doc.createElement('clinic_id')
#     clinic_id_value = doc.createTextNode(
#         treat_data['clinic_id']
#     )
#     clinic_id.appendChild(clinic_id_value)
#     security.appendChild(clinic_id)
#
#     security_signature = doc.createElement('security_signature')
#     security_signature_value = doc.createTextNode(
#         treat_data['security_signature']
#     )
#     security_signature.appendChild(security_signature_value)
#     security.appendChild(security_signature)
#
#     sam_id = doc.createElement('sam_id')
#     sam_id_value = doc.createTextNode(
#         treat_data['sam_id']
#     )
#     sam_id.appendChild(sam_id_value)
#     security.appendChild(sam_id)
#
#     register_duplicated = doc.createElement('register_duplicated')
#     register_duplicated_value = doc.createTextNode(
#         treat_data['register_duplicated']
#     )
#     register_duplicated.appendChild(register_duplicated_value)
#     security.appendChild(register_duplicated)
#
#     upload_time = doc.createElement('upload_time')
#     upload_time_value = doc.createTextNode(
#         treat_data['upload_time']
#     )
#     upload_time.appendChild(upload_time_value)
#     security.appendChild(upload_time)
#
#     upload_type = doc.createElement('upload_type')
#     upload_type_value = doc.createTextNode(
#         treat_data['upload_type']
#     )
#     upload_type.appendChild(upload_type_value)
#     security.appendChild(upload_type)
#
#     treat_after_check = doc.createElement('treat_after_check')
#     treat_after_check_value = doc.createTextNode(
#         treat_data['treat_after_check']
#     )
#     treat_after_check.appendChild(treat_after_check_value)
#     security.appendChild(treat_after_check)
#
#     prescript_sign_time = doc.createElement('prescript_sign_time')
#     prescript_sign_time_value = doc.createTextNode(
#         treat_data['prescript_sign_time']
#     )
#     prescript_sign_time.appendChild(prescript_sign_time_value)
#     security.appendChild(prescript_sign_time)
#
#     return doc

