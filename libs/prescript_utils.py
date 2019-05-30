
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from libs import system_utils
from libs import string_utils
from libs import number_utils


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
    'Info': 14,
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
    'Info': 16,
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
    if instruction is None:
        return 'PC'

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


def get_medicine_description(database, medicine_key):
    if medicine_key == '':
        return None

    sql = '''
        SELECT Description FROM medicine
        WHERE
            MedicineKey = {medicine_key}
    '''.format(medicine_key=medicine_key)
    medicine_row = database.select_record(sql)

    if len(medicine_row) <= 0:
        return None

    try:
        description = string_utils.get_str(medicine_row[0]['Description'], 'utf8')
    except TypeError:
        return None

    if description is not None and description.strip() == '':
        return None

    return description


def get_costs_html(database, table_widget, pres_days, prescript_col_dict):
    prescript_record = ''
    sequence = 0
    day_cost, total_costs = 0, 0
    for row_no in range(table_widget.rowCount()):
        item = table_widget.item(row_no, prescript_col_dict['MedicineName']
        )
        if item is None:
            continue

        medicine_name = item.text()

        item = table_widget.item(row_no, prescript_col_dict['Dosage']
        )
        if item is None:
            continue

        dosage = number_utils.get_float(item.text())

        item = table_widget.item(row_no, prescript_col_dict['MedicineKey']
        )
        if item is None:
            medicine_key = item
        else:
            medicine_key = item.text()

        item = table_widget.item(row_no, prescript_col_dict['Unit']
        )
        if item is not None:
            unit = item.text()
        else:
            unit = ''

        cost = 0
        if medicine_key is not None:
            sql = 'SELECT InPrice FROM medicine WHERE MedicineKey = {0}'.format(medicine_key)
            rows = database.select_record(sql)
            if len(rows) > 0:
                cost = number_utils.get_float(rows[0]['InPrice'])

        sequence += 1

        prescript_record += '''
                <tr>
                    <td align="center" style="padding-right: 8px;">{0}</td>
                    <td style="padding-left: 8px;">{1}</td>
                    <td align="right" style="padding-right: 8px">{2}</td>
                    <td align="right" style="padding-right: 8px">{3} {4}</td>
                    <td align="right" style="padding-right: 8px">{5:.1f}</td>
                </tr>
            '''.format(
            string_utils.xstr(sequence),
            string_utils.xstr(medicine_name),
            cost,
            dosage,
            unit,
            dosage * cost,
            )

        day_cost += dosage * cost

    prescript_record += '''
            <tr>
                <td align="center" style="padding-right: 8px;"></td>
                <td style="padding-left: 8px;">單日成本</td>
                <td align="right" style="padding-right: 8px"></td>
                <td align="right" style="padding-right: 8px"></td>
                <td align="right" style="padding-right: 8px">{day_cost:.1f}</td>
            </tr>
            <tr>
                <td align="center" style="padding-right: 8px;"></td>
                <td style="padding-left: 8px;">{pres_days}日藥總成本</td>
                <td align="right" style="padding-right: 8px"></td>
                <td align="right" style="padding-right: 8px"></td>
                <td align="right" style="padding-right: 8px">{total_costs:.1f}</td>
            </tr>
        '''.format(
        day_cost=day_cost,
        pres_days=pres_days,
        total_costs=pres_days * day_cost
    )

    prescript_data = '''
            <table align=center cellpadding="2" cellspacing="0" width="98%" style="border-width: 1px; border-style: solid;">
                <thead>
                    <tr bgcolor="LightGray">
                        <th style="text-align: center; padding-left: 8px" width="5%">序</th>
                        <th style="padding-left: 8px" width="50%" align="left">藥品名稱</th>
                        <th style="padding-right: 8px" align="right" width="15%">進價</th>
                        <th style="padding-right: 8px" align="right" width="15%">數量</th>
                        <th style="padding-right: 8px" align="right" width="15%">成本小計</th>
                    </tr>
                </thead>
                <tbody>
                    {0}
                </tbody>
            </table>
            <br>
        '''.format(prescript_record)

    html = '''
            <html>
                <head>
                    <meta charset="UTF-8">
                </head>
                <body>
                    <center><h4>用藥成本</h4></center>
                    {0}
                </body>
            </html>
        '''.format(
        prescript_data,
    )

    return html


def get_max_medicine_set(database, case_key):
    max_medicine_set = None

    sql = '''
        SELECT MedicineSet FROM prescript 
        WHERE 
            CaseKey = {0} AND
            MedicineSet >= 2
        GROUP BY MedicineSet
        ORDER BY MedicineSet DESC LIMIT 1
    '''.format(case_key)
    rows = database.select_record(sql)
    if len(rows) > 0:
        max_medicine_set = number_utils.get_integer(rows[0]['MedicineSet'])

    return max_medicine_set


