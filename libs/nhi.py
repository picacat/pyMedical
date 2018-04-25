# 2018.01.23

from libs import number

INS_TYPE = ['健保', '自費']
APPLY_TYPE = ['申報', '不申報']
VISIT = ['複診', '初診']
REG_TYPE = ['一般門診', '預約門診', '夜間急診']
INJURY_TYPE = ['普通疾病', '職業傷害', '職業病']
SHARE_TYPE = ['基層醫療', '榮民', '低收入戶', '重大傷病', '職業傷害', '三歲兒童',
              '山地離島', '其他免部份負擔', '新生兒', '愛滋病', '替代役男']
TREAT_TYPE = ['內科', '針灸治療', '傷科治療', '脫臼整復', '複雜性針灸', '複雜性傷科', '加強照護']
CHARGE_TYPE = ['診察費', '藥費', '調劑費', '處置費', '檢驗費', '照護費']
COURSE_TYPE = ['首次', '療程']
CARD = ['自動取得',
        '欠卡',
        'A000 讀卡設備故障',
        'B000 卡片不良',
        '不需取得']
COURSE = [None, '1', '2', '3', '4', '5', '6']
ROOM = ['1', '2', '3', '5', '6', '7', '8', '9', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20']
PERIOD = ['早班', '午班', '晚班']
GENDER = [None, '男', '女']
NATIONALITY = [None, '本國', '外國', '居留證', '遊民']
MARRIAGE = [None, '未婚', '已婚']
EDUCATION = [None, '國小', '國中', '高中', '大專', '碩士', '博士', '其他']
OCCUPATION = [None, '工', '商', '農漁業', '軍公教', '自由業', '服務業', '其他']
DISCOUNT = [None, '員工', '眷屬', '親友', '殘障', '僧侶', '教友', '老人', '榮民', '福保']
DIVISION = ['台北業務組', '北區業務組', '中區業務組', '南區業務組', '高屏業務組', '東區業務組']


def get_share_type(share_type):
    if share_type == '健保':
        share_type = '基層醫療'

    return share_type


# 取得療程類別
def get_course_type(course):
    if 2 <= number.get_integer(course) <= 6:
        course_type = '療程'
    else:
        course_type = '首次'

    return course_type
