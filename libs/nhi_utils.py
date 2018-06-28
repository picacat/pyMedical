# 2018.01.23

from libs import number

INS_TYPE = ['健保', '自費']
APPLY_TYPE = ['申報', '不申報']
VISIT = ['複診', '初診']
REG_TYPE = ['一般門診', '預約門診', '夜間急診']
INJURY_TYPE = ['普通疾病', '職業傷害', '職業病']
INSURED_TYPE = ['基層醫療', '榮民', '低收入戶']
SHARE_TYPE = [
    '基層醫療', '榮民', '低收入戶', '重大傷病', '職業傷害', '三歲兒童',
    '山地離島', '其他免部份負擔', '新生兒', '愛滋病', '替代役男', '天然災害',
]
AGENT_SHARE = [
    '榮民', '低收入戶', '職業傷害', '三歲兒童',
    '新生兒', '愛滋病', '替代役男', '天然災害',
]

TREAT_TYPE = [
    '內科', '針灸治療', '電針治療', '複雜性針灸', '傷科治療', '複雜性傷科',
    '脫臼復位', '脫臼整復首次', '脫臼整復',
    '小兒氣喘', '小兒腦性麻痺', '腦血管疾病', '癌症照護', '助孕照護', '保胎照護', '兒童鼻炎',
]
INS_TREAT = [
    '針灸治療', '電針治療', '複雜性針灸', '傷科治療', '複雜性傷科',
    '脫臼復位', '脫臼整復首次', '脫臼整復',
]
ACUPUNCTURE_TREAT = ['針灸治療', '電針治療', '複雜性針灸',]
MASSAGE_TREAT = ['傷科治療', '複雜性傷科',]
DISLOCATE_TREAT = ['脫臼復位', '脫臼整復首次', '脫臼整復',]
CARE_TREAT = [
    '小兒氣喘(氣霧處置)', '小兒氣喘',
    '小兒腦性麻痺(藥浴處置)', '小兒腦性麻痺',
    '腦血管疾病', '癌症照護',
    '助孕照護', '保胎照護', '兒童鼻炎',
]
ACUPUNCTURE_DRUG_DICT = {
    '針灸治療': 'B41',
    '電針治療': 'B43',
    '複雜性針灸': 'B45',
}
ACUPUNCTURE_DICT = {
    '針灸治療': 'B42',
    '電針治療': 'B44',
    '複雜性針灸': 'B46',
}
MASSAGE_DRUG_DICT = {
    '傷科治療': 'B53',
    '複雜性傷科': 'B55',
}
MASSAGE_DICT = {
    '傷科治療': 'B54',
    '複雜性傷科': 'B56',
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


CHARGE_TYPE = ['診察費', '藥費', '調劑費', '處置費', '檢驗費', '照護費']
COURSE_TYPE = ['首次', '療程']
CARD = [
    '自動取得',
    '欠卡',
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
    '不須取得',
]
ABNORMAL_CARD = [
    'A010', 'A020', 'A030',
    'B000',
    'C000', 'C001', 'C002', 'C003',
    'D000', 'D010',
    'E000', 'E001',
    'F000',
    'G000',
    'Z000',
    'H000',
]
COURSE = [None, '1', '2', '3', '4', '5', '6']
ROOM = ['1', '2', '3', '5', '6', '7', '8', '9', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20']
PERIOD = ['早班', '午班', '晚班']
POSITION = [None, '院長', '主任', '醫師', '支援醫師', '藥師', '護士', '職員', '理療師']
FULLTIME = [None, '全職', '兼職']
GENDER = [None, '男', '女']
NATIONALITY = [None, '本國', '外國', '居留證', '遊民']
MARRIAGE = [None, '未婚', '已婚']
EDUCATION = [None, '國小', '國中', '高中', '大專', '碩士', '博士', '其他']
OCCUPATION = [None, '工', '商', '農漁業', '軍公教', '自由業', '服務業', '其他']
DISCOUNT = [None, '員工', '眷屬', '親友', '殘障', '僧侶', '教友', '老人', '榮民', '福保']
DIVISION = ['台北業務組', '北區業務組', '中區業務組', '南區業務組', '高屏業務組', '東區業務組']
PACKAGE = [None, '1', '2', '3', '4', '5', '6']
PRESDAYS = [None, '3', '4', '5', '6', '7', '10', '14', '21', '28', '30']
INSTRUCTION = [None, '飯前', '飯後', '飯後睡前']


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
    if 2 <= number.get_integer(course) <= 6:
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
