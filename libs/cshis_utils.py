# 2018.04.30
from PyQt5.QtWidgets import QMessageBox, QPushButton

import io
from libs import date_utils
from libs import patient_utils
from libs import number_utils
from libs import nhi_utils
from libs import string_utils

NORMAL_CARD = '1'
RETURN_CARD = '2'

ERROR_MESSAGE = {
    4000: ['讀卡機timeout', '請檢查讀卡機連接埠是否接妥, 或是系統設定->讀卡機連接埠是否正確'],
    4012: ['未置入安全模組卡', '安全模組可能未正確安裝至讀卡機內, 請關掉讀卡機電源, 打開螺絲背蓋, 檢查安全模組卡是否安裝妥當.'],
    4013: ['未置入健保IC卡', '請確定健保IC卡已經正確的插入讀卡機'],
    4014: ['未置入醫事人員卡', '請插入醫事人員卡'],
    4029: ['IC卡權限不足', None],
    4032: ['所插入非安全模組卡', None],
    4033: ['所置入非健保IC卡', None],
    4034: ['所置入非醫事人員卡', None],
    4042: ['醫事人員卡PIN尚未認證成功', None],
    4043: ['健保卡讀取/寫入作業異常', None],
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
    5069: ['兒童預防保健服務紀錄寫入孕婦產檢欄位失敗', None],
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
    9101: ['所置入非醫師卡', None],
    9129: ['持卡人於非限制院所就診', None],
    9130: ['醫事卡失效', None],
    9140: ['醫事卡逾效期', None],

    9200: ['安全模組檔目錄錯誤或不存在或數量超過一個以上', None],
    9201: ['初始安全模組檔讀取異常，請在C:\\NHI\\SAM\\COMX1目錄下放置健保署正確安全模組檔', None],
    9202: ['安全模組檔讀取異常，已在其它電腦使用過，請在C:\\NHI\\SAM\\COMX1目錄下放置健保署正確安全模組檔。', None],
    9203: ['卡片配對錯誤，正式卡與測試卡不能混用', None],
    9204: ['找不到讀卡機，或PCSC環境異常', None],
    9205: ['開啟讀卡機連結埠失敗', None],
    9210: ['健保IC卡內部認證失敗', None],
    9211: ['雲端安全模組(IDC)對健保IC卡認證失敗', None],
    9212: ['健保IC卡對雲端安全模組認證失敗', None],
    9213: ['雲端安全模組卡片更新逾時', None],
    9220: ['醫事人員卡內部認證失敗', None],
    9221: ['雲端安全模組(IDC)驗證醫事人員卡失敗', None],
    9230: ['安全模組檔「醫療院所名稱」讀取失敗', None],
    9231: ['安全模組檔「醫療院所簡稱」讀取失敗', None],
    9240: ['雲端安全模組主控台沒起動 ', None],
    9999: ['找不到醫事人員卡讀卡機', None],
}

INSURED_MARK_DICT = {
    '1': '低收入戶',
    '2': '榮民',
    '3': '基層醫療',
    '8': '災民',
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

TREATMENT_DATA = {
    'critical_illness': [],
    'treatments': [],
}

XML_FEEDBACK_DATA = {
    'sam_id': None,
    'clinic_id': None,
    'upload_time': None,
    'receive_time': None,
}


UPLOAD_TYPE_DICT = {
    None: '',
    '': '',
    '0': '0-尚未上傳',
    '1': '1-正常上傳',
    '2': '2-異常上傳',
    '3': '3-正常補正',
    '4': '4-異常補正',
}

TREAT_AFTER_CHECK_DICT = {
    None: '',
    '': '',
    '1': '1-正常',
    '2': '2-補卡',
}


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
    try:
        insured_mark = INSURED_MARK_DICT[insured_mark_code]
    except:
        insured_mark = '基層醫療'

    return insured_mark


# 取得健保卡內容
def decode_basic_data_common(buffer):
    basic_data_info = BASIC_DATA
    basic_data_info['card_no'] = buffer[:12].decode('ascii').strip()
    basic_data_info['name'] = buffer[12:32].decode('big5', 'replace').strip()
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
    basic_data_info['insured_code'] = buffer[58:60].decode('ascii').strip()  # Reserved, not use
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


def decode_treatment_data(buffer):
    treatment_data = TREATMENT_DATA
    treatment_data['critical_illness'].clear()
    treatment_data['treatments'].clear()

    s = io.BytesIO(buffer)
    for x in range(6):
        treatment_data['critical_illness'].append({
            'ci_validity_start': s.read(7).decode('ascii'),
            'ci_validity_end': s.read(7).decode('ascii')
        })

    for x in range(6):
        item = {}
        item['treat_item'] = s.read(2).decode('ascii')
        item['treat_newborn'] = s.read(1).decode('ascii')
        item['treat_date_time'] = s.read(13).decode('ascii')
        item['treat_after_check'] = s.read(1).decode('ascii')
        item['card'] = s.read(4).decode('ascii')
        item['treat_hosp_code'] = s.read(10).decode('ascii')
        item['treat_ot_tot_fee'] = int(s.read(8).decode('ascii'))
        item['hc_treat_ot_co_fee'] = int(s.read(8).decode('ascii'))
        item['treat_ot_inpa_fee'] = int(s.read(8).decode('ascii'))
        item['treat_ot_inpa_30'] = int(s.read(7).decode('ascii'))
        item['treat_ot_inpa_180'] = int(s.read(7).decode('ascii'))

        treatment_data['treatments'].append(item)

    return treatment_data


def decode_xml_data(buffer):
    xml_feedback_data_info = XML_FEEDBACK_DATA

    xml_feedback_data_info['sam_id'] = buffer[:12].decode('ascii').strip()
    xml_feedback_data_info['clinic_id'] = buffer[12:22].decode('ascii').strip()
    xml_feedback_data_info['upload_time'] = '{0}-{1}-{2} {3}:{4}:{5}'.format(
        buffer[22:26].decode('ascii').strip(),
        buffer[26:28].decode('ascii').strip(),
        buffer[28:30].decode('ascii').strip(),
        buffer[30:32].decode('ascii').strip(),
        buffer[32:34].decode('ascii').strip(),
        buffer[34:36].decode('ascii').strip(),
    )
    xml_feedback_data_info['receive_time'] = '{0}-{1}-{2} {3}:{4}:{5}'.format(
        buffer[36:40].decode('ascii').strip(),
        buffer[40:42].decode('ascii').strip(),
        buffer[42:44].decode('ascii').strip(),
        buffer[44:46].decode('ascii').strip(),
        buffer[46:48].decode('ascii').strip(),
        buffer[48:50].decode('ascii').strip(),
    )

    return xml_feedback_data_info


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


def get_host_name(database, hosp_id):
    sql = '''
        SELECT * FROM hospid
        WHERE
            HospID = "{hosp_id}"    
    '''.format(
        hosp_id=hosp_id,
    )

    rows = database.select_record(sql)
    if len(rows) <= 0:
        return hosp_id

    return string_utils.xstr(rows[0]['HospName'])


def get_treatments_html(database, treatment_data):
    treatments = treatment_data['treatments']
    if len(treatments) <= 0:
        return '<br><br><br><center>無健保卡就醫資料</center>'

    records = ''
    for row_no, treatment in zip(range(1, len(treatments)+1), treatments):
        treat_item = string_utils.xstr(treatment['treat_item']).strip()
        treat_date_time = string_utils.xstr(treatment['treat_date_time']).strip()
        treat_after_check = string_utils.xstr(treatment['treat_after_check']).strip()
        card = string_utils.xstr(treatment['card']).strip()
        treat_hosp_code = string_utils.xstr(treatment['treat_hosp_code']).strip()

        try:
            treat_item = nhi_utils.TREAT_ITEM[treat_item]
        except KeyError:
            pass

        try:
            treat_date_time = date_utils.nhi_datetime_to_west_datetime(treat_date_time)
        except ValueError:
            treat_date_time = ''

        if treat_after_check == '1':
            treat_after_check = '正常'
        else:
            treat_after_check = '補卡'

        card = card.zfill(4)
        hosp_name = get_host_name(database, treat_hosp_code)

        records += '''
            <tr>
                <td align="center">{row_no}</td>
                <td align="center">{treat_item}</td>
                <td>{treat_date_time}</td>
                <td align="center">{treat_after_check}</td>
                <td align="center">{card}</td>
                <td>{hosp_name}</td>
            </tr>
        '''.format(
            row_no=row_no,
            treat_item=treat_item,
            treat_date_time=treat_date_time,
            treat_after_check=treat_after_check,
            card=card,
            hosp_name=hosp_name,
        )

    html = '''
        <table align=center cellpadding="2" cellspacing="0" width="98%" style="border-width: 1px; border-style: solid;">
            <thead>
                <tr bgcolor="LightGray">
                    <th style="text-align: center; padding-left: 8px" width="5%">序</th>
                    <th style="padding-left: 8px" width="15%" align="center">類別</th>
                    <th style="padding-right: 8px" align="center" width="25%">就醫日期</th>
                    <th style="padding-left: 8px" align="center" width="10%">讀卡</th>
                    <th style="padding-left: 8px" align="center" width="10%">卡序</th>
                    <th style="padding-left: 8px" align="center" width="35%">就醫院所</th>
                </tr>
            </thead>
            <tbody>
                {records}
            </tbody>
        </table>
    '''.format(
        records=records,
    )

    return html
