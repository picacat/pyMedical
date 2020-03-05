#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from libs import system_utils
from libs import ui_utils
from libs import db_utils

import dict_drug
import dict_treat
import dict_compound
import dict_instruction


# 處方詞庫 2019.06.12
class DictMedicine(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictMedicine, self).__init__(parent)
        self.parent = parent
        self.args = args
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DICT_MEDICINE, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.ui.tabWidget_medicine.addTab(
            dict_drug.DictDrug(self, *self.args), '藥品資料')
        self.ui.tabWidget_medicine.addTab(
            dict_treat.DictTreat(self, *self.args), '處置資料')
        self.ui.tabWidget_medicine.addTab(
            dict_compound.DictCompound(self, *self.args), '成方資料')
        self.ui.tabWidget_medicine.addTab(
            dict_instruction.DictInstruction(self, *self.args), '指示及醫囑')

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_template)
        self.ui.action_export_dict_medicine_json.triggered.connect(self._export_dict_medicine_json)
        self.ui.action_export_dict_compound_json.triggered.connect(self._export_dict_compound_json)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_template(self):
        self.close_all()
        self.close_tab()

    def _export_dict_compound_json(self):
        options = QFileDialog.Options()
        json_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出成方JSON檔案", 'compound.json',
            "json檔案 (*.json)",
            options=options
        )
        if not json_file_name:
            return

        sql = '''
            SELECT * FROM refcompound
            ORDER BY CompoundKey
        '''
        rows = self.database.select_record(sql)

        json_data = db_utils.mysql_to_json(rows)
        text_file = open(json_file_name, "w", encoding='utf8')
        text_file.write(str(json_data))
        text_file.close()

        system_utils.show_message_box(
            QMessageBox.Information,
            'JSON資料匯出完成',
            '<h3>{0}匯出完成.</h3>'.format(json_file_name),
            'JSON 檔案格式.'
        )

    def _export_dict_medicine_json(self):
        options = QFileDialog.Options()
        json_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出處方JSON檔案", 'medicine.json',
            "json檔案 (*.json)",
            options=options
        )
        if not json_file_name:
            return

        sql = '''
            SELECT * FROM medicine
            ORDER BY MedicineKey
        '''
        rows = self.database.select_record(sql)

        json_data = db_utils.mysql_to_json(rows)
        text_file = open(json_file_name, "w", encoding='utf8')
        text_file.write(str(json_data))
        text_file.close()

        system_utils.show_message_box(
            QMessageBox.Information,
            'JSON資料匯出完成',
            '<h3>{0}匯出完成.</h3>'.format(json_file_name),
            'JSON 檔案格式.'
        )
