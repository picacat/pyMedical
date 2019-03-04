#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import ui_utils
from libs import system_utils
import sys

if sys.platform == 'win32':
    from classes import cshis_win32 as cshis
else:
    from classes import cshis


# 主視窗
class DialogICCard(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogICCard, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        try:
            self.ic_card = cshis.CSHIS(self.database, self.system_settings)
        except NameError:
            self.ic_card = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_IC_CARD, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('關閉')

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.toolButton_verify_sam.clicked.connect(self.verify_sam)
        self.ui.toolButton_verify_hpc_pin.clicked.connect(self.verify_hpc_pin)
        self.ui.toolButton_set_hpc_pin.clicked.connect(self.set_hpc_pin)
        self.ui.toolButton_unlock_hpc_pin.clicked.connect(self.unlock_hpc_pin)
        self.ui.toolButton_update_ic_card.clicked.connect(self.update_ic_card)
        self.ui.toolButton_verify_ic_card_pin.clicked.connect(self.verify_ic_card_pin)
        self.ui.toolButton_set_ic_card_pin.clicked.connect(self.set_ic_card_pin)
        self.ui.toolButton_disable_ic_card_pin.clicked.connect(self.disable_ic_card_pin)
        self.ui.toolButton_ic_card_info.clicked.connect(self.ic_card_info)
        self.ui.toolButton_ic_card_record.clicked.connect(self.ic_card_record)
        self.ui.toolButton_reset_reader.clicked.connect(self.reset_reader)

    # 關閉
    def accepted_button_clicked(self):
        self.close()

    # 安全模組卡認證
    def verify_sam(self):
        self.ic_card.verify_sam()

    # 驗證醫事人員卡
    def verify_hpc_pin(self):
        self.ic_card.verify_hpc_pin()

    # 設定醫事人員卡密碼
    def set_hpc_pin(self):
        self.ic_card.input_hpc_pin()

    # 解鎖醫事人員卡密碼
    def unlock_hpc_pin(self):
        self.ic_card.unlock_hpc()

    # 更新病患健保卡內容
    def update_ic_card(self):
        self.ic_card.update_hc()

    # 驗證病患健保卡密碼
    def verify_ic_card_pin(self):
        self.ic_card.verify_hc_pin()

    # 設定病患健保卡密碼
    def set_ic_card_pin(self):
        self.ic_card.input_hc_pin()

    # 解除病患健保卡密碼
    def disable_ic_card_pin(self):
        self.ic_card.disable_hc_pin()

    # 讀取健保卡基本資料
    def ic_card_info(self):
        if not self.ic_card.read_register_basic_data():
            return

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle('健保卡基本資料')
        msg_box.setText(
            '''
            <font size="5" color="red">
              <b>健保IC卡卡片基本資料內容如下:</b><br><br>
            </font>
            <font size="4" color="black">
              <b>卡片號碼</b>: {0}<br>
              <b>病患姓名</b>: {1}<br>
              <b>身分證號</b>: {2}<br>
              <b>出生日期</b>: {3}<br>
              <b>病患性別</b>: {4}<br>
              <b>發卡日期</b>: {5}<br>
              <b>卡片註記</b>: {6}<br>
              <b>保險身分</b>: {7}<br>
              <b>卡片效期</b>: {8}<br>
              <b>可用次數</b>: {9}<br>
            </font> 
        '''.format(
                self.ic_card.basic_data['card_no'],
                self.ic_card.basic_data['name'],
                self.ic_card.basic_data['patient_id'],
                self.ic_card.basic_data['birthday'],
                self.ic_card.basic_data['gender'],
                self.ic_card.basic_data['card_date'],
                self.ic_card.basic_data['cancel_mark'],
                self.ic_card.basic_data['insured_mark'],
                self.ic_card.basic_data['card_valid_date'],
                self.ic_card.basic_data['card_available_count'],
            )
        )
        msg_box.setInformativeText('健保IC卡卡片內容讀取完成')
        msg_box.addButton(QPushButton("確定"), QMessageBox.AcceptRole)
        msg_box.exec_()

    # 讀取健保卡就醫資料
    def ic_card_record(self):
        print('讀取健保卡就醫資料')

    # 讀卡機裝置重新啟動
    def reset_reader(self):
        self.ic_card.reset_reader()
