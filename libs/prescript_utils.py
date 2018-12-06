
from PyQt5.QtWidgets import QMessageBox
from libs import system_utils
from libs import string_utils


# 取得服藥頻率代碼
def get_usage_code(package):
    usage_dict = {
        1: 'QD',
        2: 'BID',
        3: 'TID',
        4: 'QID',
    }

    return usage_dict[package]


# 取得服藥方式代碼
def get_instruction_code(instruction):
    if instruction.find('飯前') >= 0:
        instruction_code = 'AC'
    elif instruction.find('飯後') >= 0:
        instruction_code = 'PC'
    else:
        instruction_code = ''

    return  instruction_code

# 檢查是否重複＼開立處方
def check_prescript_exist(in_table_widget, col_no, check_value):
    exists = False

    row_count = in_table_widget.rowCount()
    field_value = None
    for row_no in range(row_count):
        field = in_table_widget.item(row_no, col_no)
        if field is not None:
            field_value = field.text()

        if check_value == field_value:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '重複處方或處置',
                '<font size="4" color="red"><b>處方或處置重複開立, 請重新輸入.</b></font>',
                '處方或處置重複輸入.'
            )
            in_table_widget.removeRow(in_table_widget.currentRow())
            exists = True
            break

    return exists


# 新增加強照護醫令
def insert_ins_care_item(database, case_key, case_date, ins_code):
    sql = '''
            SELECT * FROM prescript 
            WHERE
                (CaseKey = {0}) AND (MedicineSet = 11) AND
                (MedicineType IN ("照護"))
            ORDER BY PrescriptNo, PrescriptKey
        '''.format(case_key)

    rows = database.select_record(sql)
    if len(rows) > 0:
        return

    sql = '''
            SELECT * FROM charge_settings
            WHERE
                ChargeType = "照護費" AND
                InsCode = "{0}"
        '''.format(ins_code)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return

    row = rows[0]

    fields = [
        'PrescriptNo', 'CaseKey', 'CaseDate', 'MedicineSet', 'MedicineType',
        'MedicineKey', 'MedicineName', 'InsCode', 'Price', 'Dosage', 'Unit', 'Amount',
    ]
    data = [
        '1',
        string_utils.xstr(case_key),
        string_utils.xstr(case_date),
        '11',
        '照護',
        string_utils.xstr(row['ChargeSettingsKey']),
        string_utils.xstr(row['ItemName']),
        string_utils.xstr(row['InsCode']),
        string_utils.xstr(row['Amount']),
        '1',
        '次',
        string_utils.xstr(row['Amount']),
    ]

    database.insert_record('prescript', fields, data)

