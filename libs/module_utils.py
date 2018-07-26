
from registration import *
from return_card import *
from patient_list import *
from ic_record_upload import *

from waiting_list import *
from medical_record import *

from charge_settings import *
from users import *
from dict_diagnostic import *
from dict_medicine import *

from medical_record_list import *
from patient import *

from ins_check import *
from ins_apply import *
from ins_judge import *

from template import *

module_dict = {
    '門診掛號': Registration,
    '批價作業': Template,
    '健保卡欠還卡': ReturnCard,
    '掛號櫃台結帳': Template,
    '病患查詢': PatientList,
    '健保IC卡資料上傳': ICRecordUpload,

    '醫師看診作業': WaitingList,
    '病歷資料': MedicalRecord,
    '病歷統計': Template,

    '收費設定': ChargeSettings,
    '使用者管理': Users,
    '診察資料': DictDiagnostic,
    '處方資料': DictMedicine,

    '病歷查詢': MedicalRecordList,
    '病患資料': Patient,

    '申報預檢': InsCheck,
    '健保申報': InsApply,
    '健保抽審': InsJudge,
}


def get_module_name(tab_name):
    if tab_name.find('病歷資料') != -1:
        tab_name = '病歷資料'
    elif tab_name.find('病患資料') != -1:
        tab_name = '病患資料'

    return module_dict[tab_name]
