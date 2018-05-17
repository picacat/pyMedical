
from PyQt5.QtWidgets import QMessageBox, QPushButton


# 友杏轉檔 2018.05.09
class CvtUtec():
    def __init__(self, parent, *args):
        self.parent = parent
        self.product_type = parent.ui.comboBox_utec_product.currentText()
        self.database = parent.database
        self.source_db = parent.source_db
        self.progress_bar = parent.ui.progressBar

    # 開始轉檔
    def convert(self):
        if self.parent.ui.label_connection_status.text() == '未連線':
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('尚未開啟連線')
            msg_box.setText("<font size='4' color='Red'><b>尚未執行連線測試, 請執行連線測試後再執行轉檔作業.</b></font>")
            msg_box.setInformativeText("連線尚未開啟, 無法執行轉檔作業.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return

        if self.parent.ui.checkBox_groups.isChecked():
            self.cvt_groups()

    # 類別詞庫轉檔
    def cvt_groups(self):
        if self.product_type == 'Med2000':
            sql = 'TRUNCATE dict_groups'
            self.source_db.exec_sql(sql)
            fields = [
                'DictGroupsType', 'DictGroupsTopLevel', 'DictGroupsName'
            ]

            data = ('主訴類別', None, '內科')
            self.database.insert_record('dict_groups', fields, data)
            data = ('主訴類別', None, '婦科')
            self.database.insert_record('dict_groups', fields, data)
            data = ('主訴類別', None, '兒科')
            self.database.insert_record('dict_groups', fields, data)
            data = ('主訴類別', None, '傷骨科')
            self.database.insert_record('dict_groups', fields, data)
            data = ('舌診類別', None, '舌質')
            self.database.insert_record('dict_groups', fields, data)
            data = ('舌診類別', None, '舌苔')
            self.database.insert_record('dict_groups', fields, data)
            data = ('舌診類別', None, '其他')
            self.database.insert_record('dict_groups', fields, data)
            data = ('辨證類別', None, '內科辨證')
            self.database.insert_record('dict_groups', fields, data)
            data = ('辨證類別', None, '傷骨科辨證')
            self.database.insert_record('dict_groups', fields, data)
            data = ('治則類別', None, '內科治則')
            self.database.insert_record('dict_groups', fields, data)
            data = ('治則類別', None, '傷骨科治則')
            self.database.insert_record('dict_groups', fields, data)

            sql = 'SELECT * FROM clinicgroups ORDER BY GroupsType, GroupsName'
            rows = self.source_db.select_record(sql)
            self.progress_bar.setMaximum(len(rows))
            for row in rows:
                self.progress_bar.setValue(self.progress_bar.value() + 1)

                if row['GroupsType'] in ['內科', '婦科', '傷科']:
                    dict_groups_type = '主訴'
                elif row['GroupsType'] in ['內辨', '傷辨']:
                    dict_groups_type = '辨證'
                elif row['GroupsType'] in ['內治', '傷治']:
                    dict_groups_type = '治則'
                else:
                    continue

                if dict_groups_type == '主訴':
                    dict_groups_top_level = row['GroupsType']
                    if dict_groups_top_level == '傷科':
                        dict_groups_top_level = '傷骨科'
                elif row['GroupsType'] in ['內辨', '內治']:
                    dict_groups_top_level = '內科'
                elif row['GroupsType'] in ['傷辨', '傷治']:
                    dict_groups_top_level = '傷骨科'
                else:
                    dict_groups_top_level = None

                dict_groups_name = row['GroupsName']

                data = (
                    dict_groups_type,
                    dict_groups_top_level,
                    dict_groups_name
                )
                self.database.insert_record('dict_groups', fields, data)

            sql = 'SELECT * FROM clinic WHERE ClinicType = "舌診" GROUP BY Groups ORDER BY Groups'
            rows = self.source_db.select_record(sql)
            self.progress_bar.setMaximum(len(rows))
            for row in rows:
                self.progress_bar.setValue(self.progress_bar.value() + 1)

                dict_groups_type = '舌診'
                dict_groups_name = str(row['Groups'])

                if dict_groups_name.find('舌') > 0:
                    dict_groups_top_level = '舌質'
                elif dict_groups_name.find('苔') > 0:
                    dict_groups_top_level = '舌苔'
                else:
                    dict_groups_top_level = '其他'

                data = (
                    dict_groups_type,
                    dict_groups_top_level,
                    dict_groups_name
                )
                self.database.insert_record('dict_groups', fields, data)
