
from registration import *
from waiting_list import *
from medical_record import *
from template import *
from medical_record_list import *
from patient_list import *
from patient import *
from return_card import *
from charge_settings import *
from dict_diagnostic import *
from dict_medicine import *
from users import *

module_dict = {
    '門診掛號': Registration,
    '健保卡欠還卡': ReturnCard,
    '掛號櫃台結帳': Template,
    '醫師看診作業': WaitingList,
    '病歷查詢': MedicalRecordList,
    '病歷資料': MedicalRecord,
    '病歷統計': Template,
    '病患查詢': PatientList,
    '病患資料': Patient,
    '使用者管理': Users,
    '收費設定': ChargeSettings,
    '診察資料': DictDiagnostic,
    '處方資料': DictMedicine,
}


def get_module_name(tab_name):
    if tab_name.find('病歷資料') != -1:
        tab_name = '病歷資料'
    elif tab_name.find('病患資料') != -1:
        tab_name = '病患資料'

    return module_dict[tab_name]