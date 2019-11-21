
from registration import *
from reservation import *
from return_card import *
from income import *
from purchase_list import *
from purchase import *
from debt import *
from patient_list import *
from ic_record_upload import *

from cashier import *
from waiting_list import *
from medical_record import *
from examination_list import *
from examination import *

from charge_settings import *
from users import *
from doctor_schedule import *
from doctor_nurse_table import *
from dict_diagnostic import *
from dict_medicine import *
from dict_misc import *
from dict_ins_drug import *

from medical_record_list import *
from patient import *

from restore_records import *

from ins_check import *
from ins_apply import *
from ins_judge import *

from certificate_diagnosis import *
from certificate_payment import *

from statistics_medical_record import *
from statistics_doctor import *
from statistics_return_rate import *
from statistics_medicine import *
from statistics_ins_performance import *
from statistics_doctor_performance import *
from statistics_doctor_commission import *
from massage_registration import *


module_dict = {
    '門診掛號': Registration,
    '預約掛號': Reservation,
    '批價作業': Cashier,
    '健保卡欠還卡': ReturnCard,
    '欠還款作業': Debt,
    '櫃台購藥': PurchaseList,
    '購買商品': Purchase,
    '掛號櫃台結帳': Income,
    '病患查詢': PatientList,
    '健保IC卡資料上傳': ICRecordUpload,

    '醫師看診作業': WaitingList,
    '病歷資料': MedicalRecord,
    '病歷統計': StatisticsMedicalRecord,
    '檢驗報告查詢': ExaminationList,
    '檢驗報告登錄': Examination,

    '收費設定': ChargeSettings,
    '醫師班表': DoctorSchedule,
    '護士跟診表': DoctorNurseTable,
    '使用者管理': Users,
    '診察資料': DictDiagnostic,
    '處方資料': DictMedicine,
    '其他資料': DictMisc,
    '健保藥品': DictInsDrug,

    '病歷查詢': MedicalRecordList,
    '病患資料': Patient,

    '申報檢查': InsCheck,
    '健保申報': InsApply,
    '健保抽審': InsJudge,

    '診斷證明書': CertificateDiagnosis,
    '醫療費用證明書': CertificatePayment,

    '醫師統計': StatisticsDoctor,
    '回診率統計': StatisticsReturnRate,
    '用藥統計': StatisticsMedicine,
    '健保申報業績': StatisticsInsPerformance,
    '醫師銷售業績統計': StatisticsDoctorPerformance,

    '資料回復': RestoreRecords,

    '養生館掛號': MassageRegistration,
}


def get_module_name(tab_name):
    if tab_name.find('病歷資料') != -1:
        tab_name = '病歷資料'
    elif tab_name.find('病患資料') != -1:
        tab_name = '病患資料'
    elif tab_name.find('檢驗報告-') != -1:
        tab_name = '檢驗報告登錄'
    elif tab_name.find('醫療費用證明書-') != -1:
        tab_name = '醫療費用證明書'

    return module_dict[tab_name]
