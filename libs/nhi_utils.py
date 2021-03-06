# 2018.01.23C

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox

from threading import Thread
from queue import Queue
import datetime
import os
import sys
import ctypes

from libs import number_utils
from libs import string_utils
from libs import date_utils
from libs import case_utils
from libs import personnel_utils
from libs import charge_utils
from libs import system_utils
from libs import dialog_utils
from libs import icd10_utils

MAX_DIAG_DAYS = 26  # 合理門診量最大日期
APPLY_TYPE_CODE = {
    '申報': '1',
    '補報': '2',
}
REMEDY_TYPE_CODE = {
    '補報整筆': '1',
    '補報差額': '2',
}
TREAT_ITEM = {
    '01': '西醫門診',
    '02': '牙醫門診',
    '03': '中醫門診',
    '04': '急診',
    '05': '住院',
    '06': '轉診',
    '07': '門診回診',
    '08': '住院回診',
    'AA': '療程',
    'AB': '療程',
    'AC': '預防保健',
    'AD': '職業傷害',
    'AE': '慢箋',
    'AF': '藥局調劑',
    'AG': '排程檢查',
    'AH': '居家照護',
    'AI': '同日看診',
    'BA': '急診住院',
    'BB': '出院',
    'BC': '急診住院中',
    'BD': '急診離院',
    'BE': '職傷住院',
    'CA': '其他',
    'DA': '門診轉出',
    'DB': '門診手術',
}
MAX_COURSE = 6  # 療程次數
MAX_TREAT_DRUG = 120  # 針傷給藥限量
TREAT_DRUG_CODE = ['B41', 'B43', 'B45', 'B53', 'B62', 'B80', 'B85', 'B90']  # 針傷給藥代碼
TREAT_CODE = ['B42', 'B44', 'B46', 'B54', 'B61', 'B63', 'B81', 'B86', 'B91']  # 針傷未開藥代碼
TREAT_ALL_CODE = [  # 所有針傷處置代碼
    'B41', 'B42', 'B43', 'B44', 'B45', 'B46',
    'B53', 'B54', 'B55', 'B56', 'B57',
    'B61', 'B62', 'B63',
    'B80', 'B81', 'B82', 'B83', 'B84', 'B85', 'B85', 'B86', 'B87', 'B88', 'B89',
    'B90', 'B91', 'B92', 'B93', 'B94',
]

MAX_COMPLICATED_TREAT = 60
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

REMEDY_TYPE = ['補報整筆', '補報差額']
APPLY_TYPE = ['申報', '不申報'] + REMEDY_TYPE

PHARMACY_APPLY_TYPE = ['申報', '不申報']
VISIT = ['複診', '初診']
TOUR_FAR = ['巡迴偏遠']
TOUR_MOUNTAIN_ISLAND = ['巡迴山地', '巡迴離島']
TOUR_TYPE = TOUR_FAR + TOUR_MOUNTAIN_ISLAND
REG_TYPE = ['一般門診', '預約門診', '夜間急診', ] + TOUR_TYPE
GENERAL_INJURY_TYPE = ['普通疾病']

OCCUPATIONAL_INJURY_TYPE = ['職業傷害', '職業病']
OCCUPATIONAL_INJURY_CARD = 'IC06'

INJURY_TYPE = GENERAL_INJURY_TYPE + OCCUPATIONAL_INJURY_TYPE
INSURED_TYPE = ['基層醫療', '榮民', '低收入戶', '災民']
SHARE_TYPE = INSURED_TYPE + [
    '重大傷病', '職業傷害', '三歲兒童',
    '山地離島', '其他免部份負擔', '新生兒', '愛滋病', '替代役男', '天然災害',
]
AGENT_SHARE = [
    '榮民', '低收入戶', '職業傷害', '三歲兒童',
    '新生兒', '愛滋病', '替代役男', '天然災害',
]

ACUPUNCTURE_TREAT = ['針灸治療', '電針治療', '複雜針灸', ]
MASSAGE_TREAT = ['傷科治療', '複雜傷科', ]
DISLOCATE_TREAT = ['脫臼復位', '脫臼整復首次', '脫臼整復', ]
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
    '肺癌照護', '大腸癌照護',
    '兒童鼻炎',
]

CARE_TREAT = AUXILIARY_CARE_TREAT + IMPROVE_CARE_TREAT

SPECIAL_CODE_DICT = {
    '助孕照護': 'J9',
    '保胎照護': 'J9',
    '乳癌照護': 'JE',
    '肝癌照護': 'JF',
    '兒童鼻炎': 'JG',
    '肺癌照護': 'JI',
    '大腸癌照護': 'JJ',
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
    'A010 讀卡機故障',
    'A020 網路故障',
    'A030 安全模組故障',
    'B000 健保卡讀取不良',
    'C000 停電',
    'C001 例外就醫',
    'C002 18歲以下兒少',
    'C003 弱勢民眾就醫',
    'D000 醫療軟體當機',
    'D010 醫療電腦當機',
    'E000 健保署系統當機',
    'E001 控卡名單已簽切結書',
    'F000 巡迴醫療無法上網',
    'G000 新特約醫事機構',
    'Z000 其他',
    'H000 高齡醫師',
]

RESOURCE_TYPE = [
    '一般',
    '資源不足巡迴醫療',
    '資源不足開業',
    '偏遠地區長期進駐',
]

TOUR_AREA_LEVEL = {
    '資源不足': [
        '新北市三芝區', '新北市金山區', '新北市萬里區', '新北市貢寮區', '新北市石碇區',
        '宜蘭縣蘇澳鎮', '宜蘭縣三星鄉',
        '新竹縣關西鎮', '新竹縣新埔鎮', '新竹縣芎林鄉',
        '苗栗縣卓蘭鎮', '苗栗縣銅鑼鄉', '苗栗縣三義鄉', '苗栗縣造橋鄉', '苗栗縣三灣鄉',
        '台中市石岡區',
        '彰化縣線西鄉', '彰化縣埔鹽鄉', '彰化縣二水鄉', '彰化縣田尾鄉', '彰化縣芳苑鄉', '彰化縣竹塘鄉',
        '南投縣集集鎮', '南投縣鹿谷鄉', '南投縣中寮鄉', '南投縣魚池鄉', '南投縣國姓鄉',
        '台南市柳營區', '台南市六甲區', '台南市西港區', '台南市七股區', '台南市將軍區', '台南市山上區', '台南市楠西區',
        '台南市南化區', '台南市官田區',
        '雲林縣口湖鄉', '雲林縣林內鄉', '雲林縣二崙鄉', '雲林縣褒忠鄉', '雲林縣元長鄉', '雲林縣四湖鄉',
        '嘉義縣東石鄉', '嘉義縣六腳鄉', '嘉義縣義竹鄉', '嘉義縣水上鄉', '嘉義縣梅山鄉', '嘉義縣大埔鄉',
        '高雄市湖內區', '高雄市梓官區', '高雄市六龜區', '高雄市杉林區', '高雄市永安區', '高雄市彌陀區', '高雄市甲仙區',
        '高雄市內門區',
        '屏東縣恆春鎮', '屏東縣長治鄉', '屏東縣麟洛鄉', '屏東縣里港鄉', '屏東縣鹽埔鄉', '屏東縣高樹鄉', '屏東縣林邊鄉',
        '屏東縣南州鄉', '屏東縣九如鄉',
        '花蓮縣鳳林鎮', '花蓮縣壽豐鄉', '花蓮縣瑞穗鄉', '台東縣太麻里鄉', '台東縣卑南鄉', '台東縣池上鄉',
        '澎湖縣湖西鄉',
        '金門縣金沙鎮', '金門縣金寧鄉', '金門縣金湖鎮',
    ],
    '一級偏遠': [
        '新北市坪林區', '新北市石門區', '新北市平溪區', '新北市雙溪區',
        '宜蘭縣冬山鄉', '宜蘭縣壯圍鄉',
        '新竹縣橫山鄉', '新竹縣寶山鄉', '新竹縣北埔鄉', '新竹縣峨嵋鄉',
        '苗栗縣南庄鄉', '苗栗縣頭屋鄉', '苗栗縣西湖鄉', '苗栗縣獅潭鄉',
        '台中市大安區',
        '彰化縣大城鄉',
        '雲林縣東勢鄉',
        '嘉義縣布袋鎮', '嘉義縣溪口鄉', '嘉義縣鹿草鄉', '嘉義縣番路鄉',
        '台南市後壁區', '台南市大內區', '台南市左鎮區', '台南市龍崎區', '台南市北門區', '台南市東山區', '台南市安定區',
        '高雄市田寮區',
        '屏東縣萬巒鄉', '屏東縣竹田鄉', '屏東縣新埤鄉', '屏東縣崁頂鄉', '屏東縣車城鄉', '屏東縣枋山鄉',
        '花蓮縣富里鄉',
        '台東縣東河鄉', '台東縣鹿野鄉',
    ],
    '二級偏遠': [
        '花蓮縣豐濱鄉',
        '台東縣大武鄉', '台東縣長濱鄉',
    ],
    '山地鄉': [
        '新北市烏來區',
        '宜蘭縣大同鄉', '宜蘭縣南澳鄉',
        '桃園市復興區',
        '新竹縣尖石鄉', '新竹縣五峰鄉',
        '苗栗縣泰安鄉',
        '台中市和平區',
        '南投縣信義鄉', '南投縣仁愛鄉',
        '嘉義縣阿里山鄉',
        '高雄市茂林區', '高雄市桃源區',
        '高雄市那瑪夏區',
        '屏東縣山地門鄉', '屏東縣霧臺鄉', '屏東縣泰武鄉', '屏東縣來義鄉', '屏東縣春日鄉', '屏東縣獅子鄉',
        '屏東縣牡丹鄉', '屏東縣瑪家鄉',
        '花蓮縣秀林鄉', '花蓮縣萬榮鄉', '花蓮縣卓溪鄉',
        '台東縣延平鄉', '台東縣海端鄉', '台東縣達仁鄉', '台東縣金峰鄉',
    ],
    '一級離島': [
        '屏東縣琉球鄉',
        '連江縣南竿鄉', '連江縣北竿鄉',
    ],
    '二級離島': [
        '澎湖縣白沙鄉', '澎湖縣西嶼鄉',
        '台東縣綠島鄉',
    ],
    '三級離島': [
        '澎湖縣吉貝村', '澎湖縣望安鄉', '澎湖縣七美鄉',
        '台東縣蘭嶼鄉',
        '金門縣烈嶼鄉', '金門縣烏坵鄉',
        '連江縣莒光鄉', '連江縣東引鄉',
    ],
}

TOUR_AREA_DICT = {
    '-- 資源不足 --': None,
    '新北市三芝區': 0,
    '新北市金山區': 0,
    '新北市萬里區': 0,
    '新北市貢寮區': 0,
    '新北市石碇區': 0,
    '宜蘭縣蘇澳鎮': 0,
    '宜蘭縣三星鄉': 0,
    '新竹縣關西鎮': 0,
    '新竹縣新埔鎮': 0,
    '新竹縣芎林鄉': 0,
    '苗栗縣卓蘭鎮': 0,
    '苗栗縣銅鑼鄉': 0,
    '苗栗縣三義鄉': 0,
    '苗栗縣造橋鄉': 0,
    '苗栗縣三灣鄉': 0,
    '台中市石岡區': 0,
    '彰化縣線西鄉': 0,
    '彰化縣埔鹽鄉': 0,
    '彰化縣二水鄉': 0,
    '彰化縣田尾鄉': 0,
    '彰化縣芳苑鄉': 0,
    '彰化縣竹塘鄉': 0,
    '南投縣集集鎮': 0,
    '南投縣鹿谷鄉': 0,
    '南投縣中寮鄉': 0,
    '南投縣魚池鄉': 0,
    '南投縣國姓鄉': 0,
    '台南市柳營區': 0,
    '台南市六甲區': 0,
    '台南市西港區': 0,
    '台南市七股區': 0,
    '台南市將軍區': 0,
    '台南市山上區': 0,
    '台南市楠西區': 0,
    '台南市南化區': 0,
    '台南市官田區': 0,
    '雲林縣口湖鄉': 0,
    '雲林縣林內鄉': 0,
    '雲林縣二崙鄉': 0,
    '雲林縣褒忠鄉': 0,
    '雲林縣元長鄉': 0,
    '雲林縣四湖鄉': 0,
    '嘉義縣東石鄉': 0,
    '嘉義縣六腳鄉': 0,
    '嘉義縣義竹鄉': 0,
    '嘉義縣水上鄉': 0,
    '嘉義縣梅山鄉': 0,
    '嘉義縣大埔鄉': 0,
    '高雄市湖內區': 0,
    '高雄市梓官區': 0,
    '高雄市六龜區': 0,
    '高雄市杉林區': 0,
    '高雄市永安區': 0,
    '高雄市彌陀區': 0,
    '高雄市甲仙區': 0,
    '高雄市內門區': 0,
    '屏東縣恆春鎮': 0,
    '屏東縣長治鄉': 0,
    '屏東縣麟洛鄉': 0,
    '屏東縣里港鄉': 0,
    '屏東縣鹽埔鄉': 0,
    '屏東縣高樹鄉': 0,
    '屏東縣林邊鄉': 0,
    '屏東縣南州鄉': 0,
    '屏東縣九如鄉': 0,
    '花蓮縣鳳林鎮': 0,
    '花蓮縣壽豐鄉': 0,
    '花蓮縣瑞穗鄉': 0,
    '台東縣太麻里鄉': 0,
    '台東縣卑南鄉': 0,
    '台東縣池上鄉': 0,
    '澎湖縣湖西鄉': 0,
    '金門縣金沙鎮': 0,
    '金門縣金寧鄉': 0,
    '金門縣金湖鎮': 0,
    '-- 一級偏遠 --': None,
    '新北市坪林區': 1,
    '新北市石門區': 1,
    '新北市平溪區': 1,
    '新北市雙溪區': 1,
    '宜蘭縣冬山鄉': 1,
    '宜蘭縣壯圍鄉': 1,
    '新竹縣橫山鄉': 1,
    '新竹縣寶山鄉': 1,
    '新竹縣北埔鄉': 1,
    '新竹縣峨嵋鄉': 1,
    '苗栗縣南庄鄉': 1,
    '苗栗縣頭屋鄉': 1,
    '苗栗縣西湖鄉': 1,
    '苗栗縣獅潭鄉': 1,
    '台中市大安區': 1,
    '彰化縣大城鄉': 1,
    '雲林縣東勢鄉': 1,
    '嘉義縣布袋鎮': 1,
    '嘉義縣溪口鄉': 1,
    '嘉義縣鹿草鄉': 1,
    '嘉義縣番路鄉': 1,
    '台南市後壁區': 1,
    '台南市大內區': 1,
    '台南市左鎮區': 1,
    '台南市龍崎區': 1,
    '台南市北門區': 1,
    '台南市東山區': 1,
    '台南市安定區': 1,
    '高雄市田寮區': 1,
    '屏東縣萬巒鄉': 1,
    '屏東縣竹田鄉': 1,
    '屏東縣新埤鄉': 1,
    '屏東縣崁頂鄉': 1,
    '屏東縣車城鄉': 1,
    '屏東縣枋山鄉': 1,
    '花蓮縣富里鄉': 1,
    '台東縣東河鄉': 1,
    '台東縣鹿野鄉': 1,
    '-- 二級偏遠 --': None,
    '花蓮縣豐濱鄉': 2,
    '台東縣大武鄉': 2,
    '台東縣長濱鄉': 2,
    '-- 山地鄉 --': None,
    '新北市烏來區': 3,
    '宜蘭縣大同鄉': 3,
    '宜蘭縣南澳鄉': 3,
    '桃園市復興區': 3,
    '新竹縣尖石鄉': 3,
    '新竹縣五峰鄉': 3,
    '苗栗縣泰安鄉': 3,
    '台中市和平區': 3,
    '南投縣信義鄉': 3,
    '南投縣仁愛鄉': 3,
    '嘉義縣阿里山鄉': 3,
    '高雄市茂林區': 3,
    '高雄市桃源區': 3,
    '高雄市那瑪夏區': 3,
    '屏東縣山地門鄉': 3,
    '屏東縣霧臺鄉': 3,
    '屏東縣泰武鄉': 3,
    '屏東縣來義鄉': 3,
    '屏東縣春日鄉': 3,
    '屏東縣獅子鄉': 3,
    '屏東縣牡丹鄉': 3,
    '屏東縣瑪家鄉': 3,
    '花蓮縣秀林鄉': 3,
    '花蓮縣萬榮鄉': 3,
    '花蓮縣卓溪鄉': 3,
    '台東縣延平鄉': 3,
    '台東縣海端鄉': 3,
    '台東縣達仁鄉': 3,
    '台東縣金峰鄉': 3,
    '-- 一級離島 --': None,
    '屏東縣琉球鄉': 4,
    '連江縣南竿鄉': 4,
    '連江縣北竿鄉': 4,
    '-- 二級離島 --': None,
    '澎湖縣白沙鄉': 5,
    '澎湖縣西嶼鄉': 5,
    '台東縣綠島鄉': 5,
    '-- 三級離島 --': None,
    '澎湖縣吉貝村': 6,
    '澎湖縣望安鄉': 6,
    '澎湖縣七美鄉': 6,
    '台東縣蘭嶼鄉': 6,
    '金門縣烈嶼鄉': 6,
    '金門縣烏坵鄉': 6,
    '連江縣莒光鄉': 6,
    '連江縣東引鄉': 6,
}

TOUR_INS_CODE_DICT = {
    0: 'P23064',
    1: 'P23007',
    2: 'P23063',
    3: 'P23008',
    4: 'P23009',
    5: 'P23010',
    6: 'P23011',
}

TOUR_INS_FEE_DICT = {
    'P23064': 2000,
    'P23007': 3000,
    'P23063': 5000,
    'P23008': 8800,
    'P23009': 11000,
    'P23010': 12100,
    'P23011': 13200,
}

ABNORMAL_CARD = [
    ABNORMAL_CARD_WITH_HINT[i].split(' ')[0] for i in range(len(ABNORMAL_CARD_WITH_HINT))
]
ABNORMAL_CARD_DICT = {
    ABNORMAL_CARD_WITH_HINT[i].split(' ')[0]: ABNORMAL_CARD_WITH_HINT[i]
    for i in range(len(ABNORMAL_CARD_WITH_HINT))
}

INJURY_CARD_WITH_HINT = [
    'IC06 職業傷害',
]
INJURY_CARD = [
    INJURY_CARD_WITH_HINT[i].split(' ')[0] for i in range(len(INJURY_CARD_WITH_HINT))
]
INJURY_CARD_DICT = {
    INJURY_CARD_WITH_HINT[i].split(' ')[0]: INJURY_CARD_WITH_HINT[i]
    for i in range(len(INJURY_CARD_WITH_HINT))
}

CARD = ['自動取得', '不須取得', '欠卡'] + INJURY_CARD_WITH_HINT + ABNORMAL_CARD_WITH_HINT
UPLOAD_TYPE = ['1-正常上傳', '2-異常上傳', '3-正常補正', '4-異常補正']
TREAT_AFTER_CHECK = ['1-正常', '2-補卡']

COURSE = ['1', '2', '3', '4', '5', '6']
ROOM = ['1', '2', '3', '5', '6', '7', '8', '9', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20']
PERIOD = ['早班', '午班', '晚班']
INS_MEDICINE_TYPE = ['單方', '複方']
POSITION = ['醫師', '支援醫師', '藥師', '護士', '職員', '推拿師父']
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
SELF_PRESDAYS = ['1', '2', '3', '4', '5', '6', '7', '10', '14', '21', '28', '30']
INSTRUCTION = ['飯前', '飯後', '飯後睡前']

nhi_eii_api_error_code = {
    500: '申請檔案作業種類(sTypeCode)錯誤',
    5000: '網路環境載入異常',
    5001: '檔案權限不足或檔案大小異常',
    5002: '找不到Reader.dll',
    5003: '檔名錯誤',
    5004: '系統忙碌中，請稍後再試',
    5005: '產生簽章錯誤',
    5006: '記憶體不足',
    5007: '下載路徑不存在',
    5008: '取得醫療院所代碼錯誤',
    5009: '檔名有誤',
    5010: '認證錯誤',
    9999: '不明異常',
    5020: '連線總數量已超過，請稍後再試。',
    5021: '網路作業錯誤，訊息不完整',
    5022: '等待醫療系統處理中',
    5023: '等待EIIAPI處理中或交易不存在',
    5024: '無法建立檔案',
    5025: '寫入磁碟異常',
    5026: '解密錯誤',
    5027: '網路作業錯誤但已完成',
    5028: '連線錯誤',
    8203: '上傳下載請求檔未成功連線至伺服器',
    8218: '回饋資料下載未成功連線至伺服器',
}


# 取得資料路徑
def get_dir(system_settings, dir_type):
    base_dir = system_settings.field('資料路徑')
    if base_dir in ['', None]:
        base_dir = os.getcwd()
        system_utils.show_message_box(
            QMessageBox.Warning,
            '尚未設定資料路徑',
            '<font size="4" color="red"><b>資料路徑尚未設定, 使用預設的資料路徑<br>{base_dir}.</b></font>'.format(
                base_dir=base_dir
            ),
            '請至系統設定->其他->設定申報及備份路徑.'
        )

    dir_dict = {
        '申報路徑': '{base_dir}/nhi_upload'.format(base_dir=base_dir),
        '備份路徑': '{base_dir}/auto_backup'.format(base_dir=base_dir)
    }

    directory = dir_dict[dir_type]

    if not os.path.exists(directory):
        os.mkdir(directory)

    return directory


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
        if (medicine_type == '藥品類別' and  # 過濾自訂處方類別有與針傷處方類別相同的類別
                string_utils.xstr(row['DictGroupsName']) in ['穴道', '處置']):
            continue

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


def get_case_type(database, system_settings, row):
    injury = string_utils.xstr(row['Injury'])
    treat_type = string_utils.xstr(row['TreatType'])
    course = number_utils.get_integer(row['Continuance'])
    special_code = string_utils.xstr(row['SpecialCode'])
    regist_type = string_utils.xstr(row['RegistType'])
    treatment = string_utils.xstr(row['Treatment'])
    pres_days = case_utils.get_pres_days(database, row['CaseKey'])
    resource = system_settings.field('資源類別')

    if regist_type in TOUR_TYPE or resource == '資源不足開業':  # 巡迴醫療
        case_type = '25'
    elif treat_type in IMPROVE_CARE_TREAT:  # 加強照護
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
        elif number_utils.get_integer(case_row['DiagShareFee']) > 0 and course >= 2:
            diag_share_code = 'S20'

        if diag_share_code == 'S10' and case_row['RegistType'] in TOUR_TYPE:
            diag_share_code = 'S20'

    return diag_share_code


# 取得專案代碼
def get_special_code(database, system_settings, case_key):
    special_code_list = []
    sql = '''
            SELECT RegistType, TreatType, Treatment, SpecialCode FROM cases WHERE
            CaseKey = {0}
        '''.format(case_key)
    row = database.select_record(sql)[0]
    regist_type = string_utils.xstr(row['RegistType'])
    treat_type = string_utils.xstr(row['TreatType'])
    treatment = string_utils.xstr(row['Treatment'])
    special_code = string_utils.xstr(row['SpecialCode'])
    # 先檢查特定照護
    if treat_type in AUXILIARY_CARE_TREAT:  # 腦血管疾病
        return [None, None, None, None]

    if treat_type in IMPROVE_CARE_TREAT:
        special_code_list.append(SPECIAL_CODE_DICT[treat_type])
        special_code_list = special_code_list + [None] * (4 - len(special_code_list))
        return special_code_list

    if system_settings.field('資源類別') == '資源不足開業':
        special_code_list.append('C7')
    elif regist_type in TOUR_TYPE:
        special_code_list.append('C6')
    elif treat_type == '長期臥床':
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
    if string_utils.xstr(row['RegistType']) in TOUR_TYPE:  # 巡迴醫療不可申報初診照護
        return None

    if string_utils.xstr(row['TreatType']) in AUXILIARY_CARE_TREAT:  # 腦血管疾病, 小兒氣喘, 小兒腦麻不可申報初診照護
        return None

    if string_utils.xstr(row['Visit']) == '初診':
        return '初診照護'

    visit_year = 2  # 2年內無看診

    try:
        first_visit_year_range = row['CaseDate'].replace(year=row['CaseDate'].year - visit_year)
    except ValueError:
        if row['CaseDate'].day == 29:
            first_visit_year_range = row['CaseDate'].replace(year=row['CaseDate'].year - visit_year, day=28)
        else:
            return None

    sql = '''
        SELECT CaseKey FROM cases
        WHERE
            InsType = "健保" AND
            PatientKey = {patient_key} AND
            CaseKey != {case_key} AND
            CaseDate > "{first_visit_year_range}"
    '''.format(
        patient_key=row['PatientKey'],
        case_key=row['CaseKey'],
        first_visit_year_range=first_visit_year_range,
    )
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

    pharmacist_id = personnel_utils.get_personnel_field_value(database, pharmacist_name, 'ID')

    return pharmacist_id


def get_diag_code(database, system_settings, doctor_name, regist_type, treat_type, diag_fee):
    if diag_fee <= 0:
        return None

    if treat_type in CARE_TREAT and treat_type != '兒童鼻炎':  # 特殊照護且非兒童過敏性鼻炎不可申報診察費
        return None

    nurse = number_utils.get_integer(system_settings.field('護士人數'))
    if regist_type in TOUR_MOUNTAIN_ISLAND:  # 山地離島診察費
        if nurse > 0:
            diag_code = 'A09'  # 診察費第一段有護士
        else:
            diag_code = 'A10'  # 診察費第一段無護士
    else:
        if nurse > 0:
            diag_code = 'A01'  # 診察費第一段有護士
        else:
            diag_code = 'A02'  # 診察費第一段無護士

    position = personnel_utils.get_personnel_field_value(database, doctor_name, 'Position')
    if position == '支援醫師':
        diag_code = 'A02'

    return diag_code


# 藥服代號: A31-A32;  6次: 120010: 0-無調劑 1-A31藥師 2-A32醫師
def get_pharmacy_code(system_settings, row, pres_days, pharmacy_code='000000'):
    treat_type = string_utils.xstr(row['TreatType'])
    if treat_type in IMPROVE_CARE_TREAT and treat_type != '兒童鼻炎':  # 加強照護不可申報調劑費, 兒童鼻炎除外
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
    if number_utils.get_integer(row['Continuance']) <= 1:  # 內科或療程首次日期
        return case_date

    card = string_utils.xstr(row['Card'])
    last_month = datetime.date(case_date.year, case_date.month, 1) - datetime.timedelta(1)
    start_date = last_month.replace(day=1).strftime('%Y-%m-%d 00:00:00')

    sql = '''
        SELECT CaseDate FROM cases
        WHERE
            CaseDate BETWEEN "{start_date}" AND "{current_date}" AND
            CaseDate < "{current_date}" AND
            PatientKey = {patient_key} AND
            Card = "{card}" AND
            Continuance <= 1
        ORDER BY CaseDate DESC LIMIT 1
    '''.format(
        start_date=start_date,
        current_date=row['CaseDate'],
        patient_key=row['PatientKey'],
        card=card,
    )
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


def get_ins_xml_file_name(system_settings, apply_type, apply_date, prefix=None):
    xml_file_name = '{0}/{1}-{2}'.format(
        get_dir(system_settings, '申報路徑'),
        apply_date,
        apply_type,
    )
    if prefix is not None:
        xml_file_name += '-{0}'.format(prefix)

    xml_file_name += '.xml'

    return xml_file_name


def get_apply_date(apply_year, apply_month):
    apply_date = '{0:0>3}{1:0>2}'.format(apply_year - 1911, apply_month)

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


def get_disease_rows(database, disease_list):
    disease_rows = []
    for disease in disease_list:
        if type(disease) is tuple:
            start_disease = disease[0].split('-')[0]
            end_disease = disease[0].split('-')[1]

            sql = '''
                SELECT ICDCode FROM icd10 
                WHERE 
                    ICDCode BETWEEN "{start_disease}" AND "{end_disease}" OR
                    ICDCode LIKE "{end_disease}%"
                ORDER BY ICDCode
            '''.format(
                start_disease=start_disease,
                end_disease=end_disease,
            )
            icd_rows = database.select_record(sql)
        else:
            sql = '''
                SELECT ICDCode FROM icd10 
                WHERE 
                    ICDCode LIKE "{0}%" 
                ORDER BY ICDCode
            '''.format(disease)
            icd_rows = database.select_record(sql)

        for icd_row in icd_rows:
            icd_code = string_utils.xstr(icd_row['ICDCode'])
            sql = 'SELECT ICDCode FROM icd10 WHERE ICDCode LIKE "{0}%" LIMIT 2'.format(icd_code)
            temp_rows = database.select_record(sql)
            if len(temp_rows) == 1:
                disease_rows.append(string_utils.xstr(temp_rows[0]['ICDCode']))

    return disease_rows


def get_complicated_acupuncture_rows(database, groups_name, disease=1):
    disease_rows = []
    rows = icd10_utils.COMPLICATED_ACUPUNCTURE_DISEASE_DICT[groups_name]
    for row in rows:
        disease_list1, disease_list2 = row[0], row[1]
        if disease == 1:
            disease_list = disease_list1
        else:
            disease_list = disease_list2

        disease_row = get_disease_rows(database, disease_list)
        disease_rows += disease_row

    return disease_rows


def get_complicated_acupuncture_list(database, disease=1):
    disease_rows = []
    for row in list(icd10_utils.COMPLICATED_ACUPUNCTURE_DISEASE_DICT.keys()):
        rows = get_complicated_acupuncture_rows(database, row, disease)
        disease_rows += rows

    return disease_rows


def get_complicated_massage_rows(database, groups_name, disease=1):
    disease_rows = []
    rows = icd10_utils.COMPLICATED_MASSAGE_DISEASE_DICT[groups_name]
    for row in rows:
        disease_list1, disease_list2 = row[0], row[1]
        if disease == 1:
            disease_list = disease_list1
        else:
            disease_list = disease_list2

        disease_row = get_disease_rows(database, disease_list)
        disease_rows += disease_row

    return disease_rows


def get_ins_special_care_rows(database, groups_name, disease=1):
    disease_rows = []
    rows = icd10_utils.INS_SPECIAL_CARE_DICT[groups_name]
    for row in rows:
        disease_list1, disease_list2 = row[0], row[1]
        if disease == 1:
            disease_list = disease_list1
        else:
            disease_list = disease_list2

        disease_row = get_disease_rows(database, disease_list)
        disease_rows += disease_row

    return disease_rows


def get_custom_groups_name_rows(database, custom_dict, groups_name, disease=1):
    disease_rows = []
    rows = custom_dict[groups_name]
    for row in rows:
        disease_list1, disease_list2 = row[0], row[1]
        if disease == 1:
            disease_list = disease_list1
        else:
            disease_list = disease_list2

        disease_row = get_disease_rows(database, disease_list)
        disease_rows += disease_row

    return disease_rows


def get_complicated_massage_list(database, disease=1):
    disease_rows = []
    for row in list(icd10_utils.COMPLICATED_MASSAGE_DISEASE_DICT.keys()):
        rows = get_complicated_massage_rows(database, row, disease)
        disease_rows += rows

    return disease_rows


def get_ins_special_care_list(database, disease=1):
    disease_rows = []
    for row in list(icd10_utils.INS_SPECIAL_CARE_DICT.keys()):
        rows = get_ins_special_care_rows(database, row, disease)
        disease_rows += rows

    return disease_rows


def NHI_SendB(system_settings, type_code, dest_file):
    if sys.platform == 'win32':
        dest_file = dest_file.replace('/', '\\')

    title = '上傳健保資料'
    message = '<font size="4" color="red"><b>正在上傳健保資料中, 請稍後...</b></font>'
    hint = '正在與與健保IDC資訊中心連線, 會花費一些時間.'
    msg_box = dialog_utils.message_box(title, message, hint)
    msg_box.show()

    msg_queue = Queue()
    QtCore.QCoreApplication.processEvents()

    t = Thread(target=NHI_SendB_thread, args=(
        msg_queue, system_settings, type_code, dest_file,
    ))
    t.start()
    (error_code, local_id, nhi_id) = msg_queue.get()
    msg_box.close()

    if error_code != 0:
        error_message = nhi_eii_api_error_code[error_code]
    else:
        error_message = '''
                上傳成功<br>
                本機作業碼: {local_id}
                IDC作業碼: {nhi_id}
            '''.format(
            local_id=str(local_id).encode('ascii'),
            nhi_id=str(nhi_id).encode('ascii'),
        )

    system_utils.show_message_box(
        QMessageBox.Information,
        '上傳結果',
        '<font size="4" color="red"><b>{error_message}</b></font>'.format(
            error_message=error_message,
        ),
        '若上傳成功, 請於30分鐘後至健保VPN網站查看上傳結果.'
    )


'''
// 回傳值: 0：無任何錯誤, 其他：參考異常碼對應。
int NHI_SendB(
    int iRs232PortNo,           // [ in]健保讀卡機連接之通訊連接埠編號，起始值為0
    char *sReaderDllPathName,   // [ in]健保讀卡機Reader.dll放置路徑，為完整路徑及檔名，
                                // 例：C:\Reader.dll
    char *sUploadFileName,      // [ in]上傳作業檔案，為完整路徑及檔名，
                                // 例：C:\3501200000110990913B.zip
    char *sTypeCode,            // [ in]上傳作業種類：
                                //      03：醫費申報資料XML格式
                                //      05：預檢醫費申報資料XML格式
                                //      07：醫療費用電子申復資料
                                //      09：預檢醫療費用電子申復資料
                                //      26：檢驗(查)每日上傳資料XML格式
    char *sLocal_ID,            // [out] 本機端回傳之作業辨識碼，供識別作業之用，使用時須搭配sNHI_ID，為12個位元組
                                //       Ansi資料，存放方式請參考範例程式碼
    char *sNHI_ID)              // [out] IDC回傳之作業辨識碼，供識別作業之用，為12個位元組
                                //       Ansi資料，存放方式請參考範例程式碼

                                // 本函式將使用者端之「上傳作業種類」檔案傳送至IDC
)
'''


def NHI_SendB_thread(out_queue, system_settings, type_code, dest_file):
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname("__file__")))
    dll_file = os.path.join(BASE_DIR, 'nhi_eiiapi.dll')
    nhi_eii_api = ctypes.windll.LoadLibrary(dll_file)

    com_port = number_utils.get_integer(system_settings.field('健保卡讀卡機連接埠')) - 1  # com1=0, com2=1, com3=2,...
    reader_file = os.path.join(BASE_DIR, 'reader.dll')

    p_reader_file = ctypes.c_char_p(reader_file.encode('ascii'))
    p_type_code = ctypes.c_char_p(type_code.encode('ascii'))
    p_zip_file = ctypes.c_char_p(dest_file.encode('ascii'))

    local_id = ctypes.c_buffer(12)
    nhi_id = ctypes.c_buffer(12)
    error_code = nhi_eii_api.NHI_SendB(
        com_port,
        p_reader_file,
        p_zip_file,
        p_type_code,
        local_id,
        nhi_id,
    )

    out_queue.put((error_code, local_id, nhi_id))


def get_apply_type_sql(apply_type):
    sql = 'ApplyType = "{0}"'.format(apply_type)

    if apply_type == '補報':
        sql = 'ApplyType IN {0}'.format(tuple(REMEDY_TYPE))

    return sql


# 取得療程首次日期
def get_first_course_delta(table_widget, row_no, patient_key, course, next_case_date):
    first_case_date = None
    if course == 1:
        first_case_date = table_widget.item(row_no, 1).text()
    else:
        for i in range(course, 0, -1):
            previous_case_date = table_widget.item(row_no - i, 1)
            previous_patient_key = table_widget.item(row_no - i, 3)
            if previous_case_date is None:
                continue

            if previous_patient_key.text() != patient_key:
                continue

            previous_case_date = previous_case_date.text()
            previous_course = number_utils.get_integer(
                table_widget.item(row_no - i, 7).text()
            )
            if previous_course == 1:
                first_case_date = previous_case_date
                break

    if first_case_date is not None:
        delta = date_utils.str_to_date(next_case_date) - date_utils.str_to_date(first_case_date)
    else:
        delta = None

    return delta


# 取得相同卡序日期
def get_duplicated_card(table_widget, row_no, patient_key, card):
    duplicated_case_date = None

    for i in range(row_no, 0, -1):
        previous_patient_key = table_widget.item(i, 3)
        previous_card = table_widget.item(i, 6)
        previous_case_date = table_widget.item(i, 1)

        if previous_patient_key is not None and previous_patient_key.text() != patient_key:  # 換人
            break

        if previous_card.text() == card:
            duplicated_case_date = previous_case_date.text()
            break

    return duplicated_case_date
