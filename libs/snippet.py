from PyQt5 import QtWidgets
import db
import number
import strings


def set_past_record(self):
    self.ui.scrollArea_past.setWidgetResizable(True)
    past_record = db.select_record(self.cnx,
                                   'select * from cases where '
                                   'PatientKey = {0} and '
                                   'CaseKey != {1} '
                                   'order by CaseDate desc'
                                   .format(self.patient_data['PatientKey'],
                                           self.medical_record['CaseKey']))
    for rec in past_record:
        card = str(rec['Card'])
        if number.get_integer(rec['Continuance']) >= 1:
            card += '-' + str(rec['Continuance'])

        if rec['InsType'] == '自費':
            card = ''
        else:
            card = '卡序: {0}'.format(card)

        group_box = QtWidgets.QGroupBox('日期: {0} {1} {2}'
                                        .format(str(rec['CaseDate']),
                                                str(rec['InsType']),
                                                card)
                                        )
        group_box.setFixedHeight(500)
        group_layout = QtWidgets.QVBoxLayout()
        group_layout.setContentsMargins(0, 0, 0, 0)

        text_edit = QtWidgets.QTextEdit()
        record_summary = self.get_record_summary(rec)
        text_edit.setHtml(record_summary)
        text_edit.setReadOnly(True)
        button = QtWidgets.QPushButton('拷貝病歷')
        button.setProperty("caseKey", rec['CaseKey'])
        button.clicked.connect(self.copy_past_medical_record_button_clicked)

        group_layout.addWidget(text_edit)
        group_layout.addWidget(button)
        group_box.setLayout(group_layout)
        self.ui.verticalLayout_past.addWidget(group_box)


# 拷貝病歷
def on_copy_button_clicked(self):
    case_key = self.sender().property('caseKey')
    script = 'select * from cases where CaseKey = {0}'.format(case_key)
    row = db.select_record(self.cnx, script)[0]
    if self.ui.checkBox_symptom.isChecked():
        self.ui.textEdit_symptom.setText(strings.get_str(row['Symptom'], 'utf8'))
    if self.ui.checkBox_tongue.isChecked():
        self.ui.textEdit_tongue.setText(strings.get_str(row['Tongue'], 'utf8'))
    if self.ui.checkBox_pulse.isChecked():
        self.ui.textEdit_pulse.setText(strings.get_str(row['Pulse'], 'utf8'))
    if self.ui.checkBox_remark.isChecked():
        self.ui.textEdit_remark.setText(strings.get_str(row['Remark'], 'utf8'))

