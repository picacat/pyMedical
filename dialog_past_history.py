# 掛號顯示過去病歷

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QSettings, QSize, QPoint
from libs import ui_settings
from libs import system
from libs import strings
from classes import table_widget


# 主畫面
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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_PAST_HISTORY, self)
        self.ui.resize(self.settings.value("dialog_history_size", QSize(858, 769)))
        self.ui.move(self.settings.value("dialog_history_pos", QPoint(1054, 225)))

        self.table_widget_past_history = table_widget.TableWidget(self.ui.tableWidget_past_history, self.database)
        self.table_widget_past_history.set_column_hidden([0])

        system.set_css(self)
        system.set_theme(self.ui, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('關閉')

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def accepted_button_clicked(self):
        self.close()

    def show_past_history(self, patient_key):
        self.read_data(patient_key)
        if len(self.medical_record) <= 0:
            return

        self.ui.groupBox_past_history.setTitle('{0}的過去病歷'.format(self.patient['Name']))

        self.show()

    def read_data(self, patient_key):
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
        self.patient = self.database.select_record(sql)[0]
        sql = 'SELECT * FROM cases WHERE PatientKey = {0} ORDER BY CaseDate DESC'.format(patient_key)
        self.medical_record = self.database.select_record(sql)
        self.table_widget_past_history.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, rec_no, rec):
        wait_rec = [
            str(rec['CaseKey']),
            str(rec['CaseDate']),
            str(rec['InsType']),
            str(rec['TreatType']),
            str(rec['Card']),
            strings.int_to_str(rec['Continuance']).strip('0'),
            str(rec['Doctor']),
            str(rec['Massager']),
        ]

        for column in range(0, self.ui.tableWidget_past_history.columnCount()):
            self.ui.tableWidget_past_history.setItem(rec_no, column, QtWidgets.QTableWidgetItem(wait_rec[column]))
            if column in [5]:
                self.ui.tableWidget_past_history.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            if rec['InsType'] == '自費':
                self.ui.tableWidget_past_history.item(rec_no, column).setForeground(QtGui.QColor('blue'))
