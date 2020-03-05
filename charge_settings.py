#!/usr/bin/env python3
#coding: utf-8

import sys
import json

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import system_utils
from libs import ui_utils
from libs import dropbox_utils
from libs import number_utils
from libs import string_utils
import charge_settings_regist
import charge_settings_share
import charge_settings_nhi


# 收費設定 2018.04.14
class ChargeSettings(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ChargeSettings, self).__init__(parent)
        self.parent = parent
        self.args = args
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()

        self._read_charge_settings()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHARGE_SETTINGS, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_charge_settings)
        self.ui.action_update_nhi_payment.triggered.connect(self._update_nhi_payment)
        self.ui.action_update_nhi_payment_old.triggered.connect(self._update_nhi_payment_old)

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()

    def _read_charge_settings(self):
        self.ui.tabWidget_charge_settings.clear()

        self.ui.tabWidget_charge_settings.addTab(
            charge_settings_regist.ChargeSettingsRegist(self, *self.args), '掛號費')
        self.ui.tabWidget_charge_settings.addTab(
            charge_settings_share.ChargeSettingsShare(self, *self.args), '部份負擔')
        self.ui.tabWidget_charge_settings.addTab(
            charge_settings_nhi.ChargeSettingsNHI(self, *self.args), '健保支付標準')

    def _update_nhi_payment(self):
        json_file = 'nhi_payment.json'
        self._download_nhi_payment(
            json_file,
            'https://www.dropbox.com/s/h30h1m48ightk9o/nhi_payment.json?dl=1'
        )
        self._update_json_file(json_file)

    def _update_nhi_payment_old(self):
        json_file = 'nhi_payment_old.json'
        self._download_nhi_payment(
            json_file,
            'https://www.dropbox.com/s/586fv9kwix9jg11/nhi_payment_old.json?dl=1',
        )
        self._update_json_file(json_file)

    def _update_json_file(self, filename):
        update_list = []
        with open(filename, encoding='utf8') as json_file:
            rows = json.load(json_file)
            for row_no, row in zip(range(len(rows)), rows):
                new_ins_code = row['InsCode']
                new_amount = number_utils.get_integer(row['Amount'])
                sql = '''
                    SELECT * FROM charge_settings
                    WHERE
                        InsCode = "{ins_code}"
                '''.format(
                    ins_code=new_ins_code,
                )
                charge_row = self.database.select_record(sql)
                if len(charge_row) <= 0:
                    update_list.append(['無', row])
                elif number_utils.get_integer(charge_row[0]['Amount']) != new_amount:
                    update_list.append([charge_row[0]['Amount'], row])

        if len(update_list) <= 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('健保支付標準更新完成')
            msg_box.setText("<font size='4'><b>經過檢查, 發現健保支付標準已經是最新檔, 不需更新.</b></font>")
            msg_box.setInformativeText("請按確定鍵結束更新.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return

        self._ready_to_update(update_list)

    def _ready_to_update(self, update_list):
        html = self._get_update_html(update_list)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle('更新內容')
        msg_box.setText(
            '''
            <font size="4" color="red">
              <b>健保支付標準更新內容如下:</b>
            </font>
            {html}
        '''.format(
                html=html,
            )
        )
        msg_box.setInformativeText('請按「確定更新」按鈕執行更新作業, 或「取消」離開.')
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定更新"), QMessageBox.YesRole)
        apply_change = msg_box.exec_()
        if not apply_change:
            return

        for row in update_list:
            self._sync_database(row[1])

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('系統更新完成')
        msg_box.setText("<font size='4'><b>所有健保支付標準檔均已更新完成.</b></font>")
        msg_box.setInformativeText("恭喜您！ 所有更新均已完成.")
        msg_box.addButton(QPushButton("完成"), QMessageBox.YesRole)
        msg_box.exec_()

        self._read_charge_settings()

    def _sync_database(self, json_row):
        sql = '''
            SELECT * FROM charge_settings
            WHERE
                InsCode = "{ins_code}"
        '''.format(
            ins_code=json_row['InsCode']
        )
        rows = self.database.select_record(sql)

        if len(rows) > 0:
            self._update_record(json_row)
        else:
            self._insert_record(json_row)

    def _update_record(self, row):
        sql = '''
            UPDATE charge_settings
            SET
                Amount = {amount}
            WHERE
                InsCode = "{ins_code}"
        '''.format(
            amount=number_utils.get_integer(row['Amount']),
            ins_code=string_utils.xstr(row['InsCode'])
        )
        self.database.exec_sql(sql)

    def _insert_record(self, row):
        fields = [
            'ChargeType', 'ItemName', 'InsCode', 'Amount', 'Remark',
        ]

        data = [
            string_utils.xstr(row['ChargeType']),
            string_utils.xstr(row['ItemName']),
            string_utils.xstr(row['InsCode']),
            number_utils.get_integer(row['Amount']),
            string_utils.xstr(row['Remark']),

        ]

        self.database.insert_record('debt', fields, data)

    @staticmethod
    def _download_nhi_payment(file_name, url):
        title = '下載健保支付標準檔'
        message = '<font size="4" color="red"><b>正在下載健保支付標準檔, 請稍後...</b></font>'
        hint = '正在與更新檔資料庫連線, 會花費一些時間.'
        dropbox_utils.download_dropbox_file(file_name, url, title, message, hint)

    @staticmethod
    def _get_update_html(update_list):
        charge_list = ''
        for row_no, row in zip(range(len(update_list)), update_list):
            item_name = string_utils.xstr(row[1]['ItemName'])
            item_name = item_name.replace('>=', '')
            item_name = item_name.replace('<=', '')

            charge_list += '''
                <tr>
                    <td align=center>{sequence}</td>
                    <td>{item_name}</td>
                    <td align=center>{ins_code}</td>
                    <td align=right>{old_amount}</td>
                    <td align=right>{new_amount}</td>
                </tr>
            '''.format(
                sequence=row_no+1,
                item_name=item_name,
                ins_code=row[1]['InsCode'],
                old_amount=row[0],
                new_amount=row[1]['Amount'],
            )

        html = '''
            <table align=center cellpadding="2" cellspacing="0" width="100%" style="border-width: 1px; border-style: solid;">
                <thead>
                    <tr bgcolor="LightGray">
                        <th style="padding-left: 8px" width="10%">序</th>
                        <th style="padding-left: 8px" width="50%" align="left">診療項目</th>
                        <th style="padding-right: 8px" width="10%">醫令代碼</th>
                        <th style="padding-left: 8px" width="10%">原點數</th>
                        <th style="padding-left: 8px" width="10%">新點數</th>
                    </tr>
                </thead>
                    {charge_list}
                <tbody>
                </tbody>
            </table>
        '''.format(
            charge_list=charge_list,
        )

        return html

