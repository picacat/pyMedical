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
from libs import case_utils
from libs import personnel_utils
from libs import charge_utils
from libs import system_utils
from libs import dialog_utils

XML_OUT_PATH = '{0}/nhi_upload'.format(os.getcwd())
EMR_OUT_PATH = '{0}/emr'.format(os.getcwd())

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
APPLY_TYPE = ['申報', '不申報', '補報']
VISIT = ['複診', '初診']
REG_TYPE = ['一般門診', '預約門診', '夜間急診']
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
UPLOAD_TYPE = ['1-正常上傳','2-異常上傳', '3-正常補正', '4-異常補正']
TREAT_AFTER_CHECK = ['1-正常','2-補卡']

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

COMPLICATED_ACUPUNCTURE_DISEASE_DICT = {
    '唇舌口惡性腫瘤': [
        [
            [('C00-C10',)], [],
        ]
    ],
    '鼻咽食道惡性腫瘤': [
        [
            [('C11-C15',)], [],
        ]
    ],
    '胃腸惡性腫瘤': [
        [
            [('C16-C20',)], [],
        ]
    ],
    '肛門惡性腫瘤': [
        [
            ['C21'], [],
        ]
    ],
    '肝膽胰脾惡性腫瘤': [
        [
            [('C22-C29',)], [],
        ]
    ],
    '呼吸系統惡性腫瘤': [
        [
            [('C30-C34',)], [],
        ]
    ],
    '胸腔器官惡性腫瘤': [
        [
            [('C37-C39',)], [],
        ]
    ],
    '肢體惡性腫瘤': [
        [
            [('C40-C41',)], [],
        ]
    ],
    '皮膚惡性腫瘤': [
        [
            [('C43-C46',)], [],
        ]
    ],
    '神經系統惡性腫瘤': [
        [
            ['C47'], [],
        ]
    ],
    '腹腔惡性腫瘤': [
        [
            ['C48'], [],
        ]
    ],
    '結締組織惡性腫瘤': [
        [
            ['C49'], [],
        ]
    ],
    '乳房惡性腫瘤': [
        [
            ['C50'], [],
        ]
    ],
    '女性生殖器官惡性腫瘤': [
        [
            [('C51-C59',)], [],
        ]
    ],
    '男性生殖器官惡性腫瘤': [
        [
            [('C60-C63',)], [],
        ]
    ],
    '泌尿系統惡性腫瘤': [
        [
            [('C64-C68',)], [],
        ]
    ],
    '眼惡性腫瘤': [
        [
            ['C69'], [],
        ]
    ],
    '腦惡性腫瘤': [
        [
            [('C70-C71',)], [],
        ]
    ],
    '中樞神經惡性腫瘤': [
        [
            ['C72'], [],
        ]
    ],
    '內分泌腺體惡性腫瘤': [
        [
            [('C73-C75',)], [],
        ]
    ],
    '其他惡性腫瘤': [
        [
            [('C76-C96',)], [],
        ]
    ],
    '腦瘤併發神經功能障礙': [
        [
            ['D33'], [],
        ]
    ],
    '老年期及初老年期器質性精神病態': [
        [
            [('F03-F05',)], [],
        ]
    ],
    '亞急性譫妄': [
        [
            ['F05'], [],
        ]
    ],
    '其他器質性精神病態': [
        [
            ['F02', 'F04', 'F09'], [],
        ]
    ],
    '思覺失調症': [
        [
            ['F20', 'F21', 'F25'], [],
        ]

    ],
    '情感性精神病': [
        [
            [('F30-F39',)], [],
        ]
    ],
    '妄想狀態': [
        [
            ['F22', 'F23', 'F24'], [],
        ]
    ],
    '源自兒童期之精神病': [
        [
            ['F84'], []
        ]
    ],
    '急性脊髓灰白質炎併有其他麻痺者': [
        [
            ['A80'], [],
        ]
    ],
    '嬰兒腦性麻痺': [
        [
            ['G80'], [],
        ]
    ],
    '其他麻痺性徵候群': [  # 需要輸入次診斷碼
        [
            ['G82', 'G83'], ['B91'],
        ]
    ],
    '重症肌無力症': [
        [
            ['G70'], [],
        ]
    ],
    '頸椎脊髓損傷, 伴有脊髓病灶': [  # 需要輸入次診斷碼
        [
            ['S141'], [('S120-S126',)]
        ],
    ],
    '胸椎脊髓損傷, 伴有脊髓病灶': [  # 需要輸入次診斷碼
        [
            ['S241'], ['S220']
        ],
    ],
    '腰部脊髓傷害, 伴有脊髓病灶': [  # 需要輸入次診斷碼
        [
            ['S341'], [('S220-S320',)]
        ],
    ],
    '無明顯脊椎損傷之脊髓傷害': [
        [
            ['S141', 'S241', 'S341'], [],
        ]
    ],
    '其他脊髓病變': [
        [
            ['G95'], [],
        ]
    ],
    '蜘蛛膜下腔出血': [
        [
            ['I60'], [],
        ]
    ],
    '腦內出血': [
        [
            ['I61', 'I62'], [],
        ]
    ],
    '腦梗塞': [
        [
            ['I63', 'I65', 'I66'], [],
        ]
    ],
    '其他腦血管疾病': [
        [
            ['G45', 'G46', 'I67'], [],
        ]
    ],
    '癲癇': [
        [
            ['G40'], [],
        ]
    ],
    '巴金森病': [
        [
            ['G20', 'G21'], [],
        ]
    ],
    '脊髓小腦症': [
        [
            ['G11', 'G94'], [],
        ]
    ],
    '腦裂傷及挫傷': [
        [
            ['S019', 'S063'], [],
        ]
    ],
    '受傷後之蜘蛛網膜下、硬腦膜下及硬腦膜外出血': [
        [
            ['S019', ('S064-S066',)], [],
        ]
    ],
    '視神經及神經徑之損傷': [
        [
            [('S0401-S0404',)], [],
        ]
    ],
    '神經根級脊神經叢之損傷': [
        [
            ['S142', 'S143' , 'S242', 'S342', 'S344'], [],
        ]
    ],
    '肩及骨盆以外之軀幹神經損傷': [
        [
            ['S145', 'S243' , 'S244', 'S248', 'S249', 'S345', 'S346', 'S348', 'S349'], [],
        ]
    ],
    '肩及上肢末梢神經之損傷': [
        [
            [('S440-S445',)], [],
        ],
        [
            [('S448-S449',)], [],
        ],
        [
            [('S540-S543',)], [],
        ],
        [
            [('S548-S549',)], [],
        ],
        [
            [('S640-S644',)], [],
        ],
        [
            [('S648-S649',)], [],

        ],
    ],
    '骨盆及下肢末梢神經損傷': [
        [
            [('S740-S742',)], [],
        ],
        [
            [('S748-S749',)], [],
        ],
        [
            [('S840-S842',)], [],
        ],
        [
            [('S848-S849',)], [],
        ],
        [
            [('S940-S943',)], [],
        ],
        [
            [('S948-S949',)], [],

        ],
    ],
}


COMPLICATED_MASSAGE_DISEASE_DICT = {
    '雷特病之關節病變及有關病態，多處部位': [
        [
            ['M0239'], [],
        ]
    ],
    '畢賽徵候群之關節病變，多處部位': [
        [
            ['M352'], [],
        ]
    ],
    '更年期關節炎，多處部位': [
        [
            ['M1389'], [],
        ]
    ],
    '未明示之多發性關節病變或多發性關節炎，多處部位': [
        [
            ['M130'], [],
        ]
    ],
    '其他明示之關節病變, 多處部位': [
        [
            ['M1289'], [],
        ]
    ],
    '未明示之關節病變，多處部位': [
        [
            ['M129'], [],
        ]
    ],
    '關節軟骨疾患，多處部位': [
        [
            ['M2410'], [],
        ]
    ],
    '關節緊縮，多處部位': [
        [
            ['M2450'], [],
        ]
    ],
    '關節粘連，多處部位': [
        [
            ['M2460'], [],
        ]
    ],
    '其他關節障礙，他處未歸類，多處部位': [
        [
            ['M2480'], [],
        ]
    ],
    '未明示之關節障礙，多處部位': [
        [
            ['M249'], [],
        ]
    ],
    '復發性風濕，多處部位': [
        [
            ['M1239'], [],
        ]
    ],
    '關節痛，多處部位': [
        [
            ['M2550'], [],
        ]
    ],
    '關節僵直，他處未歸類者，多處部位': [
        [
            ['M2560'], [],
        ]
    ],
    '行走障礙，多處部位': [
        [
            ['R262'], [],
        ]
    ],
    '未明示之關節疾患，多處部位': [
        [
            ['M259'], [],
        ]
    ],
    '肩膀及上臂骨折': [
        [
            ['S42'], [],
        ]
    ],
    '肩部及上臂其他及未明示損傷': [
        [
            ['S49'], [],
        ]
    ],
    '手肘及前臂其他及未明示損傷': [
        [
            ['S59'], [],
        ]
    ],
    '腕部及手部骨折': [
        [
            ['S62'], [],
        ]
    ],
    '股骨骨折': [
        [
            ['S72'], [],
        ]
    ],
    '小腿踝部閉鎖性骨折': [
        [
            ['S82'], [],
        ]
    ],
    '足部與腳趾骨折，足踝除外': [
        [
            ['S92'], [],
        ]
    ],
    '顱骨穹窿骨折': [
        [
            ['S020'], [],
        ]
    ],
    '顱骨底部骨折': [
        [
            ['S021'], [],
        ]
    ],
    '臉骨骨折': [
        [
            ['S022', 'S026'], [],
        ]
    ],
    '顴骨及上頷骨骨折，閉鎖性': [
        [
            ['S024'], [],
        ]
    ],
    '眶底閉鎖性骨折': [
        [
            ['S023'], [],
        ]
    ],
    '其他顏面骨閉鎖性骨折': [
        [
            [('S028-S029',)], [],
        ]
    ],
    '脊柱骨折，閉鎖性': [
        [
            [('S120-S129',)], [],
        ]
    ],
    '頸椎骨折，閉鎖性': [
        [
            [('S120-S126',), 'S220'], [],
        ]
    ],
    '腰椎骨折，閉鎖性': [
        [
            ['S320'], [],
        ]
    ],
    '胝骨及尾骨骨折，閉鎖性': [
        [
            [('S321-S322',)], [],
        ]
    ],
    '未明示之脊柱骨折，閉鎖性': [
        [
            ['S129', 'S220', ('S320-S321',)], [],
        ]
    ],
    '肋骨閉鎖性骨折': [
        [
            [('S223-S224',)], [],
        ]
    ],
    '胸骨閉鎖性骨折': [
        [
            ['S222'], [],
        ]
    ],
    '連枷胸（多條肋骨塌陷性骨折）': [
        [
            ['S225'], [],
        ]
    ],
    '喉部及氣管閉鎖性骨折': [
        [
            ['S129'], [],
        ]
    ],
    '骨盆骨折': [
        [
            [('S323-S329',)], [],
        ]
    ],
    '髖臼閉鎖性骨折': [
        [
            ['S324'], [],
        ]
    ],
    '恥骨閉鎖性骨折': [
        [
            ['S325'], [],
        ]
    ],
    '骨盆其他明示部位之閉鎖性骨折': [
        [
            ['S323', 'S326', ('S32810-S32811',)], [],
        ]
    ],
    '骨盆之其他骨折，閉鎖性': [
        [
            ['S3289'], [],
        ]
    ],
    '診斷欠明之軀幹骨骨折': [
        [
            ['S229'], [],
        ]
    ],
    '鎖骨閉鎖性骨折': [
        [
            [('S42001-S42036',)], [],
        ]
    ],
    '肩胛骨骨折': [
        [
            [('S42101-S42199',)], [],
        ]
    ],
    '其他之肩胛骨骨折，閉鎖性': [
        [
            [('S42113-S42116',)], [],
        ]
    ],
    '肱骨上端閉鎖性骨折': [
        [
            [('S42201-S42296',)], [],
        ]
    ],
    '肱骨骨幹或未明示部位之閉鎖性骨折': [
        [
            [('S42301-S42399',)], [],
        ]
    ],
    '肱骨踝上骨折，閉鎖性': [
        [
            [('S42101-S42496',)], [],
        ]
    ],
    '橈骨及尺骨上端閉鎖性骨折': [
        [
            [('S52101-S52189',)], [],
        ]
    ],
    '橈骨及尺骨骨幹閉鎖性骨折': [
        [
            [('S52201-S52399',)], [],
        ]
    ],
    '橈骨及尺骨下端閉鎖性骨折': [
        [
            [('S52501-S52699',)], [],
        ]
    ],
    '橈骨及尺骨之閉鎖性骨折': [
        [
            [('S5290-S5292',)], [],
        ]
    ],
    '腕骨骨折': [
        [
            [('S62001-S62186',)], [],
        ]
    ],
    '掌骨骨折': [
        [
            [('S62201-S62399',)], [],
        ]
    ],
    '一個或多個手指骨骨折': [
        [
            [('S62501-S62699',)], [],
        ]
    ],
    '手骨之多處閉鎖性骨折': [
        [
            [('S6290-S6292',)], [],
        ]
    ],
    '肩帶未明示部位骨折': [
        [
            [('S4290-S4292',)], [],
        ]
    ],
    '前臂骨折': [
        [
            [('S5290-S5292',)], [],
        ]
    ],
    '胸骨骨折': [
        [
            ['S2220', 'S2239', 'S2249'], [],
        ]
    ],
    '股骨頸骨折': [
        [
            [('S72001-S72099',)], [],
        ]
    ],
    '經由粗隆之骨折，閉鎖性': [
        [
            [('S72101-S7226',)], [],
        ]
    ],
    '未明示部位之股骨頸骨折，閉鎖性': [
        [
            [('S72001-S72009',)], [],
        ]
    ],
    '股骨骨折，閉鎖性': [
        [
            [('S72301-S72499',)], [],
        ]
    ],
    '閉鎖性髕骨之骨折': [
        [
            [('S82001-S82099',)], [],
        ]
    ],
    '脛骨與腓骨之上端閉鎖性骨折': [
        [
            [('S82101-S82109',)], [],
        ]
    ],
    '脛骨幹閉鎖性骨折': [
        [
            [('S82201-S82299', )], [],
        ]
    ],
    '腓骨幹閉鎖性骨折': [
        [
            [('S82401-S82499',)], [],
        ]
    ],
    '閉鎖性踝骨折': [
        [
            [('S8251-S8266',)], [],
        ]
    ],
    '閉鎖性跟骨骨折': [
        [
            [('S92001-S92066',)], [],
        ]
    ],
    '其他跗骨及蹠骨之骨折，閉鎖性': [
        [
            [('S92101-S925',)], [],
        ]
    ],
    '閉鎖性一個或多個腳趾骨骨折': [
        [
            [('S92401-S92919',)], [],
        ]
    ],
    '閉鎖性下肢之其他多處及診斷欠明之骨折': [
        [
            [('S8290-S8292',)], [],
        ]
    ],
    '閉鎖性多處骨折，侵及兩側下肢，下與上肢及下肢與肋骨和胸骨者': [
        [
            ['T07'], [],
        ]
    ],
    '閉鎖性未明示部位之骨折': [
        [
            ['T148'], [],
        ]
    ],
    '肩關節半脫位和脫臼': [
        [
            [('S430-S433',)], [],
        ]
    ],
    '橈骨頭半脫位及脫臼': [
        [
            [('S530-S531',)], [],
        ]
    ],
    '腕部及手部關節半脫位及脫臼': [
        [
            ['S630'], [],
        ]
    ],
    '手指半脫位及脫臼': [
        [
            [('S631-S632',)], [],
        ]
    ],
    '髖部半脫位及脫臼': [
        [
            ['S730'], [],
        ]
    ],
    '內半月板桶柄狀撕裂，近期損傷': [
        [
            [('S8321-S8324',)], [],
        ]
    ],
    '髕骨半脫位及脫臼': [
        [
            [('S83001-S83096',)], [],
        ]
    ],
    '膝部半脫位及脫臼': [
        [
            [('S83101-S83196',)], [],
        ]
    ],
    '踝關節半脫位': [
        [
            ['S930'], [],
        ]
    ],
    '足部半脫位及脫臼': [
        [
            ['S933'], [],
        ]
    ],
    '頸部關節及韌帶脫臼及扭傷': [
        [
            [('S130-S132',)], [],
        ]
    ],
    '腰(部)脊椎半脫位(臼)和脫位(臼)': [
        [
            [('S331-S333',)], [],
        ]
    ],
    '胸部關節及靱帶之扭傷及脫位': [
        [
            [('S231-S232',)], [],
        ]
    ],
    '胸鎖骨間關節半脫位和脫臼': [
        [
            ['S432'], [],
        ]
    ],
    '其他和未明示部位的腰(部)脊椎[腰椎]和骨盆(腔)骨脫位(臼)': [
        [
            [('S3330-S3339',)], [],
        ]
    ],
    '軀幹多處挫傷': [
        [
            ['T148'], [],
        ]
    ],
    '上肢多處挫傷': [
        [
            ['S40019'], [],
        ]
    ],
    '下肢多處挫傷': [
        [
            ['S7010', 'S7012', 'S8010', 'S8012'], [],
        ]
    ],
    '下肢挫傷及其他與未明示位置之挫傷，多處位置挫傷，他處未歸類者': [
        [
            ['T148'], [],
        ]
    ],
    '肩及上臂多處位置壓砸傷': [
        [
            ['S47'], [],
        ]
    ],
    '髖部及大腿壓砸傷': [
        [
            ['S770', 'S771', 'S772'], [],
        ]
    ],
    '膝部及小腿壓砸傷': [
        [
            ['S870', 'S878'], [],
        ]
    ],
    '踝部、腳趾及足部壓砸傷': [
        [
            ['S970', 'S971', 'S978'], [],
        ]
    ],
    '多處及未明示位置之壓砸傷': [
        [
            ['S772'], [],
        ]
    ],
    '顱骨及面骨骨折之後期影響': [
        [
            ['S02'], [],
        ]
    ],
    '脊柱及軀幹骨折之後期影響，未提及脊髓病灶者': [
        [
            ['S129', 'S220', 'S229', 'S329'], [],
        ]
    ],
    '肱骨上端骨折': [
        [
            [('S422-S429',)], [],
        ]
    ],
    '頷骨脫臼': [
        [
            ['S030'], [],
        ]
    ],
    '鼻中隔軟骨脫位': [
        [
            ['S031'], [],
        ]
    ],
    '胸椎間盤創傷性破裂': [
        [
            ['S230'], [],
        ]
    ],
    '腰(部)椎間盤創傷性破裂': [
        [
            ['S330'], [],
        ]
    ],
}


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

    pharmacist_id = personnel_utils.get_personnel_field_value(database, pharmacist_name, 'ID')

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
    rows = COMPLICATED_ACUPUNCTURE_DISEASE_DICT[groups_name]
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
    for row in list(COMPLICATED_ACUPUNCTURE_DISEASE_DICT.keys()):
        rows = get_complicated_acupuncture_rows(database, row, disease)
        disease_rows += rows

    return disease_rows


def get_complicated_massage_rows(database, groups_name, disease=1):
    disease_rows = []
    rows = COMPLICATED_MASSAGE_DISEASE_DICT[groups_name]
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
    for row in list(COMPLICATED_MASSAGE_DISEASE_DICT.keys()):
        rows = get_complicated_massage_rows(database, row, disease)
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

