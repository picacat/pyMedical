#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from classes import db
from classes import table_widget

from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import case_utils


# 主視窗
class DialogMedicalRecordCollection(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogMedicalRecordCollection, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]

        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_collection()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_MEDICAL_RECORD_COLLECTION, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('匯入病歷')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_collection_type1 = table_widget.TableWidget(
            self.ui.tableWidget_collection_type1, self.database
        )
        self.table_widget_collection_type2 = table_widget.TableWidget(
            self.ui.tableWidget_collection_type2, self.database
        )
        self.table_widget_collection_name = table_widget.TableWidget(
            self.ui.tableWidget_collection_name, self.database
        )

    # 設定欄位寬度
    def _set_table_width(self):
        pass

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.tableWidget_collection_type1.itemSelectionChanged.connect(self._collection_type1_changed)
        self.ui.tableWidget_collection_type2.itemSelectionChanged.connect(self._collection_type2_changed)
        self.ui.tableWidget_collection_name.itemSelectionChanged.connect(self._collection_name_changed)

    def accepted_button_clicked(self):
        case_utils.copy_collection(
            self.database, self.parent, self.row,
            self.ui.checkBox_diagnostic.isChecked(),
            self.ui.checkBox_disease.isChecked(),
            self.ui.checkBox_prescript.isChecked(),
        )

    def _read_collection(self):
        sql = '''
            SELECT CollectionType1 FROM collection
            WHERE
                CollectionType1 IS NOT NULL
            GROUP BY CollectionType1
            ORDER BY CollectionType1
        '''
        try:
            self.table_widget_collection_type1.set_db_data_without_heading(sql, 'CollectionType1')
        except:
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def _collection_type1_changed(self):
        if not self.ui.tableWidget_collection_type1.selectedItems():
            return

        collection_type1 = self.ui.tableWidget_collection_type1.selectedItems()[0].text()
        sql = '''
            SELECT CollectionType2 FROM collection
            WHERE
                CollectionType1 = "{collection_type1}" AND
                CollectionType2 IS NOT NULL
            GROUP BY CollectionType2
            ORDER BY CollectionType2
        '''.format(
            collection_type1=collection_type1,
        )
        self.table_widget_collection_type2.set_db_data_without_heading(sql, 'CollectionType2')

    def _collection_type2_changed(self):
        if not self.ui.tableWidget_collection_type2.selectedItems():
            return

        collection_type1 = self.ui.tableWidget_collection_type1.selectedItems()[0].text()
        collection_type2 = self.ui.tableWidget_collection_type2.selectedItems()[0].text()
        sql = '''
            SELECT CollectionName FROM collection
            WHERE
                CollectionType1 = "{collection_type1}" AND
                CollectionType2 = "{collection_type2}" AND
                CollectionName IS NOT NULL
            ORDER BY CollectionName
        '''.format(
            collection_type1=collection_type1,
            collection_type2=collection_type2,
        )
        self.table_widget_collection_name.set_db_data_without_heading(sql, 'CollectionName')

    def _collection_name_changed(self):
        if not self.ui.tableWidget_collection_name.selectedItems():
            return

        collection_name = self.ui.tableWidget_collection_name.selectedItems()[0].text()
        self._show_collection_content(collection_name)

    def _show_collection_content(self, collection_name):
        self.ui.textEdit_collection.clear()

        sql = '''
            SELECT * FROM collection
            WHERE
                CollectionName = "{collection_name}"
        '''.format(
            collection_name=collection_name,
        )

        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return

        self.row = rows[0]
        self._set_collection_html(self.row)

    def _set_collection_html(self, row):
        medical_record = ''
        if row['Symptom'] is not None and string_utils.xstr(row['Symptom']) != '':
            medical_record += '<b>主訴</b>: {0}<hr>'.format(string_utils.get_str(row['Symptom'], 'utf8'))
        if row['Tongue'] is not None and string_utils.xstr(row['Tongue']) != '':
            medical_record += '<b>舌診</b>: {0}<hr>'.format(string_utils.get_str(row['Tongue'], 'utf8'))
        if row['Pulse'] is not None and string_utils.xstr(row['Pulse']) != '':
            medical_record += '<b>脈象</b>: {0}<hr>'.format(string_utils.get_str(row['Pulse'], 'utf8'))
        if row['Distincts'] is not None and string_utils.xstr(row['Distincts']) != '':
            medical_record += '<b>辨證</b>: {0}<hr>'.format(string_utils.xstr(row['Distincts']))
        if row['Cure'] is not None and string_utils.xstr(row['Cure']) != '':
            medical_record += '<b>治則</b>: {0}<hr>'.format(string_utils.xstr(row['Cure']))

        disease_list = []
        for i in range(3):
            icd9_code = string_utils.xstr(row['ICDCode{0}'.format(i+1)])
            if icd9_code == '':
                continue

            icd10_code, icd10_name = case_utils.convert_icd9_to_icd10(self.database, icd9_code)
            if icd10_name is not None:
                disease_list.append([icd10_code, icd10_name])

        icd_label = ['主診斷', '次診斷1', '次診斷2']
        for item_no, item in zip(range(len(disease_list)), disease_list):
            medical_record += '<b>{icd_label}</b>: {icd_code} {icd_name}<br>'.format(
                icd_label=icd_label[item_no],
                icd_code=item[0],
                icd_name=item[1],
            )

        medical_record = '''
            <div style="width: 95%;">
                {0}
            </div>
        '''.format(medical_record)

        prescript_record = self._get_prescript_record(row['CollectionKey'])

        html = '''
            <html>
                <head>
                    <meta charset="UTF-8">
                </head>
                <body>
                    {medical_record}
                    {prescript_record}
                </body>
            </html>
        '''.format(
            medical_record=medical_record,
            prescript_record=prescript_record,
        )

        self.ui.textEdit_collection.setHtml(html)

    def _get_prescript_record(self, collection_key):
        sql = '''
            SELECT * FROM collitems
            WHERE
                CollectionKey = {collection_key}
            ORDER BY CollectionSetKey
        '''.format(
            collection_key=collection_key,
        )

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return ''

        prescript_data = ''
        sequence = 0
        for row in rows:
            if string_utils.xstr(row['MedicineName']) == '':
                continue

            sequence += 1
            prescript_data += '''
                <tr>
                    <td align="center" style="padding-right: 8px;">{sequence}</td>
                    <td style="padding-left: 8px">{medicine_name}</td>
                    <td align="right" style="padding-right: 8px"></td>
                    <td style="padding-left: 8px"></td>
                </tr>
            '''.format(
                sequence=string_utils.xstr(sequence),
                medicine_name=string_utils.xstr(row['MedicineName']),
            )

        prescript_html = '''
            <table align=center cellpadding="2" cellspacing="0" width="98%" style="border-width: 1px; border-style: solid;">
                <thead>
                    <tr bgcolor="LightGray">
                        <th style="text-align: center; padding-left: 8px" width="10%">序</th>
                        <th style="padding-left: 8px" width="50%" align="left">健保處置</th>
                        <th style="padding-right: 8px" align="right" width="15%">次數</th>
                        <th style="padding-left: 8px" align="left" width="25%">備註</th>
                    </tr>
                </thead>
                <tbody>
                    {prescript_data}
                </tbody>
            </table>
            <br>
        '''.format(
            prescript_data=prescript_data,
        )

        return prescript_html

