from PyQt5 import QtWidgets, QtGui
from lxml import etree as ET
from libs import string_utils
from libs import number_utils
from libs import prescript_utils
from libs import db_utils


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


def get_dosage_row(database, case_key, medicine_set=1):
    sql = '''
        SELECT * FROM dosage WHERE 
            CaseKey = {0} AND
            MedicineSet = {1}
    '''.format(case_key, medicine_set)
    rows = database.select_record(sql)

    return rows


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


def get_discount_rate(database, case_key, medicine_set=1):
    sql = '''
        SELECT DiscountRate FROM dosage WHERE 
            CaseKey = {0} AND
            MedicineSet = {1} 
    '''.format(case_key, medicine_set)
    rows = database.select_record(sql)

    if len(rows) > 0:
        discount_rate = number_utils.get_integer(rows[0]['DiscountRate'])
    else:
        discount_rate = 100

    return discount_rate


def get_discount_fee(database, case_key, medicine_set=1):
    sql = '''
        SELECT DiscountFee FROM dosage WHERE 
            CaseKey = {0} AND
            MedicineSet = {1} 
    '''.format(case_key, medicine_set)
    rows = database.select_record(sql)

    if len(rows) > 0:
        discount_fee = number_utils.get_integer(rows[0]['DiscountFee'])
    else:
        discount_fee = None

    return discount_fee


def get_host_pres_days(database, case_key, medicine_set=1):
    if medicine_set >= 4:
        return 0

    sql = '''
        SELECT PresDays{medicine_set} FROM cases WHERE 
            CaseKey = {case_key}
    '''.format(
        case_key=case_key,
        medicine_set=medicine_set
    )
    rows = database.select_record(sql)

    if len(rows) > 0:
        pres_days = number_utils.get_integer(rows[0]['PresDays{0}'.format(medicine_set)])
    else:
        pres_days = 0

    return pres_days


def get_host_packages(database, case_key, medicine_set=1):
    if medicine_set >= 4:
        return 0

    sql = '''
        SELECT Package{medicine_set} FROM cases 
        WHERE 
            CaseKey = {case_key}
    '''.format(
        case_key=case_key,
        medicine_set=medicine_set
    )
    rows = database.select_record(sql)

    if len(rows) > 0:
        package = number_utils.get_integer(rows[0]['Package{0}'.format(medicine_set)])
    else:
        package = 0

    return package


def get_host_instruction(database, case_key, medicine_set=1):
    if medicine_set >= 4:
        return None

    sql = '''
        SELECT Instruction{medicine_set} FROM cases 
        WHERE 
            CaseKey = {case_key}
    '''.format(
        case_key=case_key,
        medicine_set=medicine_set
    )
    rows = database.select_record(sql)

    if len(rows) > 0:
        instruction = string_utils.xstr(rows[0]['Instruction{0}'.format(medicine_set)])
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

    medical_record = '<b>日期</b>: {case_date} {card} <b>醫師</b>:{doctor}<hr>'.format(
        case_date=string_utils.xstr(row['CaseDate'].date()),
        card=card,
        doctor=string_utils.xstr(row['Doctor']),
    )

    if row['Symptom'] is not None and string_utils.xstr(row['Symptom']) != '':
        medical_record += '<b>主訴</b>: {0}<hr>'.format(string_utils.get_str(row['Symptom'], 'utf8'))
    if row['Tongue'] is not None and string_utils.xstr(row['Tongue']) != '':
        medical_record += '<b>舌診</b>: {0}<hr>'.format(string_utils.get_str(row['Tongue'], 'utf8'))
    if row['Pulse'] is not None and string_utils.xstr(row['Pulse']) != '':
        medical_record += '<b>脈象</b>: {0}<hr>'.format(string_utils.get_str(row['Pulse'], 'utf8'))
    if row['Distincts'] is not None and string_utils.xstr(row['Distincts']) != '':
        medical_record += '<b>辨證</b>: {0}<hr>'.format(string_utils.xstr(row['Distincts']))
    if row['Cure'] is not None and string_utils.xstr(row['Cure']) != '':
        medical_record += '<b>治則</b>: {0}<hr>'.format(string_utils.xstr(row['Cure']))
    if row['Remark'] is not None and string_utils.xstr(row['Remark']) != '':
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
        ORDER BY PrescriptKey
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
        if string_utils.xstr(row['MedicineName']) in ['', '優待']:
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

    try:
        rows = get_dosage_row(database, case_key, medicine_set)
        if len(rows) <= 0:
            return dosage_data
    except:
        if medicine_set >= 4:
            return dosage_data

        rows = [{}]
        sql = '''
            SELECT 
                PresDays{medicine_set}, Package{medicine_set}, Instruction{medicine_set}
            FROM cases
            WHERE
                CaseKey = {case_key}
        '''.format(
            medicine_set=medicine_set,
            case_key=case_key,
        )
        dosage_row = database.select_record(sql)
        if len(dosage_row) <= 0:
            return dosage_data

        rows[0]['Days'] = number_utils.get_integer(
            dosage_row[0]['PresDays{0}'.format(medicine_set)]
        )
        rows[0]['Packages'] = number_utils.get_integer(
            dosage_row[0]['Package{0}'.format(medicine_set)]
        )
        rows[0]['Instruction'] = string_utils.xstr(
            dosage_row[0]['Instruction{0}'.format(medicine_set)]
        )

    row = rows[0]
    pres_days = number_utils.get_integer(row['Days'])
    packages = number_utils.get_integer(row['Packages'])
    try:
        self_total_fee = number_utils.get_integer(row['SelfTotalFee'])
    except KeyError:
        self_total_fee = None

    if packages > 0 or pres_days > 0:
        instruction = string_utils.xstr(row['Instruction'])
        dosage_data = '''
            <tr>
                <td style="text-align: left; padding-left: 30px;" colspan="4">
                    用法: {packages}包 {pres_days}日份 {instruction}服用 總量: {total_dosage}
                </td>
            </tr>
        '''.format(
            packages=packages,
            pres_days=pres_days,
            instruction=instruction,
            total_dosage=total_dosage,
        )

    if self_total_fee is not None and self_total_fee > 0:
        discount_rate = number_utils.get_integer(row['DiscountRate'])
        discount_fee = number_utils.get_integer(row['DiscountFee'])
        total_fee = number_utils.get_integer(row['TotalFee'])
        dosage_data += '''
            <tr>
                <td style="text-align: left; padding-left: 30px;" colspan="4">
                    自費合計: ${self_total_fee:,} 優待: {discount_rate}% 折扣金額: ${discount_fee:,}
                    應收金額: ${total_fee:,}
                </td>
            </tr>
        '''.format(
            self_total_fee=self_total_fee,
            discount_rate=discount_rate,
            discount_fee=discount_fee,
            total_fee=total_fee,
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
        ui.lineEdit_distinguish.setText(string_utils.xstr(row['Distincts']))
        ui.lineEdit_cure.setText(string_utils.xstr(row['Cure']))

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

        medical_record.tab_registration.ui.lineEdit_special_code.setText(
            string_utils.xstr(row['SpecialCode'])
        )

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
        medical_record.close_all_self_prescript_tabs()
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


# 拷貝處方集
def copy_collection(
        database, medical_record, medical_row, copy_diagnostic, copy_disease, copy_prescript):
    ui = medical_record.ui
    if copy_diagnostic:
        ui.textEdit_symptom.setText(string_utils.get_str(medical_row['Symptom'], 'utf8'))
        ui.textEdit_tongue.setText(string_utils.get_str(medical_row['Tongue'], 'utf8'))
        ui.textEdit_pulse.setText(string_utils.get_str(medical_row['Pulse'], 'utf8'))
        ui.lineEdit_distinguish.setText(string_utils.xstr(medical_row['Distincts']))
        ui.lineEdit_cure.setText(string_utils.xstr(medical_row['Cure']))

    if copy_disease:
        line_edit_disease = [
            [ui.lineEdit_disease_code1, ui.lineEdit_disease_name1],
            [ui.lineEdit_disease_code2, ui.lineEdit_disease_name2],
            [ui.lineEdit_disease_code3, ui.lineEdit_disease_name3],
        ]
        disease_list = []
        for i in range(3):
            icd9_code = string_utils.xstr(medical_row['ICDCode{0}'.format(i + 1)])
            if icd9_code == '':
                continue

            icd10_code, icd10_name = convert_icd9_to_icd10(database, icd9_code)
            if icd10_name is not None:
                disease_list.append([icd10_code, icd10_name])

        for item_no, item in zip(range(len(disease_list)), disease_list):
            disease_code = item[0]
            disease_name = item[1]

            line_edit_disease[item_no][0].setText(disease_code)
            line_edit_disease[item_no][1].setText(disease_name)

    if medical_record.tab_list[0] is None:  # 無健保處方
        return

    if copy_prescript:
        collection_key = medical_row['CollectionKey']
        if collection_key is None:
            return

        sql = '''
            SELECT * FROM collitems
            WHERE
                CollectionKey = {collection_key}
            ORDER BY CollectionSetKey
        '''.format(
            collection_key=collection_key,
        )
        prescript_rows = database.select_record(sql)

        treat_dict = {
            '針灸處置': '針灸治療',
            '傷科處置': '傷科治療',
        }
        medical_record.tab_list[0].ui.tableWidget_treat.setRowCount(0)
        medical_record.tab_list[0].set_treat_ui()

        for prescript_row in prescript_rows:
            medicine_name = string_utils.xstr(prescript_row['MedicineName'])
            if medicine_name in ['針灸處置', '傷科處置']:
                medical_record.tab_list[0].combo_box_treatment.setCurrentText(treat_dict[medicine_name])
                continue

            row = {
                'MedicineType': string_utils.xstr(prescript_row['MedicineType']),
                'MedicineKey': string_utils.xstr(prescript_row['MedicineKey']),
                'MedicineName': string_utils.xstr(prescript_row['MedicineName']),
                'InsCode': string_utils.xstr(prescript_row['InsCode']),
            }
            medical_record.tab_list[0].append_treat(row)
            medical_record.tab_list[0].append_null_treat()


# 拷貝分院過去病歷
def copy_host_medical_record(
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
        ui.lineEdit_distinguish.setText(string_utils.xstr(row['Distincts']))
        ui.lineEdit_cure.setText(string_utils.xstr(row['Cure']))

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

        medical_record.tab_registration.ui.lineEdit_special_code.setText(
            string_utils.xstr(row['SpecialCode'])
        )

    medical_record.close_all_self_prescript_tabs()
    if copy_ins_prescript:
        if copy_ins_prescript_to == '健保處方':
            if medical_record.tab_list[0] is not None:
                medical_record.tab_list[0].copy_host_prescript(database, case_key, '病歷拷貝')
        else:
            if medical_record.tab_list[1] is None:
                medical_record.add_prescript_tab(2)

            medical_record.tab_list[1].copy_host_prescript(database, case_key, 1)

    if copy_ins_treat:
        if medical_record.tab_list[0] is not None:
            medical_record.tab_list[0].copy_host_treat(database, case_key, '病歷拷貝')

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

            medical_record.tab_list[tab_index].copy_host_prescript(database, case_key, medicine_set)

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

    if disease_code in ['', None]:
        return ''

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


def backup_cases(database, case_key, deleter, delete_datetime):
    sql = '''
        SELECT * FROM cases
        WHERE
            CaseKey = {case_key}
    '''.format(
        case_key=case_key,
    )
    rows = database.select_record(sql)

    json_data = db_utils.mysql_to_json(rows)
    if len(json_data) <= 0:
        return

    fields = [
        'TableName', 'KeyField', 'KeyValue', 'JSON',
        'Deleter', 'DeleteDateTime',
    ]

    data = [
        'cases',
        'CaseKey',
        case_key,
        json_data,
        deleter,
        delete_datetime,
    ]

    database.insert_record('backup_records', fields, data)


def backup_prescript(database, case_key, deleter, delete_datetime):
    sql = '''
        SELECT * FROM prescript
        WHERE
            CaseKey = {case_key}
        ORDER BY PrescriptKey
    '''.format(
        case_key=case_key,
    )
    rows = database.select_record(sql)

    json_data = db_utils.mysql_to_json(rows)
    if len(json_data) <= 0:
        return

    fields = [
        'TableName', 'KeyField', 'KeyValue', 'JSON',
        'Deleter', 'DeleteDateTime',
    ]
    data = [
        'prescript',
        'CaseKey',
        case_key,
        json_data,
        deleter,
        delete_datetime,
    ]
    database.insert_record('backup_records', fields, data)


def backup_dosage(database, case_key, deleter, delete_datetime):
    sql = '''
        SELECT * FROM dosage
        WHERE
            CaseKey = {case_key}
        ORDER BY DosageKey
    '''.format(
        case_key=case_key,
    )
    rows = database.select_record(sql)

    json_data = db_utils.mysql_to_json(rows)
    if len(json_data) <= 0:
        return

    fields = [
        'TableName', 'KeyField', 'KeyValue', 'JSON',
        'Deleter', 'DeleteDateTime',
    ]

    data = [
        'dosage',
        'CaseKey',
        case_key,
        json_data,
        deleter,
        delete_datetime,
    ]
    database.insert_record('backup_records', fields, data)


def backup_medical_record(database, case_key, deleter, delete_datetime):
    backup_cases(database, case_key, deleter, delete_datetime)
    backup_prescript(database, case_key, deleter, delete_datetime)
    backup_dosage(database, case_key, deleter, delete_datetime)


def set_in_progress_icon(table_widget, row_no, col_no, in_progress):
    table_widget.setCellWidget(row_no, col_no, None)

    if in_progress == 'Y':
        icon = QtGui.QIcon('./icons/user-info.png')
        button = QtWidgets.QPushButton(table_widget)
        button.setIcon(icon)
        button.setFlat(True)
        table_widget.setCellWidget(row_no, col_no, button)


def get_return_date(database, case_key):
    sql = '''
        SELECT  ReturnDate FROM deposit
        WHERE
            CaseKey = {case_key}
    '''.format(
        case_key=case_key,
    )

    rows = database.select_record(sql)

    if len(rows) <= 0:
        return None

    return rows[0]['ReturnDate']


def convert_icd9_to_icd10(database, icd9_code):
    sql = '''
        SELECT * FROM icdmap
        WHERE
            ICD9Code = "{icd9_code}"
        ORDER BY LENGTH(ICD10Code) DESC
        LIMIT 1
    '''.format(
        icd9_code=icd9_code,
    )

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return icd9_code, None

    row = rows[0]

    return string_utils.xstr(row['ICD10Code']), string_utils.xstr(row['ICD10ChineseName'])


# 取得病歷html格式
def get_medical_record_row_html(medical_record_row):
    if medical_record_row['InsType'] == '健保':
        card = str(medical_record_row['Card'])
        if number_utils.get_integer(medical_record_row['Continuance']) >= 1:
            card += '-' + str(medical_record_row['Continuance'])
        card = '<b>健保</b>: {0}'.format(card)
    else:
        card = '<b>自費</b>'

    medical_record = '<b>日期</b>: {case_date} {card} <b>醫師</b>:{doctor}<hr>'.format(
        case_date=string_utils.xstr(medical_record_row['CaseDate']),
        card=card,
        doctor=string_utils.xstr(medical_record_row['Doctor']),
    )

    if medical_record_row['Symptom'] is not None and string_utils.xstr(medical_record_row['Symptom']) != '':
        medical_record += '<b>主訴</b>: {0}<hr>'.format(string_utils.get_str(medical_record_row['Symptom'], 'utf8'))
    if medical_record_row['Tongue'] is not None and string_utils.xstr(medical_record_row['Tongue']) != '':
        medical_record += '<b>舌診</b>: {0}<hr>'.format(string_utils.get_str(medical_record_row['Tongue'], 'utf8'))
    if medical_record_row['Pulse'] is not None and string_utils.xstr(medical_record_row['Pulse']) != '':
        medical_record += '<b>脈象</b>: {0}<hr>'.format(string_utils.get_str(medical_record_row['Pulse'], 'utf8'))
    if medical_record_row['Distincts'] is not None and string_utils.xstr(medical_record_row['Distincts']) != '':
        medical_record += '<b>辨證</b>: {0}<hr>'.format(string_utils.xstr(medical_record_row['Distincts']))
    if medical_record_row['Cure'] is not None and string_utils.xstr(medical_record_row['Cure']) != '':
        medical_record += '<b>治則</b>: {0}<hr>'.format(string_utils.xstr(medical_record_row['Cure']))
    if medical_record_row['Remark'] is not None and string_utils.xstr(medical_record_row['Remark']) != '':
        medical_record += '<b>備註</b>: {0}<hr>'.format(string_utils.get_str(medical_record_row['Remark'], 'utf8'))
    if medical_record_row['DiseaseCode1'] is not None and len(str(medical_record_row['DiseaseCode1']).strip()) > 0:
        medical_record += '<b>主診斷</b>: {0} {1}<br>'.format(str(medical_record_row['DiseaseCode1']), str(medical_record_row['DiseaseName1']))
    if medical_record_row['DiseaseCode2'] is not None and len(str(medical_record_row['DiseaseCode2']).strip()) > 0:
        medical_record += '<b>次診斷1</b>: {0} {1}<br>'.format(str(medical_record_row['DiseaseCode2']), str(medical_record_row['DiseaseName2']))
    if medical_record_row['DiseaseCode3'] is not None and len(str(medical_record_row['DiseaseCode3']).strip()) > 0:
        medical_record += '<b>次診斷2</b>: {0} {1}<br>'.format(str(medical_record_row['DiseaseCode3']), str(medical_record_row['DiseaseName3']))

    medical_record = '''
        <div style="width: 95%;">
            {0}
        </div>
    '''.format(medical_record)

    prescript_record = get_prescript_row_html(medical_record_row)

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


def get_prescript_row_html(medical_record_row):
    rows = medical_record_row['PrescriptJSON']

    if len(rows) <= 0:
        return '<br><br><br><center>無開立處方</center><br>'

    html = get_prescript_row_medicine_record(medical_record_row, 1)
    html += get_ins_prescript_treat_row_record(medical_record_row)
    html += get_self_prescript_medicine_row_record(medical_record_row)

    return html


def get_prescript_row_medicine_record(medical_record_row, medicine_set):
    rows = medical_record_row['PrescriptJSON']
    medicine_rows = []
    for row in rows:
        if row['MedicineType'] not in ['穴道', '處置', '檢驗'] and row['MedicineSet'] == medicine_set:
            medicine_rows.append(row)

    prescript_data, total_dosage = get_prescript_row_html_data(medicine_rows, medicine_set)
    if prescript_data == '':
        return ''

    prescript_data += get_dosage_row_html(medical_record_row, medicine_set, total_dosage)
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


def get_prescript_row_html_data(rows, medicine_set):
    prescript_data = ''
    total_dosage = 0

    if len(rows) <= 0:
        return prescript_data, total_dosage

    sequence = 0
    for row in rows:
        if string_utils.xstr(row['MedicineName']) in ['', '優待']:
            continue

        sequence += 1

        if row['Dosage'] is None or row['Dosage'] == 0.00:
            dosage = ''
        else:
            dosage_value = number_utils.get_float(row['Dosage'])
            dosage = '{0:.1f}'.format(dosage_value)
            total_dosage += dosage_value

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


def get_dosage_row_html(medical_record_row, medicine_set, total_dosage):
    dosage_data = ''

    rows = medical_record_row['DosageJSON']
    if len(rows) <= 0:
        return dosage_data

    try:
        row = rows[medicine_set-1]
    except IndexError:
        return dosage_data

    pres_days = number_utils.get_integer(row['Days'])
    packages = number_utils.get_integer(row['Packages'])
    try:
        self_total_fee = number_utils.get_integer(row['SelfTotalFee'])
    except KeyError:
        self_total_fee = None

    if packages > 0 or pres_days > 0:
        instruction = string_utils.xstr(row['Instruction'])
        dosage_data = '''
            <tr>
                <td style="text-align: left; padding-left: 30px;" colspan="4">
                    用法: {packages}包 {pres_days}日份 {instruction}服用 總量: {total_dosage}
                </td>
            </tr>
        '''.format(
            packages=packages,
            pres_days=pres_days,
            instruction=instruction,
            total_dosage=total_dosage,
        )

    if self_total_fee is not None and self_total_fee > 0:
        discount_rate = number_utils.get_integer(row['DiscountRate'])
        discount_fee = number_utils.get_integer(row['DiscountFee'])
        total_fee = number_utils.get_integer(row['TotalFee'])
        dosage_data += '''
            <tr>
                <td style="text-align: left; padding-left: 30px;" colspan="4">
                    自費合計: ${self_total_fee:,} 優待: {discount_rate}% 折扣金額: ${discount_fee:,}
                    應收金額: ${total_fee:,}
                </td>
            </tr>
        '''.format(
            self_total_fee=self_total_fee,
            discount_rate=discount_rate,
            discount_fee=discount_fee,
            total_fee=total_fee,
        )

    return dosage_data


def get_ins_prescript_treat_row_record(medical_record_row):
    medicine_set = 1
    prescript_html = ''
    treatment = string_utils.xstr(medical_record_row['Treatment'])

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

    rows = medical_record_row['PrescriptJSON']
    medicine_rows = []
    for row in rows:
        if row['MedicineType'] in ['穴道', '處置', '檢驗'] and row['MedicineSet'] == medicine_set:
            medicine_rows.append(row)

    prescript_data, _ = get_prescript_row_html_data(medicine_rows, medicine_set)

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


def get_self_prescript_medicine_row_record(medical_record_row):
    prescript_html = ''

    max_medicine_set = 1
    rows = medical_record_row['PrescriptJSON']
    for row in rows:
        medicine_set = row['MedicineSet']
        if medicine_set > max_medicine_set:
            max_medicine_set = medicine_set

    if max_medicine_set <= 1:
        return prescript_html

    for medicine_set in range(2, max_medicine_set+1):
        prescript_html += get_prescript_row_medicine_record(medical_record_row, medicine_set)

    return prescript_html
