
# 讀卡機作業 2018.05.03
from PyQt5 import QtCore
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMessageBox, QPushButton

import ctypes
import os

from threading import Thread
from queue import Queue

from libs import number_utils
from libs import date_utils
from libs import cshis_utils
from libs import case_utils
from libs import prescript_utils
from libs import string_utils
from libs import nhi_utils
from libs import system_utils


# 健保ICD卡 2018.03.31
class CSHIS:
    def __init__(self, database, system_settings):
        self.database = database
        self.com_port = number_utils.get_integer(system_settings.field('健保卡讀卡機連接埠')) - 1  # com1=0, com2=1, com3=2,...
        try:
            self.cshis = ctypes.cdll.LoadLibrary('/nhi/lib/cshis50.so')
        except OSError as e:
            system_utils.show_message_box(
                QMessageBox.Critical,
                'OSError',
                '<font size="4" color="red"><b>{error_message}</b></font>'.format(error_message=e),
                '函式錯誤, 找不到此函式.'
            )
            self.cshis = None

        self.basic_data = cshis_utils.BASIC_DATA
        self.treat_data = cshis_utils.TREAT_DATA

    def __del__(self):
        if self.cshis is not None:
            self._close_com()

    def _open_com(self):
        com_port = ctypes.c_short(self.com_port)
        self.cshis.csOpenCom(com_port)

    def _close_com(self):
        self.cshis.csCloseCom()

    @staticmethod
    def _message_box(title, message, hint):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setInformativeText(hint)
        msg_box.setStandardButtons(QMessageBox.NoButton)

        return msg_box

    def do_thread(self, nhi_thread, *args):
        msg_box = None
        try:
            operation = args[0]
        except IndexError:
            operation = None

        if operation:
            msg_box = self._message_box('健保讀卡機作業', args[1], args[2])
            msg_box.show()

        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()
        t = Thread(target=nhi_thread, args=(msg_queue, ))
        t.start()
        error_code = msg_queue.get()
        if msg_box:
            msg_box.close()

        cshis_utils.show_ic_card_message(error_code, operation)

    def verify_sam_thread(self, out_queue):
        self._open_com()
        error_code = self.cshis.csVerifySAMDC()
        self._close_com()
        out_queue.put(error_code)

    def verify_sam(self):
        self.do_thread(
            self.verify_sam_thread,
            '健保讀卡機安全模組卡認證',
            '<font size="4" color="red"><b>健保讀卡機安全模組卡認證中, 請稍後...</b></font>',
            '正在與健保IDC資訊中心連線, 會花費一些時間.'
        )

    def update_hc(self,  show_message=True):
        error_code = 0

        self._open_com()
        try:
            error_code = self.cshis.csUpdateHCContents()
        except:
            pass
        finally:
            self._close_com()

        if show_message or error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保IC卡卡片內容更新')

    def verify_hc_pin(self):
        self._open_com()
        error_code = self.cshis.csVerifyHCPIN()
        self._close_com()
        cshis_utils.show_ic_card_message(error_code, '健保IC卡密碼驗證')

    def input_hc_pin(self):
        self._open_com()
        error_code = self.cshis.csInputHCPIN()
        self._close_com()
        cshis_utils.show_ic_card_message(error_code, '健保IC卡密碼設定')

    def disable_hc_pin(self):
        self._open_com()
        error_code = self.cshis.csDisableHCPIN()
        self._close_com()
        cshis_utils.show_ic_card_message(error_code, '健保IC卡密碼解除')

    def verify_hpc_pin(self):
        self._open_com()
        error_code = self.cshis.hpcVerifyHPCPIN()
        self._close_com()
        cshis_utils.show_ic_card_message(error_code, '醫事人員卡密碼驗證')

    def input_hpc_pin(self):
        self._open_com()
        error_code = self.cshis.hpcInputHPCPIN()
        self._close_com()
        cshis_utils.show_ic_card_message(error_code, '醫事人員卡密碼設定')

    def unlock_hpc(self):
        self._open_com()
        error_code = self.cshis.hpcUnlockHPC()
        self._close_com()
        cshis_utils.show_ic_card_message(error_code, '醫事人員卡密碼解鎖')

    def reset_reader(self):
        self._open_com()
        error_code = self.cshis.csSoftwareReset(0)  # 0=讀卡機, 1=安全模組, 2=醫事人員卡, 3=健保卡
        self._close_com()
        cshis_utils.show_ic_card_message(error_code, '讀卡機重新啟動')

    def read_basic_data(self):
        buffer_size = 72
        buffer = ctypes.c_buffer(buffer_size)  # c: char *
        buffer_len = ctypes.c_short(buffer_size)  # c: int *
        self._open_com()
        error_code = self.cshis.hisGetBasicData(buffer, ctypes.byref(buffer_len))
        self._close_com()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡讀取')
            return False

        self.basic_data = cshis_utils.decode_basic_data(buffer)

        return True

    def read_register_basic_data(self):
        buffer_size = 78
        buffer = ctypes.create_string_buffer(buffer_size)  # c: char *
        buffer_len = ctypes.c_short(buffer_size)  # c: int *
        self._open_com()
        error_code = self.cshis.hisGetRegisterBasic(buffer, ctypes.byref(buffer_len))
        self._close_com()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡讀取')
            return False

        self.basic_data = cshis_utils.decode_register_basic_data(buffer)

        return True

    def get_card_status(self):
        available_count = None
        available_date = None
        buffer_size = 9
        buffer = ctypes.create_string_buffer(buffer_size)  # c: char *
        buffer_len = ctypes.c_short(buffer_size)  # c: int *
        self._open_com()
        error_code = self.cshis.hisGetRegisterBasic2(buffer, ctypes.byref(buffer_len))
        self._close_com()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡讀取')
            return available_date, available_count

        available_date = date_utils.nhi_date_to_west_date(buffer[:7].decode('ascii').strip())
        available_count = number_utils.get_integer(buffer[7:9].decode('ascii').strip())

        return available_date, available_count

    '''
    取得健保卡就醫序號
    hisGetSeqNumber256(
        char *cTreatItem            [in] cTreatItem為就醫類別(HC健8-1)，為英數字，長度需可存放三個char(包括尾端之\0)。
                                        須累計就醫序號及扣除可用次數之代號: 
                                            01=西醫門診
                                            02=牙醫門診
                                            03=中醫門診
                                            04=急診
                                            05=住院
                                        不須累計就醫序號及不扣除可用次數之代號: 
                                            AA=同一 療程之項目以六次以內治療為 限者
                                            AB=以同一療程之項目屬"非"六次以內治療為限者
                                            AC=預防保健
                                            AD=職業傷害或職業病
                                            AE=慢性病連續處方箋領藥
                                            AF=藥局調劑
                                            AG=排程檢查
                                            AH=居家照護（第二次以 後）
                                            AI=同日同醫師看診（第二次以後）
                                            BA=門（急）診當次轉住院之入院
                                            BB=出院
                                            BC=急診中、住院中執行項目
                                            BD=急診第二日﹝含﹞以後之離院
                                            BE=職業傷害或職業病之住院
                                            CA=其他規定不須累計就醫序號即不扣除就醫次數者
        char *cBabyTreat            [in] cBabyTreat為新生兒就醫註記(HC健8-2)，為英數字，長度需可存放兩個char(包括尾端之\0)。
        char *cTreatAfterCheck      [in] cTreatAfterCheck為補卡註記，傳入'1'表正常、'2'表補卡，長度需可存放一個char
        char *pBuffer               [out] pBuffer，為HIS準備之buffer，需可存入「pBuffer回傳內容」所稱之欄位值。
                                          回傳內容及順序如下: 共296 Bytes
                                          就診日期時間(1-13)
                                          就醫序號(14-17)
                                          醫療院所代碼(18-27)
                                          安全簽章(28-283) (此256Bytes為安全簽章為RSA所產生之亂數，再經過轉換所呈現之數值)
                                          SAM ID(284-295)
                                          是否同日就診(296)，'Y'表同日就診，'N'表非同日就診
                                          
                                          欄位存入的順序，如「pBuffer回傳內容」所述。
                                          1-13    就診日期時間  13 bytes EEEMMDDHHNNSS  EEE=民國年
                                          14-17   就醫序號      4 bytes
                                          18-27   院所代號     10 bytes
                                          28-283  安全簽章    256 bytes
                                          284-295 SAM ID      10 bytes
                                          296     是否同日就診   1 bytes  Y=是 N=否
           int * iBufferLen)        [in/out] iBufferLen，為HIS準備之buffer，HIS呼叫此API時，傳入準備的buffer長度；
                                             CS亦利用此buffer傳出填入到buffer中的資料長度(buffer的尾端不必補\0)。
    '''
    def get_seq_number_256_thread(self, out_queue, treat_item, baby_treat, treat_after_check):
        p_treat_item = ctypes.c_char_p(treat_item.encode('ascii'))
        p_baby_treat = ctypes.c_char_p(baby_treat.encode('ascii'))
        p_treat_after_check = ctypes.c_char_p(treat_after_check.encode('ascii'))
        buffer_size = 296
        buffer = ctypes.c_buffer(buffer_size)  # c: char *
        buffer_len = ctypes.c_short(buffer_size)  # c: short *
        self._open_com()
        error_code = self.cshis.hisGetSeqNumber256(
            p_treat_item,
            p_baby_treat,
            p_treat_after_check,
            buffer,
            ctypes.byref(buffer_len))
        self._close_com()

        out_queue.put((error_code, buffer))

    # 取得安全簽章
    def get_seq_number_256(self, treat_item, baby_treat, treat_after_check):
        title = '取得掛號安全簽章'
        message = '<font size="4" color="red"><b>健保讀卡機取得掛號安全簽章中, 請稍後...</b></font>'
        hint = '正在與與健保IDC資訊中心連線, 會花費一些時間.'
        msg_box = self._message_box(title, message, hint)
        msg_box.show()

        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()

        t = Thread(target=self.get_seq_number_256_thread, args=(msg_queue, treat_item, baby_treat, treat_after_check, ))
        t.start()
        (error_code, buffer) = msg_queue.get()
        msg_box.close()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡取得就醫序號')
            return False

        self.treat_data = cshis_utils.decode_treat_data(buffer)
        return True

    '''
    就醫費用資料寫入作業
    hisWriteTreatmentFee(
        char * pDateTime            [in] pDateTime: 傳入之「就診日期時間」(HC健8-3)，長度14 bytes(含null char)。
        char * pPatientID           [in] pPatientID: 傳入之民眾「身分證號」(HC基3)，長度11 bytes(含null char)。
        char * pPatientBirthDate    [in] pPatientBirthDate: 傳入之民眾「出生日期」(HC基4)，長度8 bytes(含null char)。
        char * pDataWrite           [in] pDataWrite: 傳入欲寫入之資料
                                         其順序內容如下:
                                         門診醫療費用【當次】(1-8)
                                         門診部分負擔費用【當次】(9-16)
                                         住院醫療費用【當次】(17-24)
                                         住院部分負擔費用【當次急性30天， 慢性180天以下】(25-31)
                                         住院部分負擔費用【當次急性31天， 慢性181天以上】(32-38)
                                         各欄位資料往左靠，不足處補空白，長度依卡片存放內容規定。
    '''
    def write_treatment_fee_thread(
            self, out_queue, registration_datetime, patient_id, patient_birthday, data_write):
        p_registration_datetime = ctypes.c_char_p(registration_datetime.encode('ascii'))
        p_patient_id = ctypes.c_char_p(patient_id.encode('ascii'))
        p_patient_birthday = ctypes.c_char_p(patient_birthday.encode('ascii'))
        p_data_write = ctypes.c_char_p(data_write.encode('ascii'))

        self._open_com()
        error_code = self.cshis.hisWriteTreatmentFee(
            p_registration_datetime,
            p_patient_id,
            p_patient_birthday,
            p_data_write,
        )
        self._close_com()

        out_queue.put(error_code)

    # 就醫費用資料寫入作業
    def write_treatment_fee(self, registration_datetime, patient_id, patient_birthday, data_write):
        title = '寫入診察費用資料'
        message = '<font size="4" color="red"><b>健保讀卡機正在寫入診察費用資料中, 請稍後...</b></font>'
        hint = '正在與與健保IDC資訊中心連線, 會花費一些時間.'
        msg_box = self._message_box(title, message, hint)
        msg_box.show()
        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()
        t = Thread(target=self.write_treatment_fee_thread,
                   args=(msg_queue, registration_datetime, patient_id, patient_birthday, data_write, ))
        t.start()
        error_code = msg_queue.get()
        msg_box.close()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡寫入診察費用資料')
            return None

        return True

    '''
        進行疾病診斷碼押碼
        hisGetICD10EnC(
        char * IN                   [in] 為呼叫者傳入的原始診斷碼 押碼範圍：ICD-10 CM 疾病診斷碼長度超過 5 Bytes
                                         及字母｢E｣、｢V｣開頭的診斷碼
        char * OUT                  [out] 為呼叫者所準備之buffer，供CS填入押碼後的診斷碼 5 bytes
    '''
    def get_icd10_encode(self, disease_code):
        p_disease_code = ctypes.c_char_p(disease_code.encode('ascii'))
        icd10_encoding = ctypes.create_string_buffer(5)  # c: char *
        self._open_com()
        error_code = self.cshis.hisGetICD10EnC(
            p_disease_code,
            icd10_encoding,
        )
        self._close_com()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, 'ICD10病名碼押碼')
            return None

        return icd10_encoding[:5].decode('ascii').strip()
    '''
    就醫診療資料寫入作業
    hisWriteTreatmentCode(
        char * pDateTime            [in] pDateTime: 傳入之「就診日期時間」(HC健8-3)，長度14 bytes(含null char)。
        char * pPatientID           [in] pPatientID: 傳入之民眾「身分證號」(HC基3)，長度11 bytes(含null char)。
        char * pPatientBirthDate    [in] pPatientBirthDate: 傳入之民眾「出生日期」(HC基4)，長度8 bytes(含null char)。
        char * pDataWrite           [in] pDataWrite: 傳入欲寫入之資料，自控制軟體3.3版起，傳入pDataWrite增加定義ICD-10 CM格式，
                                         控制軟體藉由辨識傳入pDataWrite內含特殊辨識字串認定HIS將以 ICD-10 CM 格式寫入資料，
                                         辨識字串內容請參考範例程式。 
                                         
                                         以ICD-10 CM格式寫入及其順序內容如下:
                                         補卡註記[HC健8-4] (1)             1 bytes補卡註記 1: 正常 2: 補卡
                                         主要診斷碼[HC健8-8] (3-9)         7 bytes
                                         次要診斷碼[HC健8-9] 第1組 (12-18)  7 bytes
                                         次要診斷碼[HC健8-9] 第2組 (21-27)  7 bytes
                                         次要診斷碼[HC健8-9] 第3組 (30-36)  7 bytes
                                         次要診斷碼[HC健8-9] 第4組 (39-45)  7 bytes
                                         次要診斷碼[HC健8-9] 第5組 (48-54)  7 bytes
                                         資料皆往左靠，不足處補空白。pDataWrite尾隨一個null char。
        char * pBufferDocID)        [out] pBufferDocID: 傳回HPC之身分證號欄位(醫事人員卡之醫師基本資料段)及尾隨之一個null char
                                          buffer 大小至少11 bytes。若讀卡機內無HPC卡，則pBufferDocID存入null char。
    '''
    def write_treatment_code_thread(
            self, out_queue, registration_datetime, patient_id, patient_birthday, data_write):
        p_registration_datetime = ctypes.c_char_p(registration_datetime.encode('ascii'))
        p_patient_id = ctypes.c_char_p(patient_id.encode('ascii'))
        p_patient_birthday = ctypes.c_char_p(patient_birthday.encode('ascii'))
        p_data_write = ctypes.c_char_p(data_write.encode('ascii'))

        doctor_id = ctypes.create_string_buffer(10)  # c: char *
        self._open_com()
        error_code = self.cshis.hisWriteTreatmentCode(
            p_registration_datetime,
            p_patient_id,
            p_patient_birthday,
            p_data_write,
            doctor_id,
        )
        self._close_com()

        out_queue.put((error_code, doctor_id))

    # 就醫診療資料寫入作業
    def write_treatment_code(self, registration_datetime, patient_id, patient_birthday, data_write):
        title = '寫入診察資料'
        message = '<font size="4" color="red"><b>健保讀卡機正在寫入診察資料中, 請稍後...</b></font>'
        hint = '正在與與健保IDC資訊中心連線, 會花費一些時間.'
        msg_box = self._message_box(title, message, hint)
        msg_box.show()
        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()
        t = Thread(target=self.write_treatment_code_thread,
                   args=(msg_queue, registration_datetime, patient_id, patient_birthday, data_write, ))
        t.start()
        (error_code, out_doctor_id) = msg_queue.get()
        msg_box.close()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡寫入診察資料')
            return None

        doctor_id = out_doctor_id[:40].decode('ascii')

        return doctor_id

    '''
    處方箋寫入作業-回傳簽章
    hisWritePrescriptionSign(
        char * pDateTime            [in] 傳入之「就診日期時間」(HC健8-3)，長度14 bytes(含null char)
        char * pPatientID           [in] 傳入之民眾「身分證號」(HC基3)，長度11 bytes(含null char)
        char * pPatientBirthDate    [in] pPatientBirthDate: 傳入之民眾「出生日期」(HC基4)，長度8 bytes(含null char)
        char * pDataWrite           [in] pDataWrite: 傳入欲寫入一組門診處方箋之資料
                                         順序內容如下: 
                                         就診日期時間(1-13)
                                         醫令類別(14)
                                         診療項目代號(15-26)
                                         診療部位(27-32)
                                         用法(33-50)
                                         天數(51-52)
                                         總量(53-59)
                                         交付處方註記(60-61)
        char * pBuffer              [out] pBuffer: 為HIS準備之buffer，需可存入「pBuffer回傳內容」所稱之欄位值。
        int * iBufferLen)           [in/out] iBufferLen: HIS所準備buffer之長度，HIS呼叫此API時，傳入準備的buffer長度；
        欄位存入的順序，如「pBuffer回傳內容」所述
    '''
    def write_prescript_sign_thread(
            self, out_queue, registration_datetime, patient_id, patient_birthday, data_write):
        p_registration_datetime = ctypes.c_char_p(registration_datetime.encode('ascii'))
        p_patient_id = ctypes.c_char_p(patient_id.encode('ascii'))
        p_patient_birthday = ctypes.c_char_p(patient_birthday.encode('ascii'))
        p_data_write = ctypes.c_char_p(data_write.encode('ascii'))

        buffer_size = 40
        buffer = ctypes.create_string_buffer(buffer_size)  # c: char *
        buffer_len = ctypes.c_short(buffer_size)  # c: int *
        self._open_com()
        error_code = self.cshis.hisWritePrescriptionSign(
            p_registration_datetime,
            p_patient_id,
            p_patient_birthday,
            p_data_write,
            buffer,
            ctypes.byref(buffer_len)
        )
        self._close_com()

        out_queue.put((error_code, buffer))

    def write_prescript_sign(self, registration_datetime, patient_id, patient_birthday, data_write):
        title = '取得處置簽章'
        message = '<font size="4" color="red"><b>健保讀卡機取得處置簽章中, 請稍後...</b></font>'
        hint = '正在與與健保IDC資訊中心連線, 會花費一些時間.'
        msg_box = self._message_box(title, message, hint)
        msg_box.show()
        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()
        t = Thread(target=self.write_prescript_sign_thread,
                   args=(msg_queue, registration_datetime, patient_id, patient_birthday, data_write, ))
        t.start()
        (error_code, buffer) = msg_queue.get()
        msg_box.close()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡取得處置簽章')
            return None

        prescript_sign = buffer[:40].decode('ascii')

        return prescript_sign

    '''
    多筆處方箋寫入作業
    hisWriteMultiPrescriptSign(
        char * pDateTime            [in] 傳入之「就診日期時間」(HC健8-3)，長度14 bytes(含null char)
        char * pPatientID           [in] 傳入之民眾「身分證號」(HC基3)，長度11 bytes(含null char)
        char * pPatientBirthDate    [in] pPatientBirthDate: 傳入之民眾「出生日期」(HC基4)，長度8 bytes(含null char)
        char * pDataWrite           [in] pDataWrite: 傳入欲寫入之門診處方箋之資料（多組或一組），
                                         順序內容如下: 1組, 2組, 3組...
                                         門診處方箋第1組
                                         就診日期時間(1-13)
                                         醫令類別(14)
                                         診療項目代號(15-26)
                                         診療部位(27-32)
                                         用法(33-50)
                                         天數(51-52)
                                         總量(53-59)
                                         交付處方註記(60-61)
        int * iWriteCount           [in] 寫入處方資料組數
        char * pBuffer              [out] pBuffer: 為HIS準備之buffer，需可存入「pBuffer回傳內容」所稱之欄位值。
                                          欄位存入的順序，如「pBuffer回傳內容」所述
        int * iBufferLen)           [in/out] iBufferLen: HIS所準備buffer之長度，HIS呼叫此API時，傳入準備的buffer長度；
    '''
    def write_multi_prescript_sign_thread(
            self, out_queue, registration_datetime, patient_id, patient_birthday, data_write, write_count):
        p_registration_datetime = ctypes.c_char_p(registration_datetime.encode('ascii'))
        p_patient_id = ctypes.c_char_p(patient_id.encode('ascii'))
        p_patient_birthday = ctypes.c_char_p(patient_birthday.encode('ascii'))
        p_data_write = ctypes.c_char_p(data_write.encode('ascii'))

        p_write_count =  ctypes.c_int()
        p_write_count.value = write_count

        buff_size = write_count * 40
        buffer = ctypes.create_string_buffer(buff_size)  # c: char *
        buffer_len = ctypes.c_int(buff_size)  # c: int *
        self._open_com()
        error_code = self.cshis.hisWriteMultiPrescriptSign(
            p_registration_datetime,
            p_patient_id,
            p_patient_birthday,
            p_data_write,
            ctypes.byref(p_write_count),
            buffer,
            ctypes.byref(buffer_len)
        )
        self._close_com()

        out_queue.put((error_code, buffer))

    def write_multi_prescript_sign(self, registration_datetime, patient_id, patient_birthday,
                                   data_write, write_count):
        title = '取得處方簽章'
        message = '<font size="4" color="red"><b>健保讀卡機取得處方簽章中, 請稍後...</b></font>'
        hint = '正在與與健保IDC資訊中心連線, 會花費一些時間.'
        msg_box = self._message_box(title, message, hint)
        msg_box.show()
        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()
        t = Thread(target=self.write_multi_prescript_sign_thread,
                   args=(msg_queue, registration_datetime, patient_id, patient_birthday, data_write, write_count, ))
        t.start()
        (error_code, buffer) = msg_queue.get()
        msg_box.close()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡取得處方簽章')
            return None

        chunks, chunk_size = len(buffer), 40
        prescript_sign_list = [buffer[i:i+chunk_size].decode('ascii') for i in range(0, chunks, chunk_size)]

        return prescript_sign_list

    # 產生xml檔
    # treat_after_check: '1'-正常 '2'-補卡
    def treat_data_to_xml(self, treat_data=None):
        treat_data['upload_time'] = ''
        treat_data['upload_type'] = ''
        treat_data['treat_after_check'] = ''
        treat_data['prescript_sign_time'] = ''

        doc = case_utils.create_security_xml(treat_data)

        return doc

    def return_seq_number_thread(self, out_queue, treat_date):
        p_treat_date = ctypes.c_char_p(treat_date.encode('ascii'))
        self._open_com()
        error_code = self.cshis.csUnGetSeqNumber(p_treat_date)
        self._close_com()

        out_queue.put(error_code)

    # IC退掛
    def return_seq_number(self, treat_date):
        title = '健保IC卡退掛'
        message = '<font size="4" color="red"><b>健保IC卡退掛中, 請稍後...</b></font>'
        hint = '正在與與健保IDC資訊中心連線, 會花費一些時間.'
        msg_box = self._message_box(title, message, hint)
        msg_box.show()
        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()
        t = Thread(target=self.return_seq_number_thread, args=(msg_queue, treat_date))
        t.start()
        error_code = msg_queue.get()
        msg_box.close()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡退掛')
            return False
        else:
            return True

    '''
        IC卡資料上傳
        csUploadData(
            char * pUploadFileName          [in] 要上傳的檔案名稱，名稱內具備完整的路徑
            char * pFileSize                [in/out] 要上傳的檔案大小及DC回傳接收的檔案大小 (以Bytes為單位)
            char * pNumber                  [in/out] 要上傳檔案的筆數及DC回傳接收的檔案筆數
            char * pBuffer                  [out] 回傳內容及順序如下: 共50 Bytes
                                                  安全模組代碼(1-12)
                                                  醫事服務機構代碼(13-22)
                                                  上傳日期時間(23-36)
                                                  接收日期時間(37-50)
            int * iBufferLen                [in/out] iBufferLen，為HIS準備之buffer，HIS呼叫此API時，
                                                     傳入準備的buffer長度；CS亦利用此buffer傳出填入到
                                                     buffer中的資料長度(buffer的尾端不必補\0)
        );
    '''
    def upload_data_thread(self, out_queue, xml_file_name, file_size, record_count):
        p_upload_file_name = ctypes.c_char_p(xml_file_name.encode('ascii'))
        p_file_size = ctypes.c_char_p(file_size.encode('ascii'))
        p_number = ctypes.c_char_p(record_count.encode('ascii'))

        buffer_size = 50
        buffer = ctypes.create_string_buffer(buffer_size)  # c: char *
        buffer_len = ctypes.c_short(buffer_size)  # c: int *
        self._open_com()
        error_code = self.cshis.csUploadData(
            p_upload_file_name,
            p_file_size,
            p_number,
            buffer,
            ctypes.byref(buffer_len))
        self._close_com()

        out_queue.put((error_code, buffer))

    # IC卡資料上傳
    def upload_data(self, xml_file_name, record_count):
        title = '健保IC卡資料上傳'
        message = '<font size="4" color="red"><b>健保IC卡資料上傳中, 請稍後...</b></font>'
        hint = '正在與與健保IDC資訊中心連線, 會花費一些時間.'
        msg_box = self._message_box(title, message, hint)
        msg_box.show()
        msg_queue = Queue()

        file_size = os.path.getsize(xml_file_name)
        QtCore.QCoreApplication.processEvents()
        t = Thread(target=self.upload_data_thread, args=(
            msg_queue, xml_file_name, str(file_size), str(record_count)))
        t.start()
        (error_code, buffer) = msg_queue.get()
        msg_box.close()

        self.xml_feedback_data = None
        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡資料上傳')
            return False

        self.xml_feedback_data = cshis_utils.decode_xml_data(buffer)

        return True

    # ic卡寫卡
    def write_ic_card(self, write_type, patient_key, course, treat_after_check=None):
        treat_item = cshis_utils.get_treat_item(course)
        if not self.insert_correct_ic_card(patient_key):
            return False

        available_date, available_count = self.get_card_status()
        if available_count is None:
            return False

        if available_count <= 0:
            self.update_hc(False)

        if write_type in ['全部', '掛號寫卡']:
            if not self.get_seq_number_256(treat_item, ' ', treat_after_check):
                return False

        return self

    def insert_correct_ic_card(self, patient_key):
        try:
            if not self.read_basic_data():
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
        row = self.database.select_record(sql)[0]
        if self.basic_data['patient_id'] != string_utils.xstr(row['ID']):
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
                '''.format(self.basic_data['name'],
                           self.basic_data['patient_id'],
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
            '''.format(self.basic_data['card_no'],
                       patient_key)
            self.database.exec_sql(sql)

        return True

    # ic 醫令寫卡
    def write_ic_medical_record(self, case_key, treat_after_check):
        self.write_ic_treatment(case_key, treat_after_check)  # 寫入病名, 費用
        self.write_prescript_signature(case_key)  # 寫入醫令簽章
        case_utils.update_xml(
            self.database, 'cases', 'Security', 'prescript_sign_time',
            date_utils.now_to_str(), 'CaseKey', case_key
        )  # 更新健保寫卡資料

    # 寫入藥品處方簽章
    def write_medicine_signature(self, case_row, patient_row, prescript_rows, dosage_row):
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

        prescript_sign_list = self.write_multi_prescript_sign(
            registration_nhi_datetime, patient_id, birthday_nhi_datetime, data_write, len(prescript_rows)
        )

        if prescript_sign_list is None:
            return

        for row, prescript_sign in zip(prescript_rows, prescript_sign_list):
            self.database.exec_sql(
                'DELETE FROM presextend WHERE PrescriptKey = {0} AND ExtendType = "處方簽章"'.format(row['PrescriptKey'])
            )
            fields = [
                'PrescriptKey', 'ExtendType', 'Content',
            ]
            data = [
                row['PrescriptKey'], '處方簽章', prescript_sign,
            ]
            self.database.insert_record('presextend', fields, data)

    # 寫入處置處方簽章
    def write_treat_signature(self, case_row, dosage_row, patient_row):
        registration_datetime = case_utils.extract_security_xml(case_row['Security'], '寫卡時間')
        registration_nhi_datetime = date_utils.west_datetime_to_nhi_datetime(registration_datetime)
        patient_id = string_utils.xstr(patient_row['ID'])
        patient_birthday = string_utils.xstr(patient_row['Birthday'])
        birthday_nhi_datetime = date_utils.west_date_to_nhi_date(patient_birthday)

        treat_code = nhi_utils.get_treat_code(
            self.database, case_row['CaseKey']
        )
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

        treat_sign = self.write_prescript_sign(
            registration_nhi_datetime, patient_id, birthday_nhi_datetime, data_write,
        )

        if treat_sign is None:
            return

        self.database.exec_sql(
            'DELETE FROM presextend WHERE PrescriptKey = {0} AND ExtendType = "處置簽章"'.format(case_row['CaseKey'])
        )
        fields = [
            'PrescriptKey', 'ExtendType', 'Content',
        ]
        data = [
            case_row['CaseKey'], '處置簽章', treat_sign,
        ]
        self.database.insert_record('presextend', fields, data)

    # 寫入病名及費用
    def write_ic_treatment(self, case_key, treat_after_check):
        sql = '''
            SELECT PatientKey, DiseaseCode1, DiseaseCode2, DiseaseCode3, 
            DiagShareFee, DrugShareFee, InsTotalFee, Security FROM cases WHERE
            CaseKey = {0} 
        '''.format(case_key)
        case_row = self.database.select_record(sql)[0]

        sql = '''
            SELECT ID, Birthday FROM patient WHERE
            PatientKey = {0} 
        '''.format(case_row['PatientKey'])
        patient_row = self.database.select_record(sql)[0]

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
        doctor_id = self.write_treatment_code(
            registration_nhi_datetime, patient_id, birthday_nhi_datetime, data_write
        )

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
        self.write_treatment_fee(
            registration_nhi_datetime, patient_id, birthday_nhi_datetime, data_write
        )

        return doctor_id

    # 寫入處方簽章
    def write_prescript_signature(self, case_key):
        sql = '''
            SELECT CaseKey, PatientKey, Treatment, Security FROM cases WHERE
            CaseKey = {0} 
        '''.format(case_key)
        case_row = self.database.select_record(sql)[0]

        sql = '''
            SELECT * FROM dosage WHERE
            CaseKey = {0} AND MedicineSet = 1 
        '''.format(case_key)
        rows = self.database.select_record(sql)
        dosage_row = rows[0] if len(rows) > 0 else None

        sql = '''
            SELECT ID, Birthday FROM patient WHERE
            PatientKey = {0} 
        '''.format(case_row['PatientKey'])
        patient_row = self.database.select_record(sql)[0]

        sql = '''
            SELECT * FROM prescript WHERE
            CaseKey = {0} AND MedicineSet = 1 AND InsCode IS NOT NULL
        '''.format(case_key)
        prescript_rows = self.database.select_record(sql)

        if string_utils.xstr(case_row['Treatment']) in nhi_utils.INS_TREAT:
            self.write_treat_signature(case_row, dosage_row, patient_row)

        if len(prescript_rows) > 0:
            self.write_medicine_signature(case_row, patient_row, prescript_rows, dosage_row)


