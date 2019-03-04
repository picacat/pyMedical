#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog

from libs import ui_utils
from libs import system_utils
from libs import number_utils
from libs import nhi_utils
from libs import printer_utils

from classes import system_settings


# 系統設定 2018.03.19
class DialogSettings(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogSettings, self).__init__(parent)
        self.database = args[0]
        self.system_settings = args[1]
        self.parent = parent
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_settings()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_SETTINGS, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.tabWidget_settings.setCurrentIndex(0)
        self._set_combo_box()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.button_accepted)
        self.ui.buttonBox.rejected.connect(self.button_rejected)
        self.ui.spinBox_station_no.valueChanged.connect(self.spin_button_value_changed)
        self.ui.toolButton_emr_path.clicked.connect(self._get_emr_path)

    def _set_combo_box(self):
        # if sys.platform == 'win32':
        #     ui_utils.set_combo_box(self.ui.comboBox_theme, ui_utils.WIN32_THEME)
        # else:
        #     ui_utils.set_combo_box(self.ui.comboBox_theme, ui_utils.THEME)
        ui_utils.set_combo_box(
            self.ui.comboBox_theme,
            QtWidgets.QStyleFactory.keys()
        )
        ui_utils.set_combo_box(self.ui.comboBox_division, nhi_utils.DIVISION)
        ui_utils.set_combo_box(self.ui.comboBox_instruction, ['飯前', '飯後', '飯後睡前'])
        ui_utils.set_combo_box(self.ui.comboBox_color, ['紅色','綠色', '藍色', '灰色'])
        self._set_combo_box_printer()

        ui_utils.set_combo_box_item_color(
            self.ui.comboBox_color, [
                QtGui.QBrush(QtCore.Qt.red),
                QtGui.QBrush(QtCore.Qt.darkGreen),
                QtGui.QBrush(QtCore.Qt.blue),
                QtGui.QBrush(QtCore.Qt.darkGray),
            ]
        )

    def _set_combo_box_printer(self):
        printer_list = printer_utils.get_printer_list()
        print_mode = printer_utils.PRINT_MODE

        ui_utils.set_combo_box(self.ui.comboBox_regist_printer, printer_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_reserve_printer, printer_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_ins_prescript_printer, printer_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_self_prescript_printer, printer_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_ins_receipt_printer, printer_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_self_receipt_printer, printer_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_bag_printer, printer_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_massage_printer, printer_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_report_printer, printer_list, None)

        ui_utils.set_combo_box(
            self.ui.comboBox_regist_form,
            list(printer_utils.PRINT_REGISTRATION_FORM.keys()), None
        )

        ui_utils.set_combo_box(
            self.ui.comboBox_ins_prescript_form,
            list(printer_utils.PRINT_PRESCRIPTION_INS_FORM.keys()), None
        )
        ui_utils.set_combo_box(
            self.ui.comboBox_self_prescript_form,
            list(printer_utils.PRINT_PRESCRIPTION_SELF_FORM.keys()), None
        )
        ui_utils.set_combo_box(
            self.ui.comboBox_ins_receipt_form,
            list(printer_utils.PRINT_RECEIPT_INS_FORM.keys()), None
        )
        ui_utils.set_combo_box(
            self.ui.comboBox_self_receipt_form,
            list(printer_utils.PRINT_RECEIPT_SELF_FORM.keys()), None
        )

        ui_utils.set_combo_box(self.ui.comboBox_regist_print_mode, print_mode, None)
        ui_utils.set_combo_box(self.ui.comboBox_reserve_print_mode, print_mode, None)
        ui_utils.set_combo_box(self.ui.comboBox_ins_prescript_print_mode, print_mode, None)
        ui_utils.set_combo_box(self.ui.comboBox_self_prescript_print_mode, print_mode, None)
        ui_utils.set_combo_box(self.ui.comboBox_ins_receipt_print_mode, print_mode, None)
        ui_utils.set_combo_box(self.ui.comboBox_self_receipt_print_mode, print_mode, None)
        ui_utils.set_combo_box(self.ui.comboBox_bag_print_mode, print_mode, None)
        ui_utils.set_combo_box(self.ui.comboBox_massage_print_mode, print_mode, None)

        ui_utils.set_combo_box(self.ui.comboBox_report_print_mode, print_mode, None)

    ####################################################################################################################
    # 讀取設定檔
    def _read_settings(self):
        self._read_clinic_settings()
        self._read_regist_no_settings()
        self._read_registration_settings()
        self._read_doctor_settings()
        self._read_printer_settings()
        self._read_reader_settings()
        self._read_misc()

    # 讀取院所設定
    def _read_clinic_settings(self):
        self.ui.lineEdit_clinic_name.setText(self.system_settings.field('院所名稱'))
        self.ui.lineEdit_clinic_id.setText(self.system_settings.field('院所代號'))
        self.ui.lineEdit_invoice_no.setText(self.system_settings.field('統一編號'))
        self.ui.lineEdit_owner.setText(self.system_settings.field('負責醫師'))
        self.ui.lineEdit_owner_cert.setText(self.system_settings.field('醫師證號'))
        self.ui.lineEdit_clinic_cert.setText(self.system_settings.field('開業證號'))
        self.ui.lineEdit_telephone.setText(self.system_settings.field('院所電話'))
        self.ui.lineEdit_address.setText(self.system_settings.field('院所地址'))
        self.ui.lineEdit_email.setText(self.system_settings.field('電子郵件'))
        self.ui.lineEdit_period1.setText(self.system_settings.field('早班時間'))
        self.ui.lineEdit_period2.setText(self.system_settings.field('午班時間'))
        self.ui.lineEdit_period3.setText(self.system_settings.field('晚班時間'))
        self.ui.spinBox_nurse.setValue(number_utils.get_integer(self.system_settings.field('護士人數')))
        self.ui.spinBox_pharmacist.setValue(number_utils.get_integer(self.system_settings.field('藥師人數')))
        self._set_check_box(self.ui.checkBox_pharmacy_fee, '申報藥事服務費')
        self._set_check_box(self.ui.checkBox_init_fee, '申報初診照護')
        self._set_check_box(self.ui.checkBox_acupuncture_cert, '針灸認證合格')
        self._set_date_edit(self.ui.dateEdit_acupuncture_date, '針灸認證合格日期')
        self.ui.comboBox_division.setCurrentText(self.system_settings.field('健保業務'))

    # 讀取診號設定
    def _read_regist_no_settings(self):
        self._set_check_box(self.ui.checkBox_period_reset, '分班')
        self._set_check_box(self.ui.checkBox_room_reset, '分診')
        self.ui.spinBox_start_no1.setValue(number_utils.get_integer(self.system_settings.field('早班起始號')))
        self.ui.spinBox_start_no2.setValue(number_utils.get_integer(self.system_settings.field('午班起始號')))
        self.ui.spinBox_start_no3.setValue(number_utils.get_integer(self.system_settings.field('晚班起始號')))
        self._set_radio_button([self.ui.radioButton_consecutive,
                                self.ui.radioButton_odd,
                                self.ui.radioButton_even,
                                self.ui.radioButton_reservation_table],
                               ['連續號', '單號', '雙號', '預約班表'],
                               '現場掛號給號模式')

    # 讀取掛號設定
    def _read_registration_settings(self):
        self._set_radio_button([self.ui.radioButton_ins,
                                self.ui.radioButton_self],
                               ['健保', '自費'],
                               '預設門診類別')
        self.ui.spinBox_diag_count.setValue(number_utils.get_integer(self.system_settings.field('首次警告次數')))
        self.ui.spinBox_treat_count.setValue(number_utils.get_integer(self.system_settings.field('針傷警告次數')))
        self._set_check_box(self.ui.checkBox_doctor_treat, '醫師親自處置')

    # 看診設定
    def _read_doctor_settings(self):
        self.ui.spinBox_room.setValue(number_utils.get_integer(self.system_settings.field('診療室')))
        self._set_check_box(self.ui.checkBox_copy_past, '自動顯示過去病歷')
        self.ui.spinBox_packages.setValue(number_utils.get_integer(self.system_settings.field('給藥包數')))
        self.ui.spinBox_days.setValue(number_utils.get_integer(self.system_settings.field('給藥天數')))
        self.ui.comboBox_instruction.setCurrentText(self.system_settings.field('用藥指示'))
        self._set_radio_button([self.ui.radioButton_dosage1,
                                self.ui.radioButton_dosage2,
                                self.ui.radioButton_dosage3],
                               ['日劑量', '次劑量', '總量'],
                               '劑量模式')
        self._set_radio_button([self.ui.radioButton_self_room,
                                self.ui.radioButton_all_room],
                               ['指定診別', '所有診別'],
                               '候診名單顯示診別')
        self._set_radio_button([self.ui.radioButton_order_no,
                                self.ui.radioButton_order_time],
                               ['診號排序', '時間排序'],
                               '看診排序')
        self._set_radio_button([self.ui.radioButton_order_medicine_key,
                                self.ui.radioButton_order_medicine_type],
                               ['開藥順序', '處方類別'],
                               '處方排序')
        self._set_radio_button([self.ui.radioButton_by_dict_name,
                                self.ui.radioButton_by_hit_rate],
                               ['詞庫名稱', '點擊率'],
                               '詞庫排序')

    def _read_printer_settings(self):
        self.ui.comboBox_regist_print_mode.setCurrentText(self.system_settings.field('列印門診掛號單'))
        self.ui.comboBox_reserve_print_mode.setCurrentText(self.system_settings.field('列印預約掛號單'))
        self.ui.comboBox_ins_prescript_print_mode.setCurrentText(self.system_settings.field('列印健保處方箋'))
        self.ui.comboBox_self_prescript_print_mode.setCurrentText(self.system_settings.field('列印自費處方箋'))
        self.ui.comboBox_ins_receipt_print_mode.setCurrentText(self.system_settings.field('列印健保醫療收據'))
        self.ui.comboBox_self_receipt_print_mode.setCurrentText(self.system_settings.field('列印自費醫療收據'))
        self.ui.comboBox_bag_print_mode.setCurrentText(self.system_settings.field('列印藥袋'))
        self.ui.comboBox_massage_print_mode.setCurrentText(self.system_settings.field('列印民俗調理單'))

        self.ui.comboBox_regist_form.setCurrentText(self.system_settings.field('門診掛號單格式'))
        self.ui.comboBox_reserve_form.setCurrentText(self.system_settings.field('預約掛號單格式'))
        self.ui.comboBox_ins_prescript_form.setCurrentText(self.system_settings.field('健保處方箋格式'))
        self.ui.comboBox_self_prescript_form.setCurrentText(self.system_settings.field('自費處方箋格式'))
        self.ui.comboBox_ins_receipt_form.setCurrentText(self.system_settings.field('健保醫療收據格式'))
        self.ui.comboBox_self_receipt_form.setCurrentText(self.system_settings.field('自費醫療收據格式'))
        self.ui.comboBox_bag_form.setCurrentText(self.system_settings.field('藥袋格式'))
        self.ui.comboBox_massage_form.setCurrentText(self.system_settings.field('民俗調理單格式'))

        self.ui.comboBox_regist_printer.setCurrentText(self.system_settings.field('門診掛號單印表機'))
        self.ui.comboBox_reserve_printer.setCurrentText(self.system_settings.field('預約掛號單印表機'))
        self.ui.comboBox_ins_prescript_printer.setCurrentText(self.system_settings.field('健保處方箋印表機'))
        self.ui.comboBox_self_prescript_printer.setCurrentText(self.system_settings.field('自費處方箋印表機'))
        self.ui.comboBox_ins_receipt_printer.setCurrentText(self.system_settings.field('健保醫療收據印表機'))
        self.ui.comboBox_self_receipt_printer.setCurrentText(self.system_settings.field('自費醫療收據印表機'))
        self.ui.comboBox_bag_printer.setCurrentText(self.system_settings.field('藥袋印表機'))
        self.ui.comboBox_massage_printer.setCurrentText(self.system_settings.field('民俗調理單印表機'))

        self.ui.comboBox_report_print_mode.setCurrentText(self.system_settings.field('列印報表'))
        self.ui.comboBox_report_printer.setCurrentText(self.system_settings.field('報表印表機'))

        self._set_check_box(self.ui.checkBox_print_total_dosage, '列印藥品總量')
        self._set_check_box(self.ui.checkBox_print_location, '列印藥品存放位置')
        self._set_check_box(self.ui.checkBox_print_remark, '列印病歷備註')
        self._set_check_box(self.ui.checkBox_print_alias, '列印處方別名')
        self._set_check_box(self.ui.checkBox_print_clinic_name, '列印院所名稱')
        self._set_check_box(self.ui.checkBox_print_massager, '列印推拿師父')

    def _read_reader_settings(self):
        self._set_check_box(self.ui.checkBox_use_reader, '使用讀卡機')
        self.ui.spinBox_ic_reader_port.setValue(
            number_utils.get_integer(self.system_settings.field('健保卡讀卡機連接埠'))
        )
        self.ui.spinBox_hpc_reader_port.setValue(
            number_utils.get_integer(self.system_settings.field('醫事卡讀卡機連接埠'))
        )
        self._set_radio_button([self.ui.radioButton_hc3000,
                                self.ui.radioButton_teco,
                                self.ui.radioButton_cr0310],
                               ['虹堡HC3000', '東元讀卡機', '瑛茂CR0310'],
                               '讀卡機型號')
        self._set_check_box(self.ui.checkBox_read_record, '讀取卡片就醫記錄')
        self._set_check_box(self.ui.checkBox_read_disease, '讀取卡片重大傷病')
        self._set_radio_button([self.ui.radioButton_regist_secure,
                                self.ui.radioButton_doctor_secure],
                               ['掛號', '診療'],
                               '產生安全簽章位置')
        self._set_radio_button([self.ui.radioButton_doctor_write,
                                self.ui.radioButton_regist_write,
                                self.ui.radioButton_charge_write],
                               ['診療', '掛號', '批價'],
                               '產生醫令簽章位置')

    def _read_misc(self):
        self.ui.spinBox_station_no.setValue(number_utils.get_integer(self.system_settings.field('工作站編號')))
        self.ui.lineEdit_position.setText(self.system_settings.field('工作站位置'))
        self.ui.comboBox_theme.setCurrentText(self.system_settings.field('外觀主題'))
        self.ui.comboBox_color.setCurrentText(self.system_settings.field('外觀顏色'))
        self.ui.lineEdit_emr_path.setText(self.system_settings.field('電子病歷交換檔輸出路徑'))
        self._set_check_box(self.ui.checkBox_side_bar, '顯示側邊欄')

    ####################################################################################################################
    # 設定檔存檔
    def _save_settings(self):
        self._save_clinic_settings()
        self._save_regist_no_settings()
        self._save_registration_settings()
        self._save_doctor_settings()
        self._save_printer_settings()
        self._save_reader_settings()
        self._save_misc()

    # 寫入院所設定
    def _save_clinic_settings(self):
        self.system_settings.post('院所名稱', self.ui.lineEdit_clinic_name.text())
        self.system_settings.post('院所代號', self.ui.lineEdit_clinic_id.text())
        self.system_settings.post('統一編號', self.ui.lineEdit_invoice_no.text())
        self.system_settings.post('負責醫師', self.ui.lineEdit_owner.text())
        self.system_settings.post('醫師證號', self.ui.lineEdit_owner_cert.text())
        self.system_settings.post('開業證號', self.ui.lineEdit_clinic_cert.text())
        self.system_settings.post('院所電話', self.ui.lineEdit_telephone.text())
        self.system_settings.post('院所地址', self.ui.lineEdit_address.text())
        self.system_settings.post('電子郵件', self.ui.lineEdit_email.text())
        self.system_settings.post('早班時間', self.ui.lineEdit_period1.text())
        self.system_settings.post('午班時間', self.ui.lineEdit_period2.text())
        self.system_settings.post('晚班時間', self.ui.lineEdit_period3.text())
        self.system_settings.post('護士人數', self.ui.spinBox_nurse.value())
        self.system_settings.post('藥師人數', self.ui.spinBox_pharmacist.value())
        self._save_check_box(self.ui.checkBox_pharmacy_fee, '申報藥事服務費')
        self._save_check_box(self.ui.checkBox_init_fee, '申報初診照護')
        self._save_check_box(self.ui.checkBox_acupuncture_cert, '針灸認證合格')
        self._save_date_edit(self.ui.dateEdit_acupuncture_date, '針灸認證合格日期')
        self.system_settings.post('健保業務', self.ui.comboBox_division.currentText())

    # 寫入診號控制
    def _save_regist_no_settings(self):
        self._save_check_box(self.ui.checkBox_period_reset, '分班')
        self._save_check_box(self.ui.checkBox_room_reset, '分診')
        self.system_settings.post('早班起始號', self.ui.spinBox_start_no1.value())
        self.system_settings.post('午班起始號', self.ui.spinBox_start_no2.value())
        self.system_settings.post('晚班起始號', self.ui.spinBox_start_no3.value())
        self._save_radio_button([
            self.ui.radioButton_consecutive,
            self.ui.radioButton_odd,
            self.ui.radioButton_even,
            self.ui.radioButton_reservation_table],
            ['連續號', '單號', '雙號', '預約班表'],
            '現場掛號給號模式'
        )

    # 寫入掛號設定
    def _save_registration_settings(self):
        self._save_radio_button([self.ui.radioButton_ins,
                                 self.ui.radioButton_self],
                                ['健保', '自費'],
                                '預設門診類別')
        self.system_settings.post('首次警告次數', self.ui.spinBox_diag_count.value())
        self.system_settings.post('針傷警告次數', self.ui.spinBox_treat_count.value())

    def _save_doctor_settings(self):
        self.system_settings.post('診療室', self.ui.spinBox_room.value())
        self._save_check_box(self.ui.checkBox_copy_past, '自動顯示過去病歷')
        self.system_settings.post('給藥包數', self.ui.spinBox_packages.value())
        self.system_settings.post('給藥天數', self.ui.spinBox_days.value())
        self.system_settings.post('用藥指示', self.ui.comboBox_instruction.currentText())
        self._save_check_box(self.ui.checkBox_doctor_treat, '醫師親自處置')
        self._save_radio_button([self.ui.radioButton_dosage1,
                                 self.ui.radioButton_dosage2,
                                 self.ui.radioButton_dosage3],
                                ['日劑量', '次劑量', '總量'],
                                '劑量模式')
        self._save_radio_button([self.ui.radioButton_self_room,
                                 self.ui.radioButton_all_room],
                                ['指定診別', '所有診別'],
                                '候診名單顯示診別')
        self._save_radio_button([self.ui.radioButton_order_no,
                                 self.ui.radioButton_order_time],
                                ['診號排序', '時間排序'],
                                '看診排序')
        self._save_radio_button([self.ui.radioButton_order_medicine_key,
                                 self.ui.radioButton_order_medicine_type],
                                ['開藥順序', '處方類別'],
                                '處方排序')
        self._save_radio_button([self.ui.radioButton_by_dict_name,
                                 self.ui.radioButton_by_hit_rate],
                                ['詞庫名稱', '點擊率'],
                                '詞庫排序')

    def _save_printer_settings(self):
        self.system_settings.post('列印門診掛號單', self.ui.comboBox_regist_print_mode.currentText())
        self.system_settings.post('列印預約掛號單', self.ui.comboBox_reserve_print_mode.currentText())
        self.system_settings.post('列印健保處方箋', self.ui.comboBox_ins_prescript_print_mode.currentText())
        self.system_settings.post('列印自費處方箋', self.ui.comboBox_self_prescript_print_mode.currentText())
        self.system_settings.post('列印健保醫療收據', self.ui.comboBox_ins_receipt_print_mode.currentText())
        self.system_settings.post('列印自費醫療收據', self.ui.comboBox_self_receipt_print_mode.currentText())
        self.system_settings.post('列印藥袋', self.ui.comboBox_bag_print_mode.currentText())
        self.system_settings.post('列印民俗調理單', self.ui.comboBox_massage_print_mode.currentText())

        self.system_settings.post('門診掛號單格式', self.ui.comboBox_regist_form.currentText())
        self.system_settings.post('預約掛號單格式', self.ui.comboBox_reserve_form.currentText())
        self.system_settings.post('健保處方箋格式', self.ui.comboBox_ins_prescript_form.currentText())
        self.system_settings.post('自費處方箋格式', self.ui.comboBox_self_prescript_form.currentText())
        self.system_settings.post('健保醫療收據格式', self.ui.comboBox_ins_receipt_form.currentText())
        self.system_settings.post('自費醫療收據格式', self.ui.comboBox_self_receipt_form.currentText())
        self.system_settings.post('藥袋格式', self.ui.comboBox_bag_form.currentText())
        self.system_settings.post('民俗調理單格式', self.ui.comboBox_massage_form.currentText())

        self.system_settings.post('門診掛號單印表機', self.ui.comboBox_regist_printer.currentText())
        self.system_settings.post('預約掛號單印表機', self.ui.comboBox_reserve_printer.currentText())
        self.system_settings.post('健保處方箋印表機', self.ui.comboBox_ins_prescript_printer.currentText())
        self.system_settings.post('自費處方箋印表機', self.ui.comboBox_self_prescript_printer.currentText())
        self.system_settings.post('健保醫療收據印表機', self.ui.comboBox_ins_receipt_printer.currentText())
        self.system_settings.post('自費醫療收據印表機', self.ui.comboBox_self_receipt_printer.currentText())
        self.system_settings.post('藥袋印表機', self.ui.comboBox_bag_printer.currentText())
        self.system_settings.post('民俗調理單印表機', self.ui.comboBox_massage_printer.currentText())

        self.system_settings.post('列印報表', self.ui.comboBox_report_print_mode.currentText())
        self.system_settings.post('報表印表機', self.ui.comboBox_report_printer.currentText())

        self._save_check_box(self.ui.checkBox_print_total_dosage, '列印藥品總量')
        self._save_check_box(self.ui.checkBox_print_location, '列印藥品存放位置')
        self._save_check_box(self.ui.checkBox_print_remark, '列印病歷備註')
        self._save_check_box(self.ui.checkBox_print_alias, '列印處方別名')
        self._save_check_box(self.ui.checkBox_print_clinic_name, '列印院所名稱')
        self._save_check_box(self.ui.checkBox_print_massager, '列印推拿師父')

    def _save_reader_settings(self):
        self._save_check_box( self.ui.checkBox_use_reader, '使用讀卡機')
        self.system_settings.post('健保卡讀卡機連接埠', self.ui.spinBox_ic_reader_port.value())
        self.system_settings.post('醫事卡讀卡機連接埠', self.ui.spinBox_hpc_reader_port.value())
        self._save_radio_button([self.ui.radioButton_hc3000,
                                 self.ui.radioButton_teco,
                                 self.ui.radioButton_cr0310],
                                ['虹堡HC3000', '東元讀卡機', '瑛茂CR0310'],
                                '讀卡機型號')
        self._save_check_box( self.ui.checkBox_read_record, '讀取卡片就醫記錄')
        self._save_check_box( self.ui.checkBox_read_disease, '讀取卡片重大傷病')
        self._save_radio_button([self.ui.radioButton_regist_secure,
                                 self.ui.radioButton_doctor_secure],
                                ['掛號', '診療'],
                                '產生安全簽章位置')

        self._save_radio_button([self.ui.radioButton_doctor_write,
                                 self.ui.radioButton_regist_write,
                                 self.ui.radioButton_charge_write],
                                ['診療', '掛號', '批價'],
                                '產生醫令簽章位置')

    def _save_misc(self):
        self.system_settings.post('工作站編號', str(self.ui.spinBox_station_no.value()))
        self.system_settings.post('工作站位置', self.ui.lineEdit_position.text())
        self.system_settings.post('外觀主題', self.ui.comboBox_theme.currentText())
        self.system_settings.post('外觀顏色', self.ui.comboBox_color.currentText())
        self.system_settings.post('電子病歷交換檔輸出路徑', self.ui.lineEdit_emr_path.text())
        self._save_check_box(self.ui.checkBox_side_bar, '顯示側邊欄')

    # 取得電子病歷輸出路徑
    def _get_emr_path(self):
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(
            self, "QFileDialog.getExistingDirectory()",
            self.ui.lineEdit_emr_path.text(), options = options
        )
        if directory:
            self.ui.lineEdit_emr_path.setText(directory)

    ####################################################################################################################
    # 讀取 check_box 的資料
    def _set_check_box(self, check_box, field):
        if self.system_settings.field(field) == 'Y':
            check_box.setChecked(True)
        else:
            check_box.setChecked(False)

    # 讀取 check_box 的資料
    def _set_date_edit(self, date_edit, field):
        date = self.system_settings.field(field)
        if date is None:
            return

        year, month, day = date.split('-')
        date_edit.setDate(QtCore.QDate(int(year), int(month), int(day)))

    # 讀取 radio_button
    def _set_radio_button(self, radio_buttons, values, field):
        for radio_button, value in zip(radio_buttons, values):
            if self.system_settings.field(field) == value:
                radio_button.setChecked(True)
                break

    ####################################################################################################################
    # 寫入 check_box 的資料
    def _save_check_box(self, check_box, field):
        if check_box.isChecked():
            self.system_settings.post(field, 'Y')
        else:
            self.system_settings.post(field, 'N')

    # 寫入 date_edit 的資料
    def _save_date_edit(self, date_edit, field):
        date = date_edit.date().toString('yyyy-MM-dd')
        self.system_settings.post(field, date)

    # 寫入 radio_button
    def _save_radio_button(self, radio_buttons, values, field):
        select_value = None
        for radio_button, value in zip(radio_buttons, values):
            if radio_button.isChecked():
                select_value = value
                break

        self.system_settings.post(field, select_value)

    # OK
    def button_accepted(self):
        self._save_settings()
        del self.system_settings

    # Cancel
    def button_rejected(self):
        del self.system_settings

    # 更改工作站編號
    def spin_button_value_changed(self):
        self.system_settings = system_settings.SystemSettings(self.database, self.ui.spinBox_station_no.value())
        self._read_settings()

