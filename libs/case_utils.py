import xml.etree.ElementTree as ET
from xml.dom.minidom import Document
from libs import string_utils
from libs import number_utils


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


def get_pres_days(database, case_key):
    sql = '''
        SELECT * FROM dosage WHERE 
            MedicineSet = 1 AND
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)

    if len(rows) > 0:
        pres_days = number_utils.get_integer(rows[0]['Days'])
    else:
        pres_days = 0

    return pres_days
