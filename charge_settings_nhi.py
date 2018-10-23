#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from classes import table_widget
from dialog import dialog_input_nhi


# 收費設定 2018.04.14
class ChargeSettingsNHI(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ChargeSettingsNHI, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._set_instruction()
        self._read_charge()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHARGE_SETTINGS_NHI, self)
        self.table_widget_nhi = table_widget.TableWidget(self.ui.tableWidget_nhi, self.database)
        self.table_widget_nhi.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_nhi_add.clicked.connect(self._nhi_add)
        self.ui.toolButton_nhi_delete.clicked.connect(self._nhi_delete)
        self.ui.toolButton_nhi_edit.clicked.connect(self._nhi_edit)
        self.ui.tableWidget_nhi.doubleClicked.connect(self._nhi_edit)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [60, 120, 600, 150, 100, 650]
        self.table_widget_nhi.set_table_heading_width(width)

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()

    def _read_charge(self):
        self._read_nhi()

    # 健保支付標準 *******************************************************************************************************
    def _set_instruction(self):
        self.textEdit_remark.setHtml(
            '<b>診察費</b><br>' +
            '1. 每月看診日數計算方式: 每月實際看診日數<b><font color="red">超過26日者，以26日計</font></b>；' +
            '山地離島地區、花蓮縣及臺東縣之院所，每月以<b>實際看診日數</b>計.<br>' +
            '2. 專任醫師每月平均每日門診量＝【<b>當月中醫門診診察費總人次 / (當月專任中醫師數 * 每月看診日數)</b>】<br>' +
            '3. 看診時聘有護理人員: 指看診時須有護理人員在場服務。院所應於<b>費用年月次月二十日前，' +
            '至健保資訊網服務系統(VPN)填報『護理人員跟診時段』， <font color="red">未填報者，不予支付該類診察費</font></b>.<br>' +
            '4. 初診門診診察費加計: (1)設立健保特約院所<b>滿二年以上</b>（東區及山地離島地區以簽約<b>滿一年以上</b>）,' +
            '(2)患者需為<b>二年內(費用年月相減)未看診</b> (3)申報診察費之病人<b>ID歸戶人數之10%</b>為最高申請件數.<br>' +
            '5. <b>三歲(含)以下兒童</b>之門診診察費得依表定點數<b><font color="red">加計20%</font></b><br>' +
            '6. 支援中醫師看診人次計算: 依各段各專任中醫師每段看診<b><font color="red">合理量之餘額總數，依序補入支援中醫之看診人次</font></b>. ' +
            '若專任中醫師該月份均未看診(註1)，支援中醫師以看診合理量之最後一段支付點數申報.<br>' +
            '<font color="DarkGreen">' +
            '(註1) 專任醫師於產假期間全月未看診，支援醫師得以該全月未看診之專任醫師依合理量規定申報.<br>'
            '(註2) 支援醫師診察費一律按未聘有護理人員在場服務者之支付標準代碼計算<br>' +
            '</font>' +
            '<br>' +
            '<b>藥費</b><br>' +
            '1. 同一疾病或症狀之診治需連續門診者，<b>不得每次只給一日份用藥</b>，否則將累計其給藥日數，僅支付第一次就醫之診察費.<br>' +
            '2. 除指定之慢性病得最高給予三十日內之用藥量外，<b><font color="red">一般案件給藥天數不得超過七日</font></b>.<br>' +
            '<br>' +
            '<b>調劑費</b><br>' +
            '1. 未開藥者不得申報藥品調劑費<br>' +
            '2. 修習中藥課程達適當標準之藥師調劑者，須先報備，經證明核可後申報.<br>' +
            '<br>' +
            '<b>處置費</b><br>' +
            '1. 針灸、傷科、脫臼整復不得同時申報，且傷科及脫臼整復治療<b>限未設民俗調理之中醫診所申報</b>.<br>' +
            '2. 針灸、傷科及脫臼整復需連續治療者，<b>同一療程以6次為限，實施6次限申報一次診察費</b>，並應於病歷載明治療計畫.<br>' +
            '3. 專任醫師每月看診日平均針灸、傷科、脫臼整復合計<b>申報量限45人次以內. 申報量30人次以下，按表訂點數支付, ' +
            '申報量31-45人次, 按表訂點數90%支付, <font color="red">超過45人次支付點數以零計</font></b>.<br>' +
            '4. 專任醫師每月看診日平均針灸、傷科、脫臼整復治療合計申報量＝' +
            '<b>(當月針灸、傷科、脫臼整復治療處置總人次／當月專任中醫師總看診日數)</b><br>' +
            '5. 複雜性傷科處置每位專任醫師<b>每月上限為30人次</b>，超過30人次部分改以針傷治療合計量醫令計算.<br>' +
            '6. 中醫醫療院所平均每位專任醫師每月申報另開內服藥之針灸、傷科、脫臼整復處置費，' +
            '每位專任醫師<b>每月上限為120人次，<font color="red">超出120人次部分者50%支付</font></b>.<br>' +
            '<br>' +
            '<b>照護費</b><br>' +
            '1. 需接受中醫全聯會辦理之「小兒氣喘」、「小兒腦性麻痺」及「腦血管疾病、' +
            '顱腦損傷及脊髓損傷門診加強照護」課程各八小時，並由中醫全聯會於每季季底函送新增名單給保險人登錄備查.<br>' +
            '2. 小兒氣喘疾病門診加強照護：<b>年齡未滿十三歲</b>之氣喘疾病患者，並於病歷中檢附西醫診斷證明或肺功能檢查報告.<br>' +
            '3. 小兒腦性麻痺疾病門診加強照護：<b>年齡未滿十三歲</b>之腦性麻痺疾病患者.<br>' +
            '4. 腦血管疾病、顱腦損傷及脊髓損傷疾病門診加強照護：<b>自診斷日起二年內之患者.</b><br>'
            '5. 每位醫師每月各項疾病照護<b>申報上限為300人次(合計上限為650人次)，<font color="red">超出上限者費用點數支付為零</font>.</b><br>' +
            '6. 小兒氣喘及小兒腦性麻痺疾病每位患者<b>每週限申報一次</b>、腦血管疾病、顱腦損傷及脊髓損傷門診加強照護每位患者<b>每月限申報一次</b>.<br>' +
            '<font color="DarkGreen">'
            '(註1) 特定疾病門診加強照護不列入診察費及處置費合理量計算.<br>' +
            '(註2) 為避免病患重複收案，醫事人員收治病人後應於保險人健保資訊網服務系統(VPN)登錄個案之基本資料，' +
            '已被其他院所收案照護、不符適應症或已達結案條件者，不得收案.<br>' +
            '(註3) 腦血管疾病、顱腦損傷及脊髓損傷每季至少需於VPN填報巴氏量表分數乙次.<br>' +
            '(註4) 病患經加強照護病程穩定後，應教育病患自我照護，改按一般服務提供醫療照護.<br>' +
            '(註5) 腦血管疾病、顱腦損傷及脊髓損傷門診以巴氏量表測量連續二季未改善之患者應改按一般服務提供服務.' +
            '</font>' +
            '<br>' +
            ''
        )

    def _read_nhi(self):
        sql = 'SELECT * FROM charge_settings WHERE ChargeType in {0} ORDER BY FIELD(ChargeType, {1}), InsCode'.\
            format(tuple(nhi_utils.CHARGE_TYPE), str(nhi_utils.CHARGE_TYPE)[1:-1])
        self.table_widget_nhi.set_db_data(sql, self._set_nhi_data)
        row_count = self.table_widget_nhi.row_count()
        if row_count <= 0:
            self._set_nhi_basic_data()

    def _set_nhi_basic_data(self):
        fields = ['ChargeType', 'ItemName', 'InsCode', 'Amount', 'Remark']
        data = [
            ('診察費', '<=30人次門診診察費(有護理人員)', 'A01', 335, '支援醫師不適用'),
            ('診察費', '<=30人次門診診察費', 'A02', 325, None),
            ('診察費', '31-50人次門診診察費(有護理人員)', 'A03', 230, '支援醫師不適用'),
            ('診察費', '31-50人次門診診察費', 'A04', 220, None),
            ('診察費', '51-70人次門診診察費(有護理人員)', 'A05', 160, '支援醫師不適用'),
            ('診察費', '51-70人次門診診察費', 'A06', 150, None),
            ('診察費', '71-150人次門診診察費', 'A07', 90, None),
            ('診察費', '>150人次門診診察費', 'A08', 50, None),
            ('診察費', '山地離島門診診察費(有護理人員)', 'A09', 335, None),
            ('診察費', '山地離島門診診察費', 'A10', 325, None),
            ('診察費', '初診門診診察費加計', 'A90', 50, '2年以上新特約診所: 初診病患或2年內未就診病患'),
            ('藥費', '每日藥費', 'A21', 33, '一般案件給藥天數不得超過七日'),
            ('調劑費', '藥師調劑', 'A31', 23, '須先報備，經證明核可後申報'),
            ('調劑費', '醫師調劑', 'A32', 13, None),
            ('處置費', '針灸治療處置費-另開內服藥', 'B41', 215, None),
            ('處置費', '針灸治療處置費', 'B42', 215, None),
            ('處置費', '電針治療處置費-另開內服藥', 'B43', 215, None),
            ('處置費', '電針治療處置費', 'B44', 215, None),
            ('處置費', '複雜性針灸治療處置費-另開內服藥', 'B45', 295, None),
            ('處置費', '複雜性針灸治療處置費', 'B46', 295, None),
            ('處置費', '傷科治療處置費-另開內服藥', 'B53', 215, None),
            ('處置費', '傷科治療處置費', 'B54', 215, '標準作業程序: (1)四診八綱辨證(2)診斷(3)理筋手法'),
            ('處置費', '複雜性傷科治療處置費-另開內服藥', 'B55', 295, None),
            ('處置費', '複雜性傷科治療處置費', 'B56', 295, None),
            ('處置費', '骨折、脫臼整復第一線復位處置治療費', 'B57', 465,
             'B57「骨折、脫臼整復第一線復位處置治療」係指該患者受傷部位初次到醫療院所做接骨、復位之處理治療，且不得與B61併同申報'),
            ('處置費', '脫臼整復費-同療程第一次就醫', 'B61', 315, None),
            ('處置費', '脫臼整復費-同療程複診-另開內服藥', 'B62', 215, None),
            ('處置費', '脫臼整復費-同療程複診', 'B63', 215, None),
            ('照護費', '小兒氣喘照護處置費(含氣霧吸入處置費)', 'C01', 1500,
             '照護處置費包括中醫四診診察費、口服藥(不得少於五天)、針灸治療處置費、穴位推拿按摩、穴位敷貼處置費、氣霧吸入處置費'),
            ('照護費', '小兒氣喘照護處置費', 'C02', 1400,
             '照護處置費包括中醫四診診察費、口服藥(不得少於五天)、針灸治療處置費、穴位推拿按摩、穴位敷貼處置費'),
            ('照護費', '小兒腦性麻痺照護處置費(含藥浴處置費)', 'C03', 1500,
             '照護處置費包括中醫四診診察費、口服藥(不得少於五天)、頭皮針及體針半刺治療處置費、穴位推拿按摩、督脈及神闕藥灸、藥浴處置費'),
            ('照護費', '小兒腦性麻痺照護處置費', 'C04', 1400,
             '照護處置費包括中醫四診診察費、口服藥(不得少於五天)、頭皮針及體針半刺治療處置費、穴位推拿按摩、督脈及神闕藥灸'),
            ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置1-3次)', 'C05', 2000,
             '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
            ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置4-6次)', 'C06', 3500,
             '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
            ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置7-9次)', 'C07', 5500,
             '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
            ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置10-12次)', 'C08', 7500,
             '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
            ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置>=13次)', 'C09', 9500,
             '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
            ('照護費', '中醫助孕照護處置費(含針灸處置)', 'P39001', 1200,
             '包括中醫四診診察費，估排卵期評估，女性須含基礎體溫(BBT)、體質證型、濾泡期、排卵期、黃體期之月經週期療法之診療、口服藥(至少七天)、針灸治療處置費、衛教、營養飲食指導，單次門診須全部執行方能申請本項點數。'),
            ('照護費', '中醫助孕照護處置費(不含針灸處置)', 'P39002', 900,
             '包括中醫四診診察費，估排卵期評估，女性須含基礎體溫(BBT)、體質證型、濾泡期、排卵期、黃體期之月經週期療法之診療、口服藥(至少七天)、衛教、營養飲食指導，單次門診須全部執行方能申請本項點數。'),
            ('照護費', '中醫保胎照護處置費(含針灸處置)', 'P39003', 1200,
             '中醫四診診察費口服藥(至少七天)、針灸治療處置費、衛教、營養飲食指導，單次門診須全部執行方能申請本項點數。'),
            ('照護費', '中醫保胎照護處置費(不含針灸處置)', 'P39004', 900,
             '中醫四診診察費口服藥(至少七天)、衛教、營養飲食指導，單次門診須全部執行方能申請本項點數。'),
        ]
        for rec in data:
            self.database.insert_record('charge_settings', fields, rec)

        self._read_nhi()

    def _set_nhi_data(self, rec_no, rec):
        nhi_rec = [
            str(rec['ChargeSettingsKey']),
            string_utils.xstr(rec['ChargeType']),
            string_utils.xstr(rec['ItemName']),
            string_utils.xstr(rec['InsCode']),
            string_utils.xstr(rec['Amount']),
            string_utils.xstr(rec['Remark']),
        ]

        for column in range(len(nhi_rec)):
            self.ui.tableWidget_nhi.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(nhi_rec[column])
            )
            if column in [4]:
                self.ui.tableWidget_nhi.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _nhi_add(self):
        dialog = dialog_input_nhi.DialogInputNHI(self, self.database, self.system_settings, None)
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_nhi.rowCount()
            self.ui.tableWidget_nhi.insertRow(current_row)
            fields = ['ChargeType', 'ItemName', 'InsCode', 'Amount', 'Remark']
            data = [
                dialog.ui.comboBox_charge_type.currentText(),
                dialog.ui.lineEdit_item_name.text(),
                dialog.ui.lineEdit_ins_code.text(),
                dialog.ui.spinBox_amount.value(),
                dialog.ui.lineEdit_remark.text()
            ]
            self.database.insert_record('charge_settings', fields, data)
            sql = 'SELECT * FROM charge_settings WHERE ChargeType in {0} ORDER BY ChargeSettingsKey desc limit 1'.\
                format(tuple(nhi_utils.CHARGE_TYPE))
            row_data = self.database.select_record(sql)[0]
            self._set_nhi_data(current_row, row_data)
            self.ui.tableWidget_nhi.setCurrentCell(current_row, 3)

        dialog.close_all()
        dialog.deleteLater()

    def _nhi_edit(self):
        key = self.table_widget_nhi.field_value(0)
        dialog = dialog_input_nhi.DialogInputNHI(self, self.database, self.system_settings, key)
        dialog.exec_()
        dialog.close_all()
        sql = 'SELECT * FROM charge_settings WHERE ChargeSettingsKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_nhi_data(self.ui.tableWidget_nhi.currentRow(), row_data)

    def _nhi_delete(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除健保支付標準')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此筆健保支付標準資料?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        key = self.table_widget_nhi.field_value(0)
        self.database.delete_record('charge_settings', 'ChargeSettingsKey', key)
        self.ui.tableWidget_nhi.removeRow(self.ui.tableWidget_nhi.currentRow())


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = ChargeSettingsNHI()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
