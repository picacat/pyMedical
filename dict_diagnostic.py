#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from lxml import etree as ET

from libs import ui_utils
from libs import string_utils
from libs import system_utils
from libs import xml_utils
from libs import db_utils
import dict_symptom
import dict_tongue
import dict_pulse
import dict_remark
import dict_disease
import dict_distinguish
import dict_cure


# 診察詞庫 2018.11.22
class DictDiagnostic(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictDiagnostic, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DICT_DIAGNOSTIC, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.ui.tabWidget_diagnostic.addTab(
            dict_symptom.DictSymptom(self, *self.args), '主訴資料')
        self.ui.tabWidget_diagnostic.addTab(
            dict_tongue.DictTongue(self, *self.args), '舌診資料')
        self.ui.tabWidget_diagnostic.addTab(
            dict_pulse.DictPulse(self, *self.args), '脈象資料')
        self.ui.tabWidget_diagnostic.addTab(
            dict_remark.DictRemark(self, *self.args), '備註資料')
        self.ui.tabWidget_diagnostic.addTab(
            dict_disease.DictDisease(self, *self.args), '病名資料')
        self.ui.tabWidget_diagnostic.addTab(
            dict_distinguish.DictDistinguish(self, *self.args), '辨證資料')
        self.ui.tabWidget_diagnostic.addTab(
            dict_cure.DictCure(self, *self.args), '治則資料')

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_template)
        self.ui.action_export_dict_diagnostic_groups_json.triggered.connect(
            self._export_dict_diagnostic_groups_json
        )
        self.ui.action_export_dict_diagnostic_json.triggered.connect(self._export_dict_diagnostic_json)
        self.ui.action_export_disease_groups.triggered.connect(self._export_disease_groups)
        self.ui.action_export_disease_groups.triggered.connect(self._export_disease_groups)
        self.ui.action_export_icd10_json.triggered.connect(self._export_icd10_json)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_template(self):
        self.close_all()
        self.close_tab()

    def _export_disease_groups(self):
        options = QFileDialog.Options()

        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self, "匯出病名類別詞庫",
            'disease_groups.xml',
            "所有檔案 (*);;xml檔 (*.xml)", options = options
        )
        if not file_name:
            return

        sql = '''
            SELECT ICDCode, Groups FROM icd10
            WHERE
                Groups IS NOT NULL AND LENGTH(Groups) > 0
            ORDER BY ICDCode
        '''
        rows = self.database.select_record(sql)

        root = ET.Element('groups')
        for row in rows:
            disease_groups = ET.SubElement(root, 'disease_groups')
            icd = ET.SubElement(disease_groups, 'icd')
            icd.text = string_utils.xstr(row['ICDCode'])
            groups = ET.SubElement(disease_groups, 'groups')
            groups.text = string_utils.xstr(row['Groups'])

        tree = ET.ElementTree(root)
        tree.write(file_name, pretty_print=True, xml_declaration=True, encoding="utf-8")

    def _import_disease_groups(self):
        options = QFileDialog.Options()

        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self, "匯入病名類別詞庫",
            'disease_groups.xml',
            "所有檔案 (*);;xml檔 (*.xml)", options = options
        )
        if not file_name:
            return

        tree = ET.parse(file_name)

        root = tree.getroot()
        groups = root.xpath('//groups/disease_groups')

        row_count = len(groups)
        progress_dialog = QtWidgets.QProgressDialog(
            '正在匯入病名類別中, 請稍後...', '取消', 0, row_count, self
        )

        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)
        for row_no, row in zip(range(row_count), groups):
            progress_dialog.setValue(row_no)
            data = xml_utils.convert_node_to_dict(row)
            sql = '''
                UPDATE icd10
                SET
                    Groups = "{0}"
                WHERE
                    ICDCode = "{1}"
            '''.format(
                data['groups'],
                data['icd'],
            )
            self.database.exec_sql(sql)

        progress_dialog.setValue(row_count)

    def _export_dict_diagnostic_groups_json(self):
        options = QFileDialog.Options()
        json_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出診察類別JSON檔案", 'diagnostic_groups.json',
            "json檔案 (*.json)",
            options=options
        )
        if not json_file_name:
            return

        sql = '''
            SELECT * FROM dict_groups
            WHERE
                DictGroupsType IN ("主訴", "舌診", "脈象", "辨證", "治則", "備註")
            ORDER BY DictGroupsKey
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

    def _export_dict_diagnostic_json(self):
        options = QFileDialog.Options()
        json_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出診察JSON檔案", 'diagnostic.json',
            "json檔案 (*.json)",
            options=options
        )
        if not json_file_name:
            return

        sql = '''
            SELECT * FROM clinic
            ORDER BY ClinicKey
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

    def _export_icd10_json(self):
        options = QFileDialog.Options()
        json_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出病名JSON檔案", 'icd10.json',
            "json檔案 (*.json)",
            options=options
        )
        if not json_file_name:
            return

        sql = '''
            SELECT * FROM icd10
            WHERE
                ICDCode IS NOT NULL AND LENGTH(ICDCode) > 0
            ORDER BY ICDCode
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
