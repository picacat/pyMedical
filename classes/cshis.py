# 讀卡機作業 2018.05.03

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox

import ctypes
from threading import Thread
from queue import Queue

from libs import number_utils
from libs import date_utils
from libs import cshis_utils
from libs import case_utils


# 健保ICD卡 2018.03.31
class CSHIS:
    def __init__(self, system_settings):
        self.com_port = number_utils.get_integer(system_settings.field('讀卡機連接埠')) - 1  # com1=0, com2=1, com3=2,...
        self.cshis = cshis_utils.get_cshis()
        self.basic_data = cshis_utils.BASIC_DATA
        self.treat_data = cshis_utils.TREAT_DATA

    def __del__(self):
        if self.cshis is not None:
            self._close_com()

    def _open_com(self):
        self.cshis.csOpenCom(self.com_port)

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
            '正在與與健保IDC資訊中心連線, 會花費一些時間.'
        )

    def update_hc(self,  show_message=True):
        self._open_com()
        error_code = self.cshis.csUpdateHCContents()
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
        buffer = ctypes.create_string_buffer(72)  # c: char *
        buffer_len = ctypes.c_int()  # c: int *
        buffer_len.value = len(buffer)
        self._open_com()
        error_code = self.cshis.hisGetBasicData(buffer, ctypes.byref(buffer_len))
        self._close_com()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡讀取')
            return False

        self.basic_data = cshis_utils.decode_basic_data(buffer)

        return True

    def read_register_basic_data(self):
        buffer = ctypes.create_string_buffer(78)  # c: char *
        buffer_len = ctypes.c_int()  # c: int *
        buffer_len.value = len(buffer)
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
        buffer = ctypes.create_string_buffer(9)  # c: char *
        buffer_len = ctypes.c_int()  # c: int *
        buffer_len.value = len(buffer)
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
        buffer = ctypes.create_string_buffer(296)  # c: char *
        buffer_len = ctypes.c_int()  # c: int *
        buffer_len.value = len(buffer)
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

        buffer = ctypes.create_string_buffer(40)  # c: char *
        buffer_len = ctypes.c_int()  # c: int *
        buffer_len.value = len(buffer)
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

        buffer = ctypes.create_string_buffer(write_count * 40)  # c: char *
        buffer_len = ctypes.c_int()  # c: int *
        buffer_len.value = len(buffer)
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

        return doc.toprettyxml(indent='\t')

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
    def upload_file_thread(self, out_queue, xml_file_name, file_size, record_count):
        p_upload_file_name = ctypes.c_char_p(xml_file_name.encode('ascii'))
        p_file_size = ctypes.c_char_p(file_size.encode('ascii'))
        p_number = ctypes.c_char_p(record_count.encode('ascii'))
        buffer = ctypes.create_string_buffer(50)  # c: char *
        buffer_len = ctypes.c_int()  # c: int *
        buffer_len.value = len(buffer)
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
    def upload_file(self, xml_file_name, file_size, record_count):
        title = '健保IC卡資料上傳'
        message = '<font size="4" color="red"><b>健保IC卡資料上傳中, 請稍後...</b></font>'
        hint = '正在與與健保IDC資訊中心連線, 會花費一些時間.'
        msg_box = self._message_box(title, message, hint)
        msg_box.show()
        msg_queue = Queue()

        QtCore.QCoreApplication.processEvents()
        t = Thread(target=self.upload_file_thread, args=(
            msg_queue, xml_file_name, str(file_size), str(record_count)))
        t.start()
        (error_code, buffer) = msg_queue.get()
        msg_box.close()

        if error_code != 0:
            cshis_utils.show_ic_card_message(error_code, '健保卡資料上傳')
            return False

        self.xml_feedback_data = cshis_utils.decode_xml_data(buffer)
        return True
