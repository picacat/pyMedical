
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from libs import system_utils
from libs import string_utils


PRESCRIPT_COL_NO = {
    'PrescriptKey': 0,
    'PrescriptNo': 1,
    'CaseKey': 2,
    'CaseDate': 3,
    'MedicineSet': 4,
    'MedicineType': 5,
    'MedicineKey': 6,
    'InsCode': 7,
    'DosageMode': 8,
}


INS_PRESCRIPT_COL_NO = {
    **PRESCRIPT_COL_NO,
    'BackupMedicineName': 9,
    'MedicineName': 10,
    'Dosage': 11,
    'Unit': 12,
    'Instruction': 13,
}


SELF_PRESCRIPT_COL_NO = {
    **PRESCRIPT_COL_NO,
    'BackupMedicineName': 9,
    'MedicineName': 10,
    'Dosage': 11,
    'Unit': 12,
    'Instruction': 13,
    'Price': 14,
    'Amount': 15,
}

INS_TREAT_COL_NO = {
    'PrescriptKey': 0,
    'CaseKey': 1,
    'CaseDate': 2,
    'MedicineSet': 3,
    'MedicineType': 4,
    'MedicineKey': 5,
    'InsCode': 6,
    'BackupMedicineName': 7,
    'MedicineName': 8,
}

PRESCRIPT_TREAT = ['穴道', '處置']

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

# 檢查是否重複開立處方
def check_prescript_duplicates(in_table_widget, medicine_type, col_no, check_value):
    exists = False

    if check_value == '':  # 特殊處方或處置不檢查 (波形, 頻率, 時間)
        return exists

    row_count = in_table_widget.rowCount()
    field_value = None
    for row_no in range(row_count):
        field = in_table_widget.item(row_no, col_no)
        if field is not None:
            field_value = field.text()

        if check_value == field_value:
            row_no = in_table_widget.currentRow()

            if medicine_type in PRESCRIPT_TREAT:
                backup_medicine_name = INS_TREAT_COL_NO['BackupMedicineName']
                medicine_name = INS_TREAT_COL_NO['MedicineName']
            else:
                backup_medicine_name = INS_PRESCRIPT_COL_NO['BackupMedicineName']
                medicine_name = INS_PRESCRIPT_COL_NO['MedicineName']

            previous_medicine_item = in_table_widget.item(row_no, backup_medicine_name)

            in_table_widget.setItem(
                row_no, medicine_name,
                QtWidgets.QTableWidgetItem(previous_medicine_item)
            )

            system_utils.show_message_box(
                QMessageBox.Critical,
                '重複處方或處置',
                '<font size="4" color="red"><b>處方或處置重複開立, 請重新輸入.</b></font>',
                '處方或處置重複輸入.'
            )
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


# 解開成方
'''
prescript_row = [
    [0, '-1'],
    [1, string_utils.xstr(self.ui.tableWidget_prescript.currentRow() + 1)],
    [2, string_utils.xstr(self.case_key)],
    [3, string_utils.xstr(self.case_date)],
    [4, string_utils.xstr(self.medicine_set)],
    [5, string_utils.xstr(row['MedicineType'])],
    [6, string_utils.xstr(row['MedicineKey'])],
    [7, string_utils.xstr(row['InsCode'])],
    [8, self.system_settings.field('劑量模式')],
    [9, string_utils.xstr(row['MedicineName'])],
    [10, string_utils.xstr(dosage)],
    [11, string_utils.xstr(row['Unit'])],
    [12, None],
]

'''
def extract_compound(database, prescript_row, table_widget_prescript, table_widget_treat=None):
    medicine_key = prescript_row[6][1]
    sql = '''
        SELECT * FROM refcompound
        WHERE
            CompoundKey = {0}
        ORDER BY RefCompoundKey
    '''.format(medicine_key)

    compound_rows = database.select_record(sql)
    if len(compound_rows) <= 0:
        return

    for compound_row in compound_rows:
        medicine_key = string_utils.xstr(compound_row['MedicineKey'])
        if medicine_key == '':
            return


