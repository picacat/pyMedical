# 掛號顯示過去病歷

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QSettings, QSize, QPoint
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import case_utils
from libs import cshis_utils
from classes import table_widget
from dialog import dialog_medical_record_past_history


# 掛號過去病歷視窗
class DialogPastHistory(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogPastHistory, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.patient = None
        self.medical_record = None

        self.settings = QSettings('__settings.ini', QSettings.IniFormat)

        self._set_ui()
        self._set_signal()

    # 解構 (pymedical 離開時)
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 關閉
    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.settings.setValue("dialog_history_size", self.size())
        self.settings.setValue("dialog_history_pos", self.pos())

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_PAST_HISTORY, self)
        self.ui.resize(self.settings.value("dialog_history_size", QSize(858, 769)))
        self.ui.move(self.settings.value("dialog_history_pos", QPoint(1054, 225)))

        self.table_widget_past_history = table_widget.TableWidget(self.ui.tableWidget_past_history, self.database)
        self.table_widget_past_history.set_column_hidden([0, 1])

        system_utils.set_css(self, self.system_settings)
        system_utils.set_theme(self.ui, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('關閉')

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.tableWidget_past_history.doubleClicked.connect(self._open_medical_record)

    def _open_medical_record(self):
        case_key = self.table_widget_past_history.field_value(0)
        patient_key = self.table_widget_past_history.field_value(1)
        if case_key is None:
            return

        dialog = dialog_medical_record_past_history.DialogMedicalRecordPastHistory(
            self, self.database, self.system_settings, case_key, patient_key, '病歷查詢'
        )

        dialog.exec_()
        dialog.deleteLater()

    def accepted_button_clicked(self):
        self.close()

    def show_past_history(self, patient_key, ic_card=None):
        self.read_data(patient_key)
        if len(self.medical_record) <= 0:
            return

        self.ui.groupBox_past_history.setTitle('{0}的過去病歷'.format(self.patient['Name']))
        self.ui.groupBox_ic_card.setVisible(False)
        self.show()

        if ic_card is not None:
            self._set_ic_card_treatment_data(ic_card)

    def read_data(self, patient_key):
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
        self.patient = self.database.select_record(sql)[0]
        sql = 'SELECT * FROM cases WHERE PatientKey = {0} ORDER BY CaseDate DESC'.format(patient_key)
        self.medical_record = self.database.select_record(sql)
        self.table_widget_past_history.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        pres_days = case_utils.get_pres_days(self.database, row['CaseKey'])

        disease_list = [
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['DiseaseName2']),
        ]

        past_history_row = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            string_utils.int_to_str(row['Continuance']).strip('0'),
            string_utils.xstr(pres_days).strip('0'),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['Massager']),
            ', '.join(disease_list),
        ]

        for column in range(len(past_history_row)):
            self.ui.tableWidget_past_history.setItem(
                row_no, column, QtWidgets.QTableWidgetItem(past_history_row[column])
            )
            if column in [6, 7]:
                self.ui.tableWidget_past_history.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

            if row['InsType'] == '自費':
                self.ui.tableWidget_past_history.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
                )

    def _set_ic_card_treatment_data(self, ic_card):
        if self.system_settings.field('使用讀卡機') != 'Y':
            self.ui.groupBox_ic_card.setVisible(False)
            return

        if self.system_settings.field('讀取卡片就醫記錄') != 'Y':
            self.ui.groupBox_ic_card.setVisible(False)
            return

        self.ui.groupBox_ic_card.setVisible(True)
        ic_card.read_treatment_no_need_hpc()
        treatment_data = ic_card.treatment_data

        html = cshis_utils.get_treatments_html(self.database, treatment_data)
        self.ui.textEdit_treatment_data.setHtml(html)
