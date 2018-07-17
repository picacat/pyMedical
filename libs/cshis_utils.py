# 2018.04.30
from PyQt5.QtWidgets import QMessageBox, QPushButton
import sys
import ctypes
from classes import cshis
from libs import date_utils
from libs import patient_utils
from libs import number_utils
from libs import nhi_utils
from libs import string_utils
from libs import case_utils
from libs import prescript_utils

NORMAL_CARD = '1'
RETURN_CARD = '2'
ERROR_MESSAGE = {
    4000: ['讀卡機timeout', '請檢查讀卡機連接埠是否接妥, 或是系統設定->讀卡機連接埠是否正確'],
    4012: ['未置入安全模組卡', '安全模組可能未正確安裝至讀卡機內, 請關掉讀卡機電源, 打開螺絲背蓋, 檢查安全模組卡是否安裝妥當.'],
    4013: ['未置入健保IC卡', '請確定健保IC卡已經正確的插入讀卡機'],
    4014: ['未置入醫事人員卡', None],
    4029: ['IC卡權限不足', None],
    4032: ['所插入非安全模組卡', None],
    4033: ['所置入非健保IC卡', None],
    4034: ['所置入非醫事人員卡', None],
    4042: ['醫事人員卡PIN尚未認證成功', None],
    4050: ['安全模組尚未與IDC認證', '請執行[健保讀卡機安全模組認證]'],
    4051: ['安全模組與IDC認證失敗', None],
    4061: ['網路不通', '請檢查電腦網路接頭是否鬆脫或中華電信VPN網路數據機是否正常, 如有檢查困難, 請致電中華電信 0800-080-128 查詢'],
    4071: ['健保IC卡與IDC認證失敗', None],
    5001: ['就醫可用次數不足', '請執行[更新病患健保卡內容]作業, 若仍然無法取得可用次數, 請確認病患健保卡加保狀態'],
    5002: ['卡片已註銷', None],
    5003: ['卡片已過有限期限', None],
    5004: ['非新生兒一個月內就診', None],
    5005: ['讀卡機的日期時間讀取失敗', None],
    5006: ['讀取安全模組內的「醫療院所代碼」失敗', None],
    5007: ['寫入一組新的「就醫資料登錄」失敗', None],
    5008: ['安全模組簽章失敗', None],
    5009: ['無寫入就醫相關紀錄之權限', None],
    5010: ['同一天看診兩科(含)以上', None],
    5012: ['此人未在保或欠費', None],
    5015: ['「門診處方箋」讀取失敗。', None],
    5016: ['「長期處方箋」讀取失敗。', None],
    5017: ['「重要醫令」讀取失敗。', None],
    5020: ['要寫入的資料和健保IC卡不是屬於同一人。', None],
    5022: ['找不到「就醫資料登錄」中的該組資料。', None],
    5023: ['「就醫資料登錄」寫入失敗。', None],
    5028: ['HC卡「就醫費用紀錄」寫入失敗。', None],
    5033: ['「門診處方箋」寫入失敗。', None],
    5051: ['新生兒註記寫入失敗', None],
    5052: ['有新生兒出生日期，但無新生兒胞胎註記資料', None],
    5056: ['讀取醫事人員ID失敗', None],
    5057: ['過敏藥物寫入失敗。', None],
    5061: ['同意器官捐贈及安寧緩和醫療註記寫入失敗寫入失敗', None],
    5062: ['放棄同意器官捐贈及安寧緩和醫療註記輸入', None],
    5067: ['安全模組卡「醫療院所代碼」讀取失敗', None],
    5068: ['預防保健資料寫入失敗', None],
    5071: ['緊急聯絡電話寫失敗。', None],
    5078: ['產前檢查資料寫入失敗', None],
    5079: ['性別不符，健保IC卡記載為男性', None],
    5081: ['最近24小時內同院所未曾就醫，故不可取消就醫', None],
    5082: ['最近24小時內同院所未曾執行產檢服務紀錄，故不可取消產檢', None],
    5083: ['最近6次就醫不含就醫類別AC，不可單獨寫入預防保健或產檢紀錄', None],
    5084: ['最近24小時內同院所未曾執行保健服務項目紀錄，故不可取消保健服務', None],
    5087: ['刪除「孕婦產前檢查(限女性)」全部11 組的資料失敗。', None],
    5093: ['預防接種資料寫入失敗', None],
    5102: ['使用者所輸入之pin 值，與卡上之pin值不合', None],
    5105: ['原PIN碼尚未通過認證', '請先執行[驗證病患健保卡密碼]作業'],
    5107: ['使用者輸入兩次新PIN 值，兩次PIN 值不合', None],
    5108: ['密碼變更失敗', None],
    5109: ['密碼輸入過程按『取消』鍵', None],
    5110: ['變更健保IC卡密碼時, 請移除醫事人員卡', None],
    5111: ['停用失敗，且健保IC卡之Pin 碼輸入功能仍啟用', None],
    5122: ['被鎖住的醫事人員卡仍未解開', None],
    5130: ['更新健保IC卡內容失敗。', None],
    5141: ['未置入醫事人員卡, 僅能讀取重大傷病有效起訖日期', None],
    5150: ['卡片中無此筆就醫記錄', None],
    5151: ['就醫類別為數值才可退掛', None],
    5152: ['醫療院所不同，不可退掛', None],
    5153: ['本筆就醫記錄已經退掛過，不可重覆退掛', None],
    5154: ['退掛日期不符合規定', None],
    5160: ['就醫可用次數不合理', None],
    5161: ['最近一次就醫年不合理', None],
    5162: ['最近一次就醫序號不合理', None],
    5163: ['住診費用總累計不合理', None],
    5164: ['門診費用總累計不合理', None],
    5165: ['就醫累計資料年不合理', None],
    5166: ['門住診就醫累計次數不合理', None],
    5167: ['門診部分負擔費用累計不合理', None],
    5168: ['住診急性30天、慢性180天以下部分負擔費用累計不合理', None],
    5169: ['住診急性31天、慢性181天以上部分負擔費用累計不合理', None],
    5170: ['門診+住診部分負擔費用累計不合理', None],
    5171: ['[門診+住診(急性30天、慢性180天以下)]部分負擔費用累計不合理', None],
    5172: ['門診醫療費用累計不合理', None],
    5173: ['住診醫療費用累計不合理', None],
    6005: ['安全模組卡的外部認證失敗', None],
    6006: ['IDC的外部認證失敗', None],
    6007: ['安全模組卡的內部認證失敗', None],
    6008: ['寫入讀卡機日期時間失敗', None],
    6014: ['IDC 驗證簽章失敗', None],
    6015: ['檔案大小不合或檔案傳輸失敗', None],
    6016: ['記憶體空間不足', None],
    6017: ['權限不足無法開啟檔案或找不到檔案', None],
    6018: ['傳入參數錯誤', None],
    9001: ['送至IDC Message Header 檢核不符', None],
    9002: ['送至IDC語法不符', None],
    9003: ['與IDC作業逾時', None],
    9004: ['IDC異常無法Service', None],
    9010: ['IDC無法驗證該卡片', None],
    9011: ['IDC驗證健保IC卡失敗', None],
    9012: ['IDC無該卡片資料', None],
    9013: ['無效的安全模組卡', None],
    9014: ['IDC對安全模組卡認證失敗', None],
    9015: ['安全模組卡對IDC認證失敗', None],
    9020: ['IDC驗章錯誤', None],
    9030: ['無法執行卡片管理系統的認證', None],
    9040: ['無法執行健保IC卡Applet Perso認證', None],
    9041: ['健保IC卡Applet Perso認證失敗', None],
    9050: ['無法執行安全模組卡世代碼更新認證', None],
    9051: ['安全模組卡世代碼更新認證失敗', None],
    9060: ['安全模組卡遭停約處罰', None],
    9061: ['安全模組卡不在有效期內', None],
    9062: ['安全模組卡合約逾期或尚未生效', None],
    9070: ['上傳資料大小不符無法接收檔案', None],
    9071: ['上傳日期與 Data Center 不一致', None],
    9081: ['卡片可用次數大於3次, 未達可更新標準', '不須執行健保卡卡片內容更新作業'],
    9082: ['此卡已被註銷, 無法進行卡片更新作業', '請改掛健保或自費'],
    9083: ['不在保', '請改掛健保或自費'],
    9084: ['停保中', '請改掛健保或自費'],
    9085: ['已退保', '請改掛健保或自費'],
    9086: ['個人欠費', '請改掛欠卡或自費'],
    9087: ['負責人欠費', None],
    9088: ['投保單位欠費', None],
    9089: ['個人及單位均欠費', None],
    9090: ['欠費且未在保', '請改掛欠卡或自費'],
    9091: ['聲明不實', None],
    9092: ['其他', None],
    9100: ['藥師藥局無權限', None],
    9129: ['持卡人於非限制院所就診', None],
    9130: ['醫事卡失效', None],
    9140: ['醫事卡逾效期', None],
}


BASIC_DATA = {
    'card_no': None,
    'name': None,
    'patient_id': None,
    'birthday': None,
    'gender': None,
    'card_date': None,
    'cancel_mark': None,
    'emg_phone': None,
    'insured_code': None,
    'insured_mark': None,
    'card_valid_date': None,
    'card_available_count': None,
    'new_born_date': None,
    'new_born_mark': None,
}

TREAT_DATA = {
    'registered_date': None,
    'seq_number': None,
    'clinic_id': None,
    'security_signature': None,
    'sam_id': None,
    'register_duplicated': None,
}


# 取得健保讀卡機函數
def get_cshis():
    cshis = None
    if sys.platform == 'win32':
        cshis = ctypes.windll.LoadLibrary('cshis.dll')

    return cshis


def get_treat_item(course):
    treat_item = '03'  # 中醫首次
    course_type = nhi_utils.get_course_type(course)
    if course_type == '療程':
        treat_item = 'AA'

    return treat_item


# 取得卡片註記
def get_cancel_mark(cancel_mark_code):
    cancel_mark = ''

    if cancel_mark_code == '1':
        cancel_mark = '正常卡'
    elif cancel_mark_code == '2':
        cancel_mark = '註銷卡'

    return cancel_mark


# 取得卡片保險身分
def get_insured_mark(insured_mark_code):
    insured_mark = ''

    if insured_mark_code == '1':
        insured_mark = '低收入戶'
    elif insured_mark_code == '2':
        insured_mark = '榮民'
    elif insured_mark_code == '3':
        insured_mark = '基層醫療'

    return insured_mark


def decode_basic_data_common(buffer):
    basic_data_info = BASIC_DATA
    basic_data_info['card_no'] = buffer[:12].decode('ascii').strip()
    basic_data_info['name'] = buffer[12:32].decode('big5').strip()
    basic_data_info['patient_id'] = buffer[32:42].decode('ascii').strip()
    basic_data_info['birthday'] = date_utils.nhi_date_to_west_date(buffer[42:49].decode('ascii').strip())
    basic_data_info['gender'] = patient_utils.get_gender(buffer[49:50].decode('ascii').strip())
    basic_data_info['card_date'] = date_utils.nhi_date_to_west_date(buffer[50:57].decode('ascii').strip())
    basic_data_info['cancel_mark'] = get_cancel_mark(buffer[57:58].decode('ascii').strip())

    return basic_data_info


def decode_basic_data(basic_data):
    basic_data_info = decode_basic_data_common(basic_data)
    basic_data_info['emg_phone'] = basic_data[58:72].decode('ascii').strip()

    return basic_data_info


def decode_register_basic_data(buffer):
    basic_data_info = decode_basic_data_common(buffer)
    basic_data_info['insured_code'] = buffer[58:60].decode('ascii').strip()
    basic_data_info['insured_mark'] = get_insured_mark(buffer[60:61].decode('ascii').strip())
    basic_data_info['card_valid_date'] = date_utils.nhi_date_to_west_date(buffer[61:68].decode('ascii').strip())
    basic_data_info['card_available_count'] = number_utils.get_integer(buffer[68:70].decode('ascii').strip())
    basic_data_info['new_born_date'] = date_utils.nhi_date_to_west_date(buffer[70:77].decode('ascii').strip())
    basic_data_info['new_born_mark'] = buffer[77:78].decode('ascii').strip()

    return basic_data_info


def decode_treat_data(buffer):
    treat_data_info = TREAT_DATA
    treat_data_info['registered_date'] = date_utils.nhi_datetime_to_west_datetime(buffer[:13].decode('ascii').strip())
    treat_data_info['seq_number'] = buffer[13:17].decode('ascii').strip()
    treat_data_info['clinic_id'] = buffer[17:27].decode('ascii').strip()
    treat_data_info['security_signature'] = buffer[27:283].decode('ascii').strip()
    treat_data_info['sam_id'] = buffer[283:295].decode('ascii').strip()
    treat_data_info['register_duplicated'] = buffer[295:296].decode('ascii').strip()

    return treat_data_info


# 顯示讀卡機錯誤
def show_ic_card_message(error_code, process_name=None):
    if process_name is None:
        process_name = '健保讀卡機'

    if error_code == 0:
        icon = QMessageBox.Information
        error_message = '''
        <font size='6'>
        <b>{0}作業成功!</b>
        </font>'''.format(process_name)
        hint = '恭喜您! 順利的完成{0}作業!'.format(process_name)
    else:
        icon = QMessageBox.Critical
        error_message = '''
        <font size='5' color='red'>
          <b>{0}作業失敗, 錯誤代碼: {1}, 錯誤訊息如下:</b><br><br>
        </font>
        <font size='5' color='black'>
          <b>{2}</b>
        </font>
        '''.format(process_name, error_code, ERROR_MESSAGE[error_code][0])
        hint = '{0}'.format(ERROR_MESSAGE[error_code][1])
        if hint is None:
            hint = ''

    msg_box = QMessageBox()
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(process_name)
    msg_box.setText(error_message)
    msg_box.setInformativeText(hint)
    msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
    msg_box.exec_()


def insert_correct_ic_card(database, ic_card, patient_key):
    try:
        if not ic_card.read_basic_data():
            return False
    except AttributeError:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle('無法使用健保卡')
        msg_box.setText(
            '''
            <font size="4" color="red">
              <b>無法使用讀卡機, 請改掛異常卡序或欠卡<br>
            </font>
            '''
        )
        msg_box.setInformativeText("請確定讀卡機使用正常")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()
        return False

    sql = '''
        SELECT * FROM patient WHERE
        PatientKey = {0}
    '''.format(patient_key)
    row = database.select_record(sql)[0]
    if ic_card.basic_data['patient_id'] != string_utils.xstr(row['ID']):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle('健保卡身分不符')
        msg_box.setText(
            '''
            <font size="4" color="red">
              <b>此健保卡基本資料為<br>
              </font>
                <font size="4" color="blue">
                {0}: {1}<br>
                </font>
                <font size="4" color="red">
                與現行掛號病患<br>
                </font>
                <font size="4" color="blue">
                {2}: {3}<br>
                </font>
                <font size="4" color="red">
                身分證號不相符, 請檢查是否插入錯誤的健保卡.</b>
            </font>
            '''.format(ic_card.basic_data['name'],
                       ic_card.basic_data['patient_id'],
                       string_utils.xstr(row['Name']),
                       string_utils.xstr(row['ID']))
        )
        msg_box.setInformativeText("請確定插入的健保卡是否為此病患所有.")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()
        return False

    if string_utils.xstr(row['CardNo']) == '':
        sql = '''
            UPDATE patient SET CardNo = "{0}" WHERE PatientKey = {1}
        '''.format(ic_card.basic_data['card_no'],
                   patient_key)
        database.exec_sql(sql)

    return True


# ic卡寫卡
def write_ic_card(write_type, database, system_settings, patient_key, course, treat_after_check=None):
    treat_item = get_treat_item(course)
    ic_card = cshis.CSHIS(system_settings)
    if not insert_correct_ic_card(
            database,
            ic_card, patient_key):
        return False

    available_date, available_count = ic_card.get_card_status()
    if available_count <= 0:
        ic_card.update_hc(False)

    if write_type in ['全部', '掛號寫卡']:
        if not ic_card.get_seq_number_256(treat_item, ' ', treat_after_check):
            return False

    return ic_card


# 寫入藥品處方簽章
def write_medicine_signature(database, system_settings, case_row, patient_row, prescript_rows, dosage_row):
    registration_datetime = case_utils.extract_security_xml(case_row['Security'], '寫卡時間')
    registration_nhi_datetime = date_utils.west_datetime_to_nhi_datetime(registration_datetime)
    patient_id = string_utils.xstr(patient_row['ID'])
    patient_birthday = string_utils.xstr(patient_row['Birthday'])
    birthday_nhi_datetime = date_utils.west_date_to_nhi_date(patient_birthday)

    usage = (prescript_utils.get_usage_code(dosage_row['Packages']) +
             prescript_utils.get_instruction_code(dosage_row['Instruction']))
    days = number_utils.get_integer(dosage_row['Days'])

    data_write = ''
    for row in prescript_rows:
        try:
            total_dosage = format(row['Dosage'] * dosage_row['Days'], '.1f')
        except TypeError:
            total_dosage = 0

        data_write += '{0}{1}{2}{3}{4}{5}{6}{7}'.format(
            registration_nhi_datetime,                      # 就診日期時間 13 bytes: EEEmmddHHMMSS
            '1',                                            # 醫令類別 1 bytes: 1-非長期藥品 2-長期藥品 3-診療 4-特殊材料
            '{0:<12}'.format(row['InsCode']),               # 診療項目代號 12 bytes
            ' ' * 6,                                        # 診療部位 6 bytes
            '{0:<18}'.format(usage),                        # 用法 18 bytes
            '{0:0>2}'.format(days),                         # 天數 2 bytes: 00
            '{0:0>7}'.format(total_dosage),                 # 總量 7 bytes: 00000.0
            '01',                                           # 交付處方註記 2 bytes: 01-自行調劑 02-交付調劑 03-自行執行
        )

    ic_card = cshis.CSHIS(system_settings)
    prescript_sign_list = ic_card.write_multi_prescript_sign(
        registration_nhi_datetime, patient_id, birthday_nhi_datetime, data_write, len(prescript_rows)
    )

    if prescript_sign_list is None:
        return

    for row, prescript_sign in zip(prescript_rows, prescript_sign_list):
        database.exec_sql(
            'DELETE FROM presextend WHERE PrescriptKey = {0} AND ExtendType = "處方簽章"'.format(row['PrescriptKey'])
        )
        fields = [
            'PrescriptKey', 'ExtendType', 'Content',
        ]
        data = [
            row['PrescriptKey'], '處方簽章', prescript_sign,
        ]
        database.insert_record('presextend', fields, data)


# 寫入處置處方簽章
def write_treat_signature(database, system_settings, case_row, dosage_row, patient_row):
    registration_datetime = case_utils.extract_security_xml(case_row['Security'], '寫卡時間')
    registration_nhi_datetime = date_utils.west_datetime_to_nhi_datetime(registration_datetime)
    patient_id = string_utils.xstr(patient_row['ID'])
    patient_birthday = string_utils.xstr(patient_row['Birthday'])
    birthday_nhi_datetime = date_utils.west_date_to_nhi_date(patient_birthday)

    treat_code = nhi_utils.get_treat_code(string_utils.xstr(case_row['Treatment']), dosage_row)
    usage = ''  # 處置免填
    days = 0
    total_dosage = 1
    data_write = '{0}{1}{2}{3}{4}{5}{6}{7}'.format(
        registration_nhi_datetime,                      # 就診日期時間 13 bytes: EEEmmddHHMMSS
        '3',                                            # 醫令類別 1 bytes: 1-非長期藥品 2-長期藥品 3-診療 4-特殊材料
        '{0:<12}'.format(treat_code),                   # 診療項目代號 12 bytes
        ' ' * 6,                                        # 診療部位 6 bytes
        '{0:<18}'.format(usage),                         # 用法 18 bytes
        '{0:0>2}'.format(days),                         # 天數 2 bytes: 00
        '{0:0>7}'.format(total_dosage),                 # 總量 7 bytes: 00000.0
        '03',                                           # 交付處方註記 2 bytes: 01-自行調劑 02-交付調劑 03-自行執行
    )
    print(data_write)

    ic_card = cshis.CSHIS(system_settings)
    treat_sign = ic_card.write_prescript_sign(
        registration_nhi_datetime, patient_id, birthday_nhi_datetime, data_write,
    )

    if treat_sign is None:
        return

    database.exec_sql(
        'DELETE FROM presextend WHERE PrescriptKey = {0} AND ExtendType = "處置簽章"'.format(case_row['CaseKey'])
    )
    fields = [
        'PrescriptKey', 'ExtendType', 'Content',
    ]
    data = [
        case_row['CaseKey'], '處置簽章', treat_sign,
    ]
    database.insert_record('presextend', fields, data)


# 寫入病名及費用
def write_ic_treatment(database, system_settings, case_key, treat_after_check):
    ic_card = cshis.CSHIS(system_settings)

    sql = '''
        SELECT PatientKey, DiseaseCode1, DiseaseCode2, DiseaseCode3, 
        DiagShareFee, DrugShareFee, InsTotalFee, Security FROM cases WHERE
        CaseKey = {0} 
    '''.format(case_key)
    case_row = database.select_record(sql)[0]

    sql = '''
        SELECT ID, Birthday FROM patient WHERE
        PatientKey = {0} 
    '''.format(case_row['PatientKey'])
    patient_row = database.select_record(sql)[0]

    registration_datetime = case_utils.extract_security_xml(case_row['Security'], '寫卡時間')
    registration_nhi_datetime = date_utils.west_datetime_to_nhi_datetime(registration_datetime)
    patient_id = string_utils.xstr(patient_row['ID'])
    patient_birthday = string_utils.xstr(patient_row['Birthday'])
    birthday_nhi_datetime = date_utils.west_date_to_nhi_date(patient_birthday)

    disease_code1 = string_utils.xstr(case_row['DiseaseCode1'])
    disease_code2 = string_utils.xstr(case_row['DiseaseCode2'])
    disease_code3 = string_utils.xstr(case_row['DiseaseCode3'])
    data_write = '{0}{1}{2}{3}{4}{5}{6}'.format(
        treat_after_check,
        '{0:<7}'.format(disease_code1),
        '{0:<7}'.format(disease_code2),
        '{0:<7}'.format(disease_code3),
        ' ' * 7,
        ' ' * 7,
        ' ' * 7,
    )
    doctor_id = ic_card.write_treatment_code(registration_nhi_datetime, patient_id, birthday_nhi_datetime, data_write)

    ins_total_fee = string_utils.xstr(case_row['InsTotalFee'])
    share_fee = string_utils.xstr(
        (number_utils.get_integer(case_row['DiagShareFee']) +
         number_utils.get_integer(case_row['DrugShareFee']))
    )
    data_write = '{0}{1}{2}{3}{4}'.format(
        '{0:0>8}'.format(ins_total_fee),
        '{0:0>8}'.format(share_fee),
        '0' * 8,
        '0' * 7,
        '0' * 7,
        )
    ic_card.write_treatment_fee(registration_nhi_datetime, patient_id, birthday_nhi_datetime, data_write)

    return doctor_id

# 寫入處方簽章
def write_prescript_signature(database, system_settings, case_key):
    sql = '''
        SELECT CaseKey, PatientKey, Treatment, Security FROM cases WHERE
        CaseKey = {0} 
    '''.format(case_key)
    case_row = database.select_record(sql)[0]

    sql = '''
        SELECT * FROM dosage WHERE
        CaseKey = {0} AND MedicineSet = 1 
    '''.format(case_key)
    rows = database.select_record(sql)
    dosage_row = rows[0] if len(rows) > 0 else None

    sql = '''
        SELECT ID, Birthday FROM patient WHERE
        PatientKey = {0} 
    '''.format(case_row['PatientKey'])
    patient_row = database.select_record(sql)[0]

    sql = '''
        SELECT * FROM prescript WHERE
        CaseKey = {0} AND MedicineSet = 1 AND InsCode IS NOT NULL
    '''.format(case_key)
    prescript_rows = database.select_record(sql)

    if string_utils.xstr(case_row['Treatment']) in nhi_utils.INS_TREAT:
        write_treat_signature(database, system_settings, case_row, dosage_row, patient_row)

    if len(prescript_rows) > 0:
        write_medicine_signature(database, system_settings, case_row, patient_row, prescript_rows, dosage_row)
