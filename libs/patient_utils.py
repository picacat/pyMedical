
from PyQt5.QtWidgets import QMessageBox
from dialog import dialog_patient
import datetime
import re

from classes import address

from libs import string_utils
from libs import system_utils
from libs import date_utils
from libs import validator_utils
from dialog import dialog_select_patient


# 尋找病患資料
def search_patient(ui, database, settings, keyword):
    if keyword.isnumeric():
        if len(keyword) >= 7:
            script = 'SELECT * FROM patient WHERE Telephone like "%{0}%" or Cellphone like "%{0}%"'.format(keyword)
        else:
            script = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(keyword)
    else:
        script = '''
            SELECT * FROM patient 
            WHERE 
                (Name like "%{0}%") or 
                (ID like "{0}%") or 
                (Birthday = "{0}")
            ORDER BY PatientKey
        '''.format(keyword)

    try:
        row = database.select_record(script)
    except:
        return None

    row_count = len(list(row))

    if row_count <= 0:
        return None
    elif row_count >= 2:
        dialog = dialog_patient.DialogPatient(ui, database, settings, row)
        dialog.exec_()
        patient_key = dialog.get_patient_key()
        if patient_key is None:  # 取消查詢
            return -1

        script = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
        row = database.select_record(script)

    return row


def select_patient(parent, database, system_settings, table_name, primary_key_field, keyword=None):
    primary_key = ''

    dialog = dialog_select_patient.DialogSelectPatient(
        parent, database, system_settings, table_name, primary_key_field, keyword
    )
    if dialog.exec_():
        primary_key = dialog.get_primary_key()

    dialog.deleteLater()

    return primary_key


def get_patient_by_keyword(parent, database, system_settings, table_name, primary_key_field, keyword=None):
    if keyword.isdigit() and len(keyword) <= 6:
        return keyword  # primary key

    condition = [
        'Name LIKE "%{0}%"'.format(keyword),
        'ID LIKE "{0}%"'.format(keyword),
        'Telephone LIKE "%{0}%"'.format(keyword),
        'Cellphone LIKE "{0}%"'.format(keyword),
    ]

    pattern = re.compile(validator_utils.DATE_REGEXP)
    if pattern.match(keyword):
        keyword = date_utils.date_to_west_date(keyword)
        condition.append('Birthday = "{0}"'.format(keyword))

    if len(keyword) >= 2:
        condition.append('Address LIKE "%{0}%"'.format(keyword))

    sql = '''
        SELECT {primary_key_field} FROM {table_name}
        WHERE
            {condition}
    '''.format(
        table_name=table_name,
        primary_key_field=primary_key_field,
        condition=' OR '.join(condition),
    )

    try:
        rows = database.select_record(sql)
    except:
        system_utils.show_message_box(
            QMessageBox.Critical,
            '資料查詢錯誤',
            '<font size="4" color="red"><b>資料查詢條件設定有誤, 請重新查詢.</b></font>',
            '請檢視查詢的內容是否有標點符號或其他字元.'
        )
        return None

    if len(rows) == 1:
        patient_key = rows[0][primary_key_field]
    else:
        patient_key = select_patient(
            parent, database, system_settings, table_name, primary_key_field, keyword,
        )

    return patient_key


# 取得性別
def get_gender(gender_code):
    gender = None

    if gender_code in ['1', 'A', 'C', 'Y', 'M']:
        gender = '男'
    elif gender_code in ['2', 'B', 'D', 'X', 'F']:
        gender = '女'

    return gender


# 取得國籍
def get_nationality(gender_code):
    nationality = '本國'

    if gender_code in ['1', '2']:
        nationality = '本國'
    elif gender_code in ['C', 'D']:
        nationality = '外國'
    elif gender_code in ['A', 'B']:
        nationality = '居留證'
    elif gender_code in ['Y', 'X']:
        nationality = '遊民'

    return nationality


# 取得初複診
def get_visit(database, patient_key):
    visit = '複診'
    sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
    row = database.select_record(sql)[0]
    if row['InitDate'] is None:
        return visit

    current_date=datetime.datetime.now()
    if row['InitDate'].year == current_date.year and row['InitDate'].month == current_date.month and row['InitDate'].day == current_date.day:
        visit = '初診'

    return visit


def get_init_date(database, patient_key):
    sql = '''
            SELECT * FROM patient
            WHERE
                PatientKey = {0}
        '''.format(patient_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return None

    row = rows[0]

    init_date = string_utils.xstr(row['InitDate'])
    if init_date != '':
        init_date = string_utils.xstr(row['InitDate'].date())
    else:
        sql = '''
                SELECT CaseDate FROM cases
                WHERE
                    InsType = "健保" AND
                    PatientKey = {0}
                ORDER BY CaseDate LIMIT 1
            '''.format(patient_key)

        rows = database.select_record(sql)
        if len(rows) > 0:
            init_date = rows[0]['CaseDate'].date()

    return init_date


def get_patient_row(database, patient_key):
    if patient_key is None:
        return None

    sql = '''
        SELECT * FROM patient
        WHERE
            PatientKey = {0}
    '''.format(patient_key)

    rows = database.select_record(sql)

    if len(rows) <= 0:
        return None

    return rows[0]


def get_gender_code(gender):
    gender_dict = {'男': 'M', '女': 'F'}

    try:
        gender_code = gender_dict[gender]
    except KeyError:
        gender_code = 'UN'

    return  gender_code


def get_marriage_code(marriage):
    if marriage == '已婚':
        marriage_code = 'M'
    else:
        marriage_code = 'S'

    return marriage_code


def get_zip_code(database, address_str):
    zip_code = '100'
    if address_str == '':
        return ''

    city_list = []
    rows = database.select_record('SELECT City FROM address_list GROUP BY city')
    for row in rows:
        city_list.append(row['City'])

    try:
        addr = address.Address(address_str)
        city = addr.flat(1)
        district = addr.flat(2)

        if city == '平鎮':  # 特殊狀況, 有雙關鍵字
            city = '桃園市'
            district = '平鎮區'
        elif addr.tokens[0][addr.UNIT] == '縣' and city not in city_list:
            city = addr.tokens[0][addr.NAME] + '市'
            district = addr.tokens[1][addr.NAME] + '區'
        elif addr.tokens[0][addr.UNIT] == '市' and city not in city_list:
            city = None
            district = addr.tokens[0][addr.NAME]
            rows = database.select_record(
                'SELECT City, District FROM address_list WHERE District LIKE "{0}%"'.format(district)
            )
            if len(rows) > 0:
                district = string_utils.xstr(rows[0]['District'])
                city = string_utils.xstr(rows[0]['City'])

        sql = '''
            SELECT ZipCode FROM address_list 
            WHERE
                City = "{0}" AND District = "{1}"
            LIMIT 1
        '''.format(city, district)
        rows = database.select_record(sql)

        if len(rows) > 0:
            zip_code = rows[0]['ZipCode'][:3]
    except:
        pass

    return zip_code


def get_patient_id(database, patient_key):
    sql = '''
        SELECT ID FROM patient
        WHERE
            PatientKey = {patient_key}
    '''.format(
        patient_key=patient_key,
    )
    rows = database.select_record(sql)

    if len(rows) <= 0:
        return None

    return string_utils.xstr(rows[0]['ID'])


def get_temp_patient(database, temp_patient_key, field):
    if temp_patient_key is None:
        return None

    sql = '''
        SELECT * FROM temp_patient
        WHERE
            TempPatientKey = {temp_patient_key}
    '''.format(
        temp_patient_key=temp_patient_key,
    )

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return None

    row = rows[0]

    return row[field]
