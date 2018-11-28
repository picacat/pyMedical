# 2018.01.23C

import datetime
from libs import number_utils
from libs import string_utils
from libs import case_utils
from libs import personnel_utils
from libs import charge_utils

XML_OUT_PATH = './nhi_upload'
EMR_OUT_PATH = './emr'
MAX_DIAG_DAYS = 26  # 合理門診量最大日期
APPLY_TYPE_CODE = {
    '申報': '1',
    '補報': '2',
}

MAX_COURSE = 6  # 療程次數

MAX_TREAT_DRUG = 120  # 針傷給藥限量
TREAT_DRUG_CODE = ['B41', 'B43', 'B45', 'B53', 'B62', 'B80', 'B85', 'B90']  # 針傷給藥代碼
TREAT_CODE = ['B42', 'B44', 'B46', 'B54', 'B61', 'B63', 'B81', 'B86', 'B91']  # 針傷未開藥代碼
TREAT_ALL_CODE = [   # 所有針傷處置代碼
    'B41', 'B42', 'B43', 'B44', 'B45', 'B46',
    'B53', 'B54', 'B55', 'B56', 'B57',
    'B61', 'B62', 'B63',
    'B80', 'B81', 'B82', 'B83', 'B84', 'B85', 'B85', 'B86', 'B87', 'B88', 'B89',
    'B90', 'B91', 'B92', 'B93', 'B94',
]

MAX_COMPLICATED_TREAT = 30
COMPLICATED_TREAT_CODE = [
    'B55', 'B56', 'B57',
    'B82', 'B83', 'B84', 'B87', 'B88', 'B89',
    'B92', 'B93', 'B94',
]

PHARMACY_TYPE_DICT = {
    '0': '自行調劑',
    '1': '交付調劑',
    '2': '未開處方',
}

EXCLUDE_DIAG_ADJUST = ['22', '25', '30', 'B6']

DIAG_SECTION1 = 30  # 合理門診量第一段
DIAG_SECTION2 = 50
DIAG_SECTION3 = 70
DIAG_SECTION4 = 150

TREAT_SECTION1 = 30  # 針傷合理量第一段
TREAT_SECTION2 = 45

INS_CLASS = '60'  # 60-中醫科
INS_TYPE = ['健保', '自費']
APPLY_TYPE = ['申報', '不申報', '補報']
VISIT = ['複診', '初診']
REG_TYPE = ['一般門診', '預約門診', '夜間急診']
GENERAL_INJURY_TYPE = ['普通疾病']

OCCUPATIONAL_INJURY_TYPE = ['職業傷害', '職業病']
OCCUPATIONAL_INJURY_CARD = 'IC06'

INJURY_TYPE = GENERAL_INJURY_TYPE + OCCUPATIONAL_INJURY_TYPE
INSURED_TYPE = ['基層醫療', '榮民', '低收入戶']
SHARE_TYPE = INSURED_TYPE + [
    '重大傷病', '職業傷害', '三歲兒童',
    '山地離島', '其他免部份負擔', '新生兒', '愛滋病', '替代役男', '天然災害',
]
AGENT_SHARE = [
    '榮民', '低收入戶', '職業傷害', '三歲兒童',
    '新生兒', '愛滋病', '替代役男', '天然災害',
]

ACUPUNCTURE_TREAT = ['針灸治療', '電針治療', '複雜針灸',]
MASSAGE_TREAT = ['傷科治療', '複雜傷科',]
DISLOCATE_TREAT = ['脫臼復位', '脫臼整復首次', '脫臼整復',]
INS_TREAT = ACUPUNCTURE_TREAT + MASSAGE_TREAT + DISLOCATE_TREAT

# 案件分類: 30
AUXILIARY_CARE_TREAT = [
    '小兒氣喘', '小兒腦性麻痺',
    '腦血管疾病',
]

# 案件分類: 22
IMPROVE_CARE_TREAT = [
    '助孕照護', '保胎照護',
    '乳癌照護', '肝癌照護',
    '兒童鼻炎',
]

CARE_TREAT = AUXILIARY_CARE_TREAT + IMPROVE_CARE_TREAT

SPECIAL_CODE_DICT = {
    '助孕照護': 'J9',
    '保胎照護': 'J9',
    '乳癌照護': 'JE',
    '肝癌照護': 'JF',
    '兒童鼻炎': 'JG',
}

INS_TREAT_WITH_CARE = INS_TREAT + CARE_TREAT
TREAT_TYPE = ['內科'] + INS_TREAT_WITH_CARE + ['自購']

APPLY_TYPE_DICT = {
    '申報': '1',
    '補報': '2',
}

APPLY_TYPE_NAME_DICT = {
    '1': '申報',
    '2': '補報',
}

INJURY_DICT = {
    '職業傷害': '1',
    '職業病': '2',
    '普通傷害': '3',
    '普通疾病': '4',
}

ACUPUNCTURE_DRUG_DICT = {
    '針灸治療': 'B41',
    '電針治療': 'B43',
    '複雜針灸': 'B45',
}
ACUPUNCTURE_DICT = {
    '針灸治療': 'B42',
    '電針治療': 'B44',
    '複雜針灸': 'B46',
}
MASSAGE_DRUG_DICT = {
    '傷科治療': 'B53',
    '複雜傷科': 'B55',
}
MASSAGE_DICT = {
    '傷科治療': 'B54',
    '複雜傷科': 'B56',
}
DISLOCATE_DRUG_DICT = {
    '脫臼復位': 'B57',
    '脫臼整復首次': 'B61',
    '脫臼整復': 'B62',
}
DISLOCATE_DICT = {
    '脫臼復位': 'B57',
    '脫臼整復首次': 'B61',
    '脫臼整復': 'B63',
}
CARE_DICT = {
    '小兒氣喘(氣霧處置)': 'C01',
    '小兒氣喘': 'C02',
    '小兒腦性麻痺(藥浴處置)': 'C03',
    '小兒腦性麻痺': 'C04',
    '腦血管疾病': 'C05',
}

TREAT_DICT = {
    **ACUPUNCTURE_DRUG_DICT,
    **ACUPUNCTURE_DICT,
    **MASSAGE_DRUG_DICT,
    **MASSAGE_DICT,
    **DISLOCATE_DRUG_DICT,
    **DISLOCATE_DICT,
    **CARE_DICT,
}

TREAT_NAME_DICT = {
    'B41': '針灸治療',
    'B42': '針灸治療',
    'B43': '電針治療',
    'B44': '電針治療',
    'B45': '複雜針灸',
    'B46': '複雜針灸',
    'B53': '傷科治療',
    'B54': '傷科治療',
    'B55': '複雜傷科',
    'B56': '複雜傷科',
    'B61': '脫臼整復首次',
    'B62': '脫臼整復',
    'B63': '脫臼整復',
}

FREQUENCY = {
    1: 'QD',
    2: 'BID',
    3: 'TID',
    4: 'QID',
    5: 'PID',
    6: 'Q4H',
    7: 'Q4H',
    8: 'Q3H',
}

USAGE = {
    '飯前': 'AC',
    '飯後': 'PC',
    '飯後睡前': 'PC',
}

CHARGE_TYPE = ['診察費', '藥費', '調劑費', '處置費', '檢驗費', '照護費']
COURSE_TYPE = ['首次', '療程']
ABNORMAL_CARD_WITH_HINT = [
    'A010 讀卡機設備故障',
    'A020 網路故障',
    'A030 讀卡機安全模組故障',
    'B000 健保卡讀取不良',
    'C000 停電',
    'C001 例外就醫',
    'C002 18歲以下兒少',
    'C003 弱勢民眾安心就醫',
    'D000 醫療軟體系統當機',
    'D010 醫療院所電腦當機',
    'E000 健保暑資訊系統當機',
    'E001 控卡名單已簽切結書',
    'F000 巡迴醫療無法上網',
    'G000 新特約醫事機構',
    'Z000 其他',
    'H000 高齡醫師',
]
ABNORMAL_CARD = [
    ABNORMAL_CARD_WITH_HINT[i].split(' ')[0] for i in range(len(ABNORMAL_CARD_WITH_HINT))
]
ABNORMAL_CARD_DICT = {
    ABNORMAL_CARD_WITH_HINT[i].split(' ')[0]: ABNORMAL_CARD_WITH_HINT[i]
    for i in range(len(ABNORMAL_CARD_WITH_HINT))
}
CARD = ['自動取得', '不須取得', '欠卡'] + ABNORMAL_CARD_WITH_HINT

COURSE = ['1', '2', '3', '4', '5', '6']
ROOM = ['1', '2', '3', '5', '6', '7', '8', '9', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20']
PERIOD = ['早班', '午班', '晚班']
POSITION = ['院長', '主任', '醫師', '支援醫師', '藥師', '護士', '職員', '推拿師父']
FULLTIME = ['全職', '兼職']
GENDER = ['男', '女']
NATIONALITY = ['本國', '外國', '居留證', '遊民']
MARRIAGE = ['未婚', '已婚']
EDUCATION = ['國小', '國中', '高中', '大專', '碩士', '博士', '其他']
OCCUPATION = ['工', '商', '農漁業', '軍公教', '自由業', '服務業', '其他']
DISCOUNT = ['員工', '眷屬', '親友', '殘障', '僧侶', '教友', '老人', '榮民', '福保']
DIVISION = ['台北業務組', '北區業務組', '中區業務組', '南區業務組', '高屏業務組', '東區業務組']
PACKAGE = ['1', '2', '3', '4', '5', '6']
PRESDAYS = ['3', '4', '5', '6', '7', '10', '14', '21', '28', '30']
INSTRUCTION = ['飯前', '飯後', '飯後睡前']


# 取得負擔類別
def get_share_type(share_type):
    if share_type == '健保':
        share_type = '基層醫療'

    return share_type


# 取得就醫類別
def get_treat_type(treatment):
    treat_type = '內科'
    if treatment in ACUPUNCTURE_TREAT:
        treat_type = '針灸治療'
    elif treatment in MASSAGE_TREAT:
        treat_type = '傷科治療'

    return treat_type


# 取得療程類別
def get_course_type(course):
    if 2 <= number_utils.get_integer(course) <= 6:
        course_type = '療程'
    else:
        course_type = '首次'

    return course_type


# 取得藥品類別
def get_medicine_type(database, medicine_type):
    sql = 'select * from dict_groups where DictGroupsType = "{0}"'.format(medicine_type)
    rows = database.select_record(sql)
    medicine_groups = []
    for row in rows:
        medicine_groups.append(row['DictGroupsName'])

    return medicine_groups


def get_treat_code(database, case_key):
    sql = '''
            SELECT * FROM dosage WHERE
            CaseKey = {0}
        '''.format(case_key)
    rows = database.select_record(sql)
    dosage_row = rows[0] if len(rows) > 0 else None
    if dosage_row is not None:
        pres_days = number_utils.get_integer(dosage_row['Days'])
    else:
        pres_days = 0

    sql = '''
            SELECT Treatment FROM cases WHERE
            CaseKey = {0}
        '''.format(case_key)
    row = database.select_record(sql)[0]
    treatment = string_utils.xstr(row['Treatment'])

    treat_code = None
    if treatment in ACUPUNCTURE_TREAT:
        if pres_days > 0:
            treat_code = ACUPUNCTURE_DRUG_DICT[treatment]
        else:
            treat_code = ACUPUNCTURE_DICT[treatment]
    elif treatment in MASSAGE_TREAT:
        if pres_days > 0:
            treat_code = MASSAGE_DRUG_DICT[treatment]
        else:
            treat_code = MASSAGE_DICT[treatment]
    elif treatment in DISLOCATE_TREAT:
        if pres_days > 0:
            treat_code = DISLOCATE_DRUG_DICT[treatment]
        else:
            treat_code = DISLOCATE_DICT[treatment]
    elif treatment in CARE_TREAT:
            treat_code = CARE_DICT[treatment]

    return treat_code


def get_case_type(database, row):
    injury = string_utils.xstr(row['Injury'])
    treat_type = string_utils.xstr(row['TreatType'])
    course = number_utils.get_integer(row['Continuance'])
    special_code = string_utils.xstr(row['SpecialCode'])
    treatment = string_utils.xstr(row['Treatment'])
    pres_days = case_utils.get_pres_days(database, row['CaseKey'])

    if treat_type in IMPROVE_CARE_TREAT:  # 加強照護
        case_type = '22'
    elif treat_type in AUXILIARY_CARE_TREAT:  # 輔助照護
        case_type = '30'
    elif injury in OCCUPATIONAL_INJURY_TYPE:  # 職業傷害及職業病
        case_type = 'B6'
    elif course >= 1 and treatment in INS_TREAT:  # 一般針傷脫臼處置
        case_type = '29'
    elif (course == 0 and pres_days > 7) or (special_code != ''):  # 慢性病專案
        case_type = '24'
    else:
        case_type = '21'  # 預設為21

    return case_type


# 取得門診負擔 (treat_type 取代 treatment的原因: 掛號時須取得門診負擔, 以treat_type代表)
def get_diag_share_code(database, share_type, treatment, course, case_row=None):
    diag_share_code = ''
    course_type = get_course_type(course)

    if treatment in ACUPUNCTURE_TREAT:
        treatment = '針灸治療'
    elif treatment in MASSAGE_TREAT:
        treatment = '傷科治療'
    else:
        treatment = '內科'

    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "門診負擔" AND 
            ShareType = "{0}" AND TreatType = "{1}" AND Course = "{2}"
    '''.format(share_type, treatment, course_type)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return diag_share_code

    if len(row) > 0:
        diag_share_code = string_utils.xstr(row['InsCode'])

    if case_row is not None:
        if number_utils.get_integer(case_row['DrugShareFee']) > 0:
            diag_share_code = 'S20'
        elif (number_utils.get_integer(case_row['DiagShareFee']) > 0 and course >= 2):
            diag_share_code = 'S20'

    return diag_share_code


# 取得專案代碼
def get_special_code(database, case_key):
    special_code_list = []
    sql = '''
            SELECT TreatType, Treatment, SpecialCode FROM cases WHERE
            CaseKey = {0}
        '''.format(case_key)
    row = database.select_record(sql)[0]
    treat_type = string_utils.xstr(row['TreatType'])
    treatment = string_utils.xstr(row['Treatment'])
    special_code = string_utils.xstr(row['SpecialCode'])
    # 先檢查特定照護
    if treat_type in AUXILIARY_CARE_TREAT:  # 腦血管疾病
        return [None, None, None, None]

    if treat_type in IMPROVE_CARE_TREAT:
        special_code_list.append(SPECIAL_CODE_DICT[treat_type])
        special_code_list = special_code_list + [None] * (4 - len(special_code_list))
        return  special_code_list

    if treat_type == '長期臥床':
        special_code_list.append('J1')
    elif treat_type == '遠洋漁業':
        special_code_list.append('J2')
    elif treat_type == '遠洋貨船':
        special_code_list.append('J3')

    if special_code != '':
        special_code_list.append(special_code)

    if treatment in ACUPUNCTURE_TREAT:
        special_code_list.append('C3')
    elif treatment in MASSAGE_TREAT:
        special_code_list.append('C4')
    elif treatment in DISLOCATE_TREAT:
        special_code_list.append('C5')

    special_code_list = special_code_list + [None] * (4 - len(special_code_list))
    return special_code_list


# 取得初診照護
def get_visit(database, row):
    if string_utils.xstr(row['TreatType']) in AUXILIARY_CARE_TREAT:  # 腦血管疾病, 小兒氣喘, 小兒腦麻不可申報其他項目
        return None

    if string_utils.xstr(row['Visit']) == '初診':
        return '初診照護'

    visit_year = 2  # 2年內無看診
    first_visit_year_range = row['CaseDate'].replace(year=row['CaseDate'].year - visit_year)

    sql = '''
        SELECT CaseKey FROM cases
        WHERE
            InsType = "健保" AND
            CaseKey = {0} AND
            CaseDate > "{1}"
    '''.format(row['CaseKey'], first_visit_year_range)
    rows = database.select_record(sql)
    if len(rows) <= 0:  # 2年內無看診
        return '初診照護'

    return None


# 調劑方式: 0-自行調劑 1-交付調劑 2-未開處方
def get_pres_type(pres_days):
    pres_type = 2
    if pres_days > 0:
        pres_type = 0

    return pres_type


def get_pharmacist_id(database, system_settings, row):
    pres_days = case_utils.get_pres_days(database, row['CaseKey'])

    if pres_days <= 0:
        return None

    if string_utils.xstr(row['PharmacyType']) != '申報':
        return None


    if number_utils.get_integer(row['PharmacyFee']) <= 0:
        return None

    pharmacist_name = string_utils.xstr(row['Pharmacist'])
    if pharmacist_name == '':
        pharmacist_name = string_utils.xstr(row['Doctor'])

    pharmacist_id = personnel_utils.get_personnel_id(database, pharmacist_name)

    return pharmacist_id


def get_diag_code(database, system_settings, doctor_name, treat_type, diag_fee):
    diag_code = None

    if diag_fee <= 0:
        return diag_code

    if treat_type in CARE_TREAT and treat_type != '兒童鼻炎':  # 兒童過敏性鼻炎可申報診察費
        return diag_code

    nurse = number_utils.get_integer(system_settings.field('護士人數'))
    if nurse > 0:
        diag_code = 'A01'  # 診察費第一段有護士
    else:
        diag_code = 'A02'  # 診察費第一段無護士

    position = personnel_utils.get_personnel_position(database, doctor_name)
    if position == '支援醫師':
        diag_code = 'A02'

    return diag_code


# 藥服代號: A31-A32;  6次: 120010: 0-無調劑 1-A31藥師 2-A32醫師
def get_pharmacy_code(system_settings, row, pres_days, pharmacy_code='000000'):
    if string_utils.xstr(row['TreatType']) in IMPROVE_CARE_TREAT:  # 加強照護不可申報調劑費
        return pharmacy_code

    pharmacy_code = [x for x in pharmacy_code]
    course = number_utils.get_integer(row['Continuance'])

    if course >= 1:
        course -= 1
    else:
        course = 0

    if pres_days <= 0:
        pharmacy_code[course] = '0'
    elif string_utils.xstr(row['PharmacyType']) == '申報':
        pharmacist = system_settings.field('藥師人數')
        if int(pharmacist) > 0:
            pharmacy_code[course] = '1'
        else:
            pharmacy_code[course] = '2'
    else:
        pharmacy_code[course] = '0'

    return ''.join(pharmacy_code)


def get_treat_records(database, row, ins_apply_row=None):
    if ins_apply_row is not None:
        treat_records = [
            {
                'CaseKey': number_utils.get_integer(ins_apply_row['CaseKey1']),
                'TreatCode': string_utils.xstr(ins_apply_row['TreatCode1']),
                'TreatFee': number_utils.get_integer(ins_apply_row['TreatFee1']),
                'Percent': number_utils.get_integer(ins_apply_row['Percent1'])},
            {
                'CaseKey': number_utils.get_integer(ins_apply_row['CaseKey2']),
                'TreatCode': string_utils.xstr(ins_apply_row['TreatCode2']),
                'TreatFee': number_utils.get_integer(ins_apply_row['TreatFee2']),
                'Percent': number_utils.get_integer(ins_apply_row['Percent2'])},
            {
                'CaseKey': number_utils.get_integer(ins_apply_row['CaseKey3']),
                'TreatCode': string_utils.xstr(ins_apply_row['TreatCode3']),
                'TreatFee': number_utils.get_integer(ins_apply_row['TreatFee3']),
                'Percent': number_utils.get_integer(ins_apply_row['Percent3'])},
            {
                'CaseKey': number_utils.get_integer(ins_apply_row['CaseKey4']),
                'TreatCode': string_utils.xstr(ins_apply_row['TreatCode4']),
                'TreatFee': number_utils.get_integer(ins_apply_row['TreatFee4']),
                'Percent': number_utils.get_integer(ins_apply_row['Percent4'])},
            {
                'CaseKey': number_utils.get_integer(ins_apply_row['CaseKey5']),
                'TreatCode': string_utils.xstr(ins_apply_row['TreatCode5']),
                'TreatFee': number_utils.get_integer(ins_apply_row['TreatFee5']),
                'Percent': number_utils.get_integer(ins_apply_row['Percent5'])},
            {
                'CaseKey': number_utils.get_integer(ins_apply_row['CaseKey6']),
                'TreatCode': string_utils.xstr(ins_apply_row['TreatCode6']),
                'TreatFee': number_utils.get_integer(ins_apply_row['TreatFee6']),
                'Percent': number_utils.get_integer(ins_apply_row['Percent6'])},
        ]
    else:
        treat_records = [
            {
                'CaseKey': 0,
                'TreatCode': None,
                'TreatFee': 0,
                'Percent': 100},
            {
                'CaseKey': 0,
                'TreatCode': None,
                'TreatFee': 0,
                'Percent': 100},
            {
                'CaseKey': 0,
                'TreatCode': None,
                'TreatFee': 0,
                'Percent': 100},
            {
                'CaseKey': 0,
                'TreatCode': None,
                'TreatFee': 0,
                'Percent': 100},
            {
                'CaseKey': 0,
                'TreatCode': None,
                'TreatFee': 0,
                'Percent': 100},
            {
                'CaseKey': 0,
                'TreatCode': None,
                'TreatFee': 0,
                'Percent': 100},
        ]

    if string_utils.xstr(row['TreatType']) == '腦血管疾病':
        if treat_records[0]['CaseKey'] == 0:
            treat_records[0]['CaseKey'] = number_utils.get_integer(row['CaseKey'])
            treat_records[1]['CaseKey'] = 1  # CaseKey2 = 腦血管疾病次數 redefine
        else:
            treat_records[1]['CaseKey'] += 1

        treat_records[0]['TreatCode'] = get_brain_treat_code(treat_records[1]['CaseKey'])
        treat_records[0]['TreatFee'] = charge_utils.get_ins_fee_from_ins_code(
            database, treat_records[0]['TreatCode']
        )

        return treat_records

    course = number_utils.get_integer(row['Continuance'])
    if course <= 1:
        course = 0
    else:
        course -= 1

    treat_records[course]['CaseKey'] = number_utils.get_integer(row['CaseKey'])
    treat_records[course]['TreatCode'] = get_treat_code(
        database,
        treat_records[course]['CaseKey']
    )

    if string_utils.xstr(row['TreatType']) in CARE_TREAT:  # 加強照護類不含脫臼費(redefine 照護費)
        treat_records[course]['TreatFee'] = (
                number_utils.get_integer(row['AcupunctureFee']) +
                number_utils.get_integer(row['MassageFee']))
    else:
        treat_records[course]['TreatFee'] = (
                number_utils.get_integer(row['AcupunctureFee']) +
                number_utils.get_integer(row['MassageFee']) +
                number_utils.get_integer(row['DislocateFee']))

    return treat_records


# 取得腦血管疾病醫令
def get_brain_treat_code(record_count):
    if record_count <= 3:
        treat_code = 'C05'
    elif record_count <= 6:
        treat_code = 'C06'
    elif record_count <= 9:
        treat_code = 'C07'
    elif record_count <= 12:
        treat_code = 'C08'
    else:
        treat_code = 'C09'

    return treat_code


# 取得療程開始日期
def get_start_date(database, row):
    case_date = row['CaseDate'].date()
    card = string_utils.xstr(row['Card'])
    last_month = datetime.date(case_date.year, case_date.month, 1) - datetime.timedelta(1)
    start_date = last_month.replace(day=1).strftime('%Y-%m-%d 00:00:00')
    if number_utils.get_integer(row['Continuance']) <= 1:
        return case_date

    sql = '''
        SELECT CaseDate FROM cases
        WHERE
            CaseDate BETWEEN "{0}" AND "{1}" AND
            Card = "{2}" AND
            Continuance <= 1
    '''.format(start_date, row['CaseDate'], card)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return case_date

    return rows[0]['CaseDate']


def nurse_schedule_on_duty(database, case_key, doctor_name):
    on_duty = False

    sql = '''
        SELECT CaseDate, Period 
        FROM cases
        WHERE 
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return on_duty

    case_date = rows[0]['CaseDate'].date()
    period = string_utils.xstr(rows[0]['Period'])

    sql = '''
        SELECT *
        FROM nurse_schedule
        WHERE
            ScheduleDate = "{0}" AND
            Doctor = "{1}"
    '''.format(case_date, doctor_name)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return on_duty

    if period == '早班':
        nurse = rows[0]['Nurse1']
    elif period == '午班':
        nurse = rows[0]['Nurse2']
    elif period == '晚班':
        nurse = rows[0]['Nurse3']

    if string_utils.xstr(nurse) != '':
        on_duty = True

    return on_duty

def get_ins_xml_file_name(apply_type, apply_date, prefix=None):
    xml_file_name = '{0}/{1}-{2}'.format(
        XML_OUT_PATH,
        apply_date,
        apply_type,
    )
    if prefix is not None:
        xml_file_name += '-{0}'.format(prefix)

    xml_file_name += '.xml'

    return xml_file_name

def get_apply_date(apply_year, apply_month):
    apply_date = '{0:0>3}{1:0>2}'.format(apply_year-1911, apply_month)

    return apply_date

def extract_pharmacy_code(pharmacy_code_str):
    pharmacy_count = 0
    pharmacy_code = ''
    for i in range(len(pharmacy_code_str)):
        if pharmacy_code_str[i] in ['1', '2']:
            pharmacy_code = 'A3{0}'.format(pharmacy_code_str[i])
            pharmacy_count += 1

        if pharmacy_count >= 2:
            pharmacy_code = ''
            break

    return pharmacy_code


def get_usage(instruction):
    if '飯前' in instruction:
        usage = 'AC'
    elif '飯後' in instruction:
        usage = 'PC'
    else:
        usage = 'PC'

    return usage

