

# 增加點擊率
def increment_hit_rate(database, table_name, primary_key_field, primary_key):
    if primary_key in [None, '']:
        return

    sql = '''
        UPDATE {table_name}
        SET
            HitRate = HitRate + 1
        WHERE
            {primary_key_field} = {primary_key}
    '''.format(
        table_name=table_name,
        primary_key_field=primary_key_field,
        primary_key=primary_key
    )

    database.exec_sql(sql)


def str_converter(field_value):
    import datetime

    if isinstance(field_value, datetime.datetime):
        field_value = field_value.__str__()
    elif isinstance(field_value, bytes):
        try:
            field_value = field_value.decode('utf8')
        except UnicodeDecodeError:
            field_value = field_value.decode('big5')
    else:
        field_value = field_value.__str__()

    return field_value


def mysql_to_json(rows):
    import json

    json_data = json.dumps(rows, indent=4, ensure_ascii=False, default=str_converter)

    return json_data


def set_default_data(database, table_name):
    if table_name == 'system_settings':
        set_system_settings_default_data(database)
    elif table_name == 'dict_groups':
        set_dict_groups_default_data(database)
    elif table_name == 'charge_settings':
        set_charge_settings_default_data(database)
    elif table_name == 'icd10':
        set_icd10_default_data(database)
    elif table_name == 'clinic':
        set_dict_diagnostic_default_data(database)
    elif table_name == 'medicine':
        set_dict_medicine_default_data(database)
    elif table_name == 'refcompound':
        set_dict_compound_default_data(database)


def set_system_settings_default_data(database):
    from classes import system_settings
    from libs import ui_utils

    _system_settings = system_settings.SystemSettings(database, ui_utils.CONFIG_FILE)
    _system_settings.post('院所名稱', '中醫診所')
    _system_settings.post('早班時間', '08:00')
    _system_settings.post('午班時間', '14:00')
    _system_settings.post('晚班時間', '18:00')
    _system_settings.post('早班起始號', '1')
    _system_settings.post('午班起始號', '1')
    _system_settings.post('晚班起始號', '1')
    _system_settings.post('外觀主題', 'Fusion')
    _system_settings.post('外觀顏色', '藍色')
    _system_settings.post('顯示側邊欄', 'Y')
    _system_settings.post('資源類別', '一般')
    _system_settings.post('預設門診類別', '健保')
    _system_settings.post('針灸認證合格', 'Y')
    _system_settings.post('針灸認證合格日期', '2019-01-01')
    _system_settings.post('現場掛號給號模式', '預約班表')
    _system_settings.post('針傷警告次數', '15')
    _system_settings.post('首次警告次數', '6')
    _system_settings.post('老人優待', 'Y')
    _system_settings.post('老人優待年齡', '65')


def set_dict_groups_default_data(database):
    from convert import cvt_groups

    cvt_groups.cvt_pymedical_groups(database)
    cvt_groups.cvt_pymedical_disease_groups(database)
    cvt_groups.cvt_disease_common(database)
    cvt_groups.cvt_disease_treat(database)

    set_dict_diagnostic_groups_default_data(database)


def set_charge_settings_default_data(database):
    from libs import charge_utils

    charge_utils.set_nhi_basic_data(database)
    charge_utils.set_diag_share_basic_data(database)
    charge_utils.set_drug_share_basic_data(database)
    charge_utils.set_discount_basic_data(database)
    charge_utils.set_regist_fee_basic_data(database)


def set_dict_diagnostic_default_data(database):
    from PyQt5 import QtWidgets, QtCore
    import json

    file_name = './mysql/default/diagnostic.json'
    field = [
        'ClinicType', 'ClinicCode', 'InputCode', 'ClinicName', 'Position', 'Groups',
    ]
    with open(file_name, encoding='utf8') as json_file:
        rows = json.load(json_file)
        row_count = len(rows)
        progress_dialog = QtWidgets.QProgressDialog(
            '正在產生診察詞庫檔中, 請稍後...', '取消', 0, row_count, None
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)
        for row_no, row in zip(range(row_count), rows):
            data = [
                row['ClinicType'], row['ClinicCode'], row['InputCode'], row['ClinicName'],
                row['Position'], row['Groups'],
            ]
            database.insert_record('clinic', field, data)
            progress_dialog.setValue(row_no)

        progress_dialog.setValue(row_count)


def set_dict_diagnostic_groups_default_data(database):
    from PyQt5 import QtWidgets, QtCore
    import json

    file_name = './mysql/default/diagnostic_groups.json'
    field = [
        'DictOrderNo', 'DictGroupsType', 'DictGroupsTopLevel', 'DictGroupsLevel2',
        'DictGroupsName',
    ]
    with open(file_name, encoding='utf8') as json_file:
        rows = json.load(json_file)
        row_count = len(rows)
        progress_dialog = QtWidgets.QProgressDialog(
            '正在產生診察詞庫類別檔中, 請稍後...', '取消', 0, row_count, None
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)
        for row_no, row in zip(range(row_count), rows):
            data = [
                row['DictOrderNo'], row['DictGroupsType'], row['DictGroupsTopLevel'], row['DictGroupsLevel2'],
                row['DictGroupsName'],
            ]
            database.insert_record('dict_groups', field, data)
            progress_dialog.setValue(row_no)

        progress_dialog.setValue(row_count)


def set_icd10_default_data(database):
    from PyQt5 import QtWidgets, QtCore
    import json

    file_name = './mysql/default/icd10.json'
    field = [
        'ICDCode', 'InputCode', 'ChineseName', 'EnglishName', 'SpecialCode', 'Groups',
    ]
    with open(file_name, encoding='utf8') as json_file:
        rows = json.load(json_file)
        row_count = len(rows)
        progress_dialog = QtWidgets.QProgressDialog(
            '正在產生ICD10病名檔中, 請稍後...', '取消', 0, row_count, None
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)
        for row_no, row in zip(range(row_count), rows):
            data = [
                row['ICDCode'], row['InputCode'], row['ChineseName'], row['EnglishName'],
                row['SpecialCode'], row['Groups'],
            ]
            database.insert_record('icd10', field, data)
            progress_dialog.setValue(row_no)

        progress_dialog.setValue(row_count)


def set_dict_medicine_default_data(database):
    from PyQt5 import QtWidgets, QtCore
    import json

    file_name = './mysql/default/medicine.json'
    field = [
        'MedicineKey',
        'MedicineType', 'MedicineMode', 'MedicineCode', 'InputCode', 'InsCode', 'MedicineName',
        'Unit', 'Description'
    ]
    with open(file_name, encoding='utf8') as json_file:
        rows = json.load(json_file)
        row_count = len(rows)
        progress_dialog = QtWidgets.QProgressDialog(
            '正在產生處方詞庫檔中, 請稍後...', '取消', 0, row_count, None
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)
        for row_no, row in zip(range(row_count), rows):
            data = [
                row['MedicineKey'],
                row['MedicineType'], row['MedicineMode'], row['MedicineCode'], row['InputCode'],
                row['InsCode'], row['MedicineName'], row['Unit'], row['Description'],
            ]
            database.insert_record('medicine', field, data)
            progress_dialog.setValue(row_no)

        progress_dialog.setValue(row_count)


def set_dict_compound_default_data(database):
    from PyQt5 import QtWidgets, QtCore
    import json

    file_name = './mysql/default/compound.json'
    field = [
        'CompoundKey', 'MedicineKey', 'Quantity', 'Unit',
    ]
    with open(file_name, encoding='utf8') as json_file:
        rows = json.load(json_file)
        row_count = len(rows)
        progress_dialog = QtWidgets.QProgressDialog(
            '正在產生成方詞庫檔中, 請稍後...', '取消', 0, row_count, None
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)
        for row_no, row in zip(range(row_count), rows):
            data = [
                row['CompoundKey'], row['MedicineKey'], row['Quantity'], row['Unit'],
            ]
            database.insert_record('refcompound', field, data)
            progress_dialog.setValue(row_no)

        progress_dialog.setValue(row_count)
