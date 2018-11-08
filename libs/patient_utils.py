from dialog import dialog_patient
import datetime

from libs import string_utils


# 尋找病患資料
def search_patient(ui, database, settings, keyword):
    if keyword.isnumeric():
        if len(keyword) >= 7:
            script = 'SELECT * FROM patient WHERE Telephone like "%{0}%" or Cellphone like "%{0}%"'.format(keyword)
        else:
            script = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(keyword)
    else:
        script = ('SELECT * FROM patient WHERE '
                  '(Name like "%{0}%") or '
                  '(ID like "{0}%") or '
                  '(Birthday = "{0}")').format(keyword)

    script += ' ORDER BY PatientKey'
    row = database.select_record(script)
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
    sql = '''
        SELECT * FROM patient
        WHERE
            PatientKey = {0}
    '''.format(patient_key)

    rows = database.select_record(sql)

    if len(rows) <= 0:
        return None

    return rows[0]