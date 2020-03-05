#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton, QInputDialog
import os.path
import webbrowser
import subprocess
import datetime

from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import system_utils
from libs import log_utils
from dialog import dialog_ins_apply

import ins_apply_generate_file
import ins_apply_calculated_data
import ins_apply_calculate
import ins_apply_adjust_fee
import ins_apply_total_fee
import ins_apply_schedule_table
import ins_check_apply_fee
import ins_apply_fee_performance
import ins_apply_xml
import ins_apply_tab
import ins_apply_tour


# 健保申報 2018.10.01
class InsApply(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsApply, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.clinic_id = None
        self.apply_year = None
        self.apply_month = None
        self.apply_date = None
        self.apply_type_code = None
        self.start_date = None
        self.end_date = None
        self.apply_type = None
        self.ins_generate_date = None
        self.period = '全月'
        self.ins_calculated_table = []
        self.lock_type = '申報上鎖'

        self._set_ui()
        self._set_signal()
        # database.read_wait()   # activate by pymedical.py->tab_changed

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_app(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_APPLY, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)

    # 設定信號
    def _set_signal(self):
        self.ui.action_reapply.triggered.connect(self.open_dialog)
        self.ui.action_open_nhi_vpn.triggered.connect(self._open_nhi_vpn)
        self.ui.action_upload.triggered.connect(self._upload_data)
        self.ui.action_close.triggered.connect(self.close_app)
        self.ui.action_ins_lock.triggered.connect(self._lock_ins_data)

    def open_medical_record(self, case_key):
        self.parent.open_medical_record(case_key, '健保申報')

    def open_dialog(self):
        xml_dir = self.system_settings.field('資料路徑')
        if xml_dir in ['', None] or not os.path.exists(xml_dir):
            system_utils.show_message_box(
                QMessageBox.Critical,
                '申報路徑有誤',
                '<font color="red"><h3>申報路徑設定有誤, 請檢視申報路徑是否空白或正確.</h3></font>',
                '請至系統設定->其他頁面檢視申報及備份路徑的設定值.'
            )
            return

        dialog = dialog_ins_apply.DialogInsApply(self.ui, self.database, self.system_settings)
        if self.apply_year is not None:
            dialog.ui.comboBox_year.setCurrentText(string_utils.xstr(self.apply_year))
            dialog.ui.comboBox_month.setCurrentText(string_utils.xstr(self.apply_month))
            dialog.ui.lineEdit_clinic_id.setText(self.clinic_id)
            dialog.ui.comboBox_period.setCurrentText(self.period)
            if self.apply_type == '申報':
                dialog.ui.radioButton_apply.setChecked(True)
            else:
                dialog.ui.radioButton_reapply.setChecked(True)

        if not dialog.exec_():
            return

        self.apply_year = number_utils.get_integer(dialog.ui.comboBox_year.currentText())
        self.apply_month = number_utils.get_integer(dialog.ui.comboBox_month.currentText())
        if dialog.ui.radioButton_apply.isChecked():
            self.apply_type = '申報'  # 申報
            self.apply_type_code = '1'
        else:
            self.apply_type = '補報'  # 補報
            self.apply_type_code = '2'

        self.start_date = dialog.ui.dateEdit_start.date()
        self.end_date = dialog.ui.dateEdit_end.date()
        self.clinic_id = dialog.ui.lineEdit_clinic_id.text()
        self.period = dialog.ui.comboBox_period.currentText()
        self.ins_generate_date = dialog.ui.dateEdit_ins_generate_date.date()
        self.apply_date = '{0:0>3}{1:0>2}'.format(self.apply_year-1911, self.apply_month)

        if dialog.ui.radioButton_ins_apply.isChecked():
            apply_option = '健保申報'
        else:
            apply_option = '申報查詢'

        if apply_option == '健保申報':
            if self._generate_ins_data():
                self._calculate_ins_data()
                self._adjust_ins_fee()
                self._add_ins_apply_tab()
                self._create_xml_file()
            else:
                return
        elif apply_option == '申報查詢':
            self._calculate_ins_data()
            self._add_ins_apply_tab()

            xml_file_name = nhi_utils.get_ins_xml_file_name(
                self.system_settings, self.apply_type_code, self.apply_date
            )
            if not os.path.isfile(xml_file_name):
                self._create_xml_file()
        else:
            pass

        self._check_ins_xml_file()
        self._check_tour()

        dialog.close_all()
        dialog.deleteLater()

    def _check_apply_data_exists(self):
        apply_data_exists = False
        sql = '''
            SELECT * FROM insapply
            WHERE
                ApplyDate = "{0}" AND
                ApplyType = "{1}" AND
                ApplyPeriod = "{2}" AND
                ClinicID = "{3}"
        '''.format(self.apply_date, self.apply_type_code, self.period, self.clinic_id)
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            apply_data_exists = True

        return apply_data_exists

    def _lock_ins_data(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('申報資料上鎖')
        msg_box.setText(
            '''
            <font size="4" color="red">
              <b>確定將{0}年{1}月份申報資料上鎖?</b>
            </font>
            '''.format(self.apply_year, self.apply_month)
        )
        msg_box.setInformativeText("資料上鎖後, 將無法再次執行健保申報作業!")
        msg_box.addButton(QPushButton("資料上鎖"), QMessageBox.YesRole)
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        cancel = msg_box.exec_()
        if cancel:
            return

        apply_date = '{year}-{month:0>2}'.format(
            year=self.apply_year,
            month=self.apply_month,
        )
        generate_date = self.ins_generate_date.toString('yyyy-MM-dd')

        self.database.exec_sql(
            'DELETE FROM system_log WHERE LogType = "{lock_type}" AND LogName = "{apply_date}"'.format(
                lock_type=self.lock_type,
                apply_date=apply_date,
            )
        )

        log_utils.write_system_log(self.database, self.lock_type, apply_date, generate_date)

        system_utils.show_message_box(
            QMessageBox.Information,
            '健保資料已上鎖',
            '<font size="4" color="red"><b>{apply_year}年{apply_month}月份申報資料已上鎖.</b></font>'.format(
                apply_year=self.apply_year,
                apply_month=self.apply_month,
            ),
            '資料上鎖後, 就無法再次執行該月份的健保申報作業.'
        )

    def _check_apply_data_lock(self):
        lock_data = False
        apply_date = '{year}-{month:0>2}'.format(
            year=self.apply_year,
            month=self.apply_month,
        )

        sql = '''
            SELECT * FROM system_log
            WHERE
                LogType = "{lock_type}" AND
                LogName = "{apply_date}"
        '''.format(
            lock_type=self.lock_type,
            apply_date=apply_date,
        )
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            lock_data = True

        return lock_data

    def _generate_ins_data(self):
        if self._check_apply_data_lock():
            system_utils.show_message_box(
                QMessageBox.Critical,
                '健保資料已上鎖',
                '<font size="4" color="red"><b>{apply_year}年{apply_month}月份申報資料已上鎖, 不可再次申報.</b></font>'.format(
                    apply_year=self.apply_year,
                    apply_month=self.apply_month,
                ),
                '請勿再次執行健保申報, 以免造成申報資料流水號與金額與上次申報資料產生差異.'
            )
            return

        if self._check_apply_data_exists():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('申報資料已存在')
            msg_box.setText(
                '''
                <font size="4" color="red">
                  <b>{0}年{1}月份申報資料已存在, 是否重新申報?<br>
                </font>
                '''.format(self.apply_year, self.apply_month)
            )
            msg_box.setInformativeText("若資料已申報上傳, 請勿重新申報, 以免抽審時與上傳資料不符!")
            msg_box.addButton(QPushButton("重新申報"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            cancel = msg_box.exec_()
            if cancel:
                return False

        self.ui.tabWidget_ins_data.clear()

        ins_generate = ins_apply_generate_file.InsApplyGenerateFile(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.start_date, self.end_date,
            self.period, self.apply_type, self.clinic_id
        )
        ins_generate.generate_ins_file()

        return True

    def _adjust_ins_fee(self):
        ins_adjust_fee = ins_apply_adjust_fee.InsApplyAdjustFee(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.start_date, self.end_date,
            self.period, self.apply_type, self.clinic_id,
            self.ins_calculated_table,
        )
        ins_adjust_fee.adjust_ins_fee()

    def _calculate_ins_data(self):
        ins_calculate = ins_apply_calculate.InsApplyCalculate(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.start_date, self.end_date,
            self.period, self.apply_type, self.clinic_id
        )
        ins_calculate.calculate_ins_data()
        self.ins_calculated_table = ins_calculate.ins_calculated_table

    def _add_ins_apply_tab(self):
        self.ui.tabWidget_ins_data.clear()

        self.tab_ins_apply_tab = ins_apply_tab.InsApplyTab(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.period, self.apply_type, self.clinic_id
        )
        self.tab_ins_apply_calculated_data = ins_apply_calculated_data.InsApplyCalculatedData(
            self, self.database, self.system_settings,
            self.ins_calculated_table,
        )
        self.tab_ins_apply_total_fee = ins_apply_total_fee.InsApplyTotalFee(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.start_date, self.end_date,
            self.period, self.apply_type, self.clinic_id,
            self.ins_generate_date,
            self.ins_calculated_table,
        )

        self.tab_ins_apply_schedule_table = ins_apply_schedule_table.InsApplyScheduleTable(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.start_date, self.end_date,
            self.period, self.apply_type, self.clinic_id,
            self.ins_generate_date,
            self.ins_calculated_table,
        )

        self.ui.tabWidget_ins_data.addTab(self.tab_ins_apply_calculated_data, '申報統計資料')
        self.ui.tabWidget_ins_data.addTab(self.tab_ins_apply_total_fee, '申報總表')
        self.ui.tabWidget_ins_data.addTab(self.tab_ins_apply_schedule_table, '醫護排班表')
        self.ui.tabWidget_ins_data.addTab(self.tab_ins_apply_tab, '申報資料')

    def _create_xml_file(self):
        ins_xml_file = ins_apply_xml.InsApplyXML(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.start_date, self.end_date,
            self.period, self.apply_type, self.clinic_id,
            self.tab_ins_apply_total_fee.ins_total_fee,
        )
        ins_xml_file.create_xml_file()

    def _check_ins_xml_file(self):
        self.tab_ins_check_apply_fee = ins_check_apply_fee.InsCheckApplyFee(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.start_date, self.end_date,
            self.period, self.apply_type, self.clinic_id,
            self.ins_generate_date,
            self.tab_ins_apply_total_fee.ins_total_fee,
        )
        self.ui.tabWidget_ins_data.addTab(self.tab_ins_check_apply_fee, '申報金額核對')

        self.tab_ins_apply_fee_performance = ins_apply_fee_performance.InsApplyFeePerformance(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.start_date, self.end_date,
            self.period, self.apply_type, self.clinic_id,
            self.ins_generate_date,
            self.tab_ins_apply_total_fee.ins_total_fee,
        )
        self.ui.tabWidget_ins_data.addTab(self.tab_ins_apply_fee_performance, '申報業績')

    def _check_tour(self):
        self.tab_tour = ins_apply_tour.InsApplyTour(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.start_date, self.end_date,
            self.period, self.apply_type, self.clinic_id,
        )
        if self.tab_tour.tour_apply_count > 0:
            self.ui.tabWidget_ins_data.addTab(self.tab_tour, '巡迴醫療')

    def _open_nhi_vpn(self):
        med_vpn_addr = 'https://medvpn.nhi.gov.tw/iwse0000/IWSE0020S02.aspx'
        webbrowser.open(med_vpn_addr, new=0)  # 0: open in existing tab, 2: new tab

    @staticmethod
    def _message_box(title, message, hint):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setInformativeText(hint)
        msg_box.setStandardButtons(QMessageBox.NoButton)

        return msg_box

    def _upload_data(self):
        xml_file = nhi_utils.get_ins_xml_file_name(
            self.system_settings, self.apply_type_code, self.apply_date
        )
        if not os.path.isfile(xml_file):
            system_utils.show_message_box(
                QMessageBox.Information,
                '無申報檔案',
                '<font size="4" color="red"><b>找不到申報檔案, 請確定是否已執行過健保申報作業.</b></font>',
                '請重新執行健保申報申報作業.'
            )
            return

        zip_file = '{clinic_id}14{apply_date}{apply_type}3B.zip'.format(
            clinic_id=self.system_settings.field('院所代號'),
            apply_date=self.apply_date,
            apply_type=self.apply_type_code,
        )

        xml_path = nhi_utils.get_dir(self.system_settings, '申報路徑')
        zip_file = os.path.join(xml_path, zip_file)

        cmd = ['7z', 'a', '-tzip', zip_file, xml_file, '-o{0}'.format(xml_file)]
        sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        sp.communicate()

        type_code = '03'  # 醫療費用申報
        nhi_utils.NHI_SendB(self.system_settings, type_code, zip_file)

        try:
            self._write_log()
        except:
            pass

    def _write_log(self):
        log_type = '申報日期'
        apply_date = '{year}-{month:0>2}'.format(
            year=self.apply_year,
            month=self.apply_month,
        )
        generate_date = self.ins_generate_date.toString('yyyy-MM-dd')

        self.database.exec_sql(
            'DELETE FROM system_log WHERE LogType = "{log_type}" AND LogName = "{apply_date}"'.format(
                log_type=log_type,
                apply_date=apply_date,
            )
        )

        log_utils.write_system_log(self.database, '申報日期', apply_date, generate_date)

