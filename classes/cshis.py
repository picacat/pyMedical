# 讀卡機作業 2018.05.03

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox

import ctypes
from threading import Thread
from queue import Queue

from libs import number
from libs import date_utils
from libs import cshis_utils


# 健保ICD卡 2018.03.31
class CSHIS:
    def __init__(self, system_settings):
        self.com_port = number.get_integer(system_settings.field('讀卡機連接埠')) - 1  # com1=0, com2=1, com3=2,...
        self.cshis = cshis_utils.get_cshis()
        self.basic_data = cshis_utils.BASIC_DATA
        self.treat_data = cshis_utils.TREAT_DATA

    def __del__(self):
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
        available_count = number.get_integer(buffer[7:9].decode('ascii').strip())

        return available_date, available_count

    '''
    取得健保卡就醫序號
    hisGetSeqNumber256(
        char *cTreatItem 3 bytes 含null字元
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
        char *cBabyTreat 2 bytes 含null字元
        char *cTreatAfterCheck 1 byte, 1=正常 2=補卡
        char *pBuffer 296 bytes, 
                1-13    就診日期時間  13 bytes EEEMMDDHHNNSS  EEE=民國年
                14-17   就醫序號      4 bytes
                18-27   院所代號     10 bytes
                28-283  安全簽章    256 bytes
                284-295 SAM ID      10 bytes
                296     是否同日就診   1 bytes  Y=是 N=否
           int * iBufferLen);
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
