#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore, QtGui, QtChart
from PyQt5.QtWidgets import QFileDialog, QMessageBox

import os.path
from lxml import etree as ET

from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import personnel_utils
from libs import export_utils
from libs import xml_utils


# 醫師申報金額業績 2019.08.01
class InsApplyFeePerformance(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsApplyFeePerformance, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = args[2]
        self.apply_month = args[3]
        self.start_date = args[4]
        self.end_date = args[5]
        self.period = args[6]
        self.apply_type = args[7]
        self.clinic_id = args[8]
        self.ins_generate_date = args[9]
        self.ins_total_fee = args[10]
        self.ui = None

        self.apply_date = nhi_utils.get_apply_date(self.apply_year, self.apply_month)
        self.apply_type_code = nhi_utils.APPLY_TYPE_CODE[self.apply_type]

        self._set_ui()
        self._set_signal()
        self._check_ins_apply_fee()

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_APPLY_FEE_PERFORMANCE, self)
        system_utils.set_css(self, self.system_settings)
        self.ui.tableWidget_doctor_xml.setAlternatingRowColors(True)
        self.table_widget_doctor_xml = table_widget.TableWidget(self.ui.tableWidget_doctor_xml, self.database)
        self.table_widget_case_xml = table_widget.TableWidget(self.ui.tableWidget_case_xml, self.database)
        self.center()
        self._set_table_width()

    def _set_table_width(self):
        width = [
            130, 100, 100, 100, 100, 100, 100, 100,
        ]
        self.table_widget_doctor_xml.set_table_heading_width(width)
        self.table_widget_case_xml.set_table_heading_width(width)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_export_doctor_excel.clicked.connect(self.export_doctor_to_excel)
        self.ui.toolButton_export_case_type_excel.clicked.connect(self.export_case_to_excel)

    def _check_ins_apply_fee(self):
        self._check_ins_apply_fee_doctor()
        self._check_ins_apply_fee_case_type()
        self._plot_chart()

    def _check_ins_apply_fee_doctor(self):
        self.ui.tableWidget_doctor_xml.setRowCount(0)

        xml_file_name = nhi_utils.get_ins_xml_file_name(
            self.system_settings, self.apply_type_code, self.apply_date
        )
        if not os.path.isfile(xml_file_name):
            return

        tree = ET.parse(xml_file_name)

        root = tree.getroot()
        self._parse_doctor_ddata(root)
        self._calculate_ins_apply_fee_doctor()
        self.ui.tableWidget_doctor_xml.sortItems(7, QtCore.Qt.DescendingOrder)
        self._calculate_total(self.ui.tableWidget_doctor_xml)

        for row in range(self.ui.tableWidget_doctor_xml.rowCount()):
            for column in range(1, self.ui.tableWidget_doctor_xml.columnCount()):
                item = self.ui.tableWidget_doctor_xml.item(row, column)
                if item is not None:
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _calculate_ins_apply_fee_doctor(self):
        for row_no in range(self.ui.tableWidget_doctor_xml.rowCount()):
            doctor_item = self.ui.tableWidget_doctor_xml.item(row_no, 0)
            if doctor_item is None:
                continue

            doctor_id = doctor_item.text()
            doctor_name = personnel_utils.person_id_to_name(self.database, doctor_id)

            total_fee = number_utils.get_integer(self.ui.tableWidget_doctor_xml.item(row_no, 6).text())
            share_fee = number_utils.get_integer(self.ui.tableWidget_doctor_xml.item(row_no, 7).text())
            ins_apply_fee = total_fee - share_fee

            data = [
                [0, doctor_name],
                [8, ins_apply_fee],
            ]

            for col_no in range(len(data)):
                item = QtWidgets.QTableWidgetItem()
                item.setData(QtCore.Qt.EditRole, data[col_no][1])
                self.ui.tableWidget_doctor_xml.setItem(
                    row_no, data[col_no][0], item,
                )

    def _calculate_total(self, table_widget):
        row_count = table_widget.rowCount()

        table_widget.setRowCount(row_count+1)

        total_count = 0
        total_diag_fee = 0
        total_drug_fee = 0
        total_pharmacy_fee = 0
        total_treat_fee = 0
        total_ins_total_fee = 0
        total_share_fee = 0
        total_ins_apply_fee = 0
        for row_no in range(row_count):
            ord_item = table_widget.item(row_no, 1)
            if ord_item is None:
                continue

            ord_count = number_utils.get_integer(ord_item.text())
            diag_fee = number_utils.get_integer(table_widget.item(row_no, 2).text())
            drug_fee = number_utils.get_integer(table_widget.item(row_no, 3).text())
            pharmacy_fee = number_utils.get_integer(table_widget.item(row_no, 4).text())
            treat_fee = number_utils.get_integer(table_widget.item(row_no, 5).text())
            ins_total_fee = number_utils.get_integer(table_widget.item(row_no, 6).text())
            share_fee = number_utils.get_integer(table_widget.item(row_no, 7).text())
            ins_apply_fee = number_utils.get_integer(table_widget.item(row_no, 8).text())

            total_count += ord_count
            total_diag_fee += diag_fee
            total_drug_fee += drug_fee
            total_pharmacy_fee += pharmacy_fee
            total_treat_fee += treat_fee
            total_ins_total_fee += ins_total_fee
            total_share_fee += share_fee
            total_ins_apply_fee += ins_apply_fee

        data = [
            '合計',
            total_count,
            total_diag_fee,
            total_drug_fee,
            total_pharmacy_fee,
            total_treat_fee,
            total_ins_total_fee,
            total_share_fee,
            total_ins_apply_fee,
        ]

        for col_no in range(len(data)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, data[col_no])
            table_widget.setItem(row_count, col_no, item)

    def _get_cell_value(self, table_widget, row_no, col_no):
        item = table_widget.item(row_no, col_no)
        if item is None:
            return 0

        return number_utils.get_integer(item.text())

    def _parse_doctor_ddata(self, root):
        dbody = root.xpath('//outpatient/ddata/dbody')

        record_count = len(dbody)
        progress_dialog = QtWidgets.QProgressDialog(
            '正在統計醫師申報業績, 請稍後...', '取消', 0, record_count, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for xml_row_no, ddata in zip(range(record_count), dbody):
            progress_dialog.setValue(xml_row_no)
            self._parse_pdata(ddata, self.ui.tableWidget_doctor_xml)

            xdata = xml_utils.convert_node_to_dict(ddata)
            doctor_id = xdata['d30']
            table_widget_row_no = None
            for i in range(self.ui.tableWidget_doctor_xml.rowCount()):
                item = self.ui.tableWidget_doctor_xml.item(i, 0)
                if item is None:
                    break

                if item.text() == doctor_id:
                    table_widget_row_no = i
                    break

            if table_widget_row_no is None:
                table_widget_row_no = self.ui.tableWidget_doctor_xml.rowCount()
                self.ui.tableWidget_doctor_xml.setRowCount(table_widget_row_no+1)

            last_share_fee = self._get_cell_value(self.ui.tableWidget_doctor_xml, table_widget_row_no, 7)
            share_fee = number_utils.get_integer(xdata['d40']) + last_share_fee

            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, share_fee)
            self.ui.tableWidget_doctor_xml.setItem(
                table_widget_row_no, 7, item,
            )

        progress_dialog.setValue(record_count)

    def _parse_pdata(self, ddata, table_widget):
        pdata = ddata.xpath('./pdata')

        for row in pdata:
            xdata = xml_utils.convert_node_to_dict(row)
            doctor_id = xdata['p16']

            table_widget_row_no = None
            for i in range(table_widget.rowCount()):
                item = table_widget.item(i, 0)
                if item is None:
                    break

                if item.text() == doctor_id:
                    table_widget_row_no = i
                    break

            if table_widget_row_no is None:
                table_widget_row_no = table_widget.rowCount()
                table_widget.setRowCount(table_widget_row_no+1)

            last_total_count = self._get_cell_value(table_widget, table_widget_row_no, 1)
            last_diag_fee = self._get_cell_value(table_widget, table_widget_row_no, 2)
            last_drug_fee = self._get_cell_value(table_widget, table_widget_row_no, 3)
            last_pharmacy_fee = self._get_cell_value(table_widget, table_widget_row_no, 4)
            last_treat_fee = self._get_cell_value(table_widget, table_widget_row_no, 5)
            last_total_fee = self._get_cell_value(table_widget, table_widget_row_no, 6)
            last_share_fee = self._get_cell_value(table_widget, table_widget_row_no, 7)
            last_apply_fee = self._get_cell_value(table_widget, table_widget_row_no, 8)

            pdata_fee = {
                'total_count': last_total_count,
                'diag_fee': last_diag_fee,
                'drug_fee': last_drug_fee,
                'pharmacy_fee': last_pharmacy_fee,
                'treat_fee': last_treat_fee,
                'total_fee': last_total_fee,
                'share_fee': last_share_fee,
                'apply_fee': last_apply_fee,
            }
            try:
                price = number_utils.get_integer(xdata['p12'])
            except:
                price = 0

            pdata_fee['total_count'] = last_total_count + 1
            if string_utils.xstr(xdata['p3']) == '0':
                pdata_fee['diag_fee'] = price + last_diag_fee
            elif string_utils.xstr(xdata['p3']) == '1':
                pdata_fee['drug_fee'] = price + last_drug_fee
            elif string_utils.xstr(xdata['p3']) == '2':
                pdata_fee['treat_fee'] = price + last_treat_fee
            elif string_utils.xstr(xdata['p3']) == '9':
                pdata_fee['pharmacy_fee'] = price + last_pharmacy_fee

            pdata_fee['total_fee'] = (
                pdata_fee['diag_fee'] +
                pdata_fee['drug_fee'] +
                pdata_fee['treat_fee'] +
                pdata_fee['pharmacy_fee']
            )

            data = [
                doctor_id,
                pdata_fee['total_count'],
                pdata_fee['diag_fee'],
                pdata_fee['drug_fee'],
                pdata_fee['pharmacy_fee'],
                pdata_fee['treat_fee'],
                pdata_fee['total_fee'],
                pdata_fee['share_fee'],
                pdata_fee['apply_fee'],
            ]

            for col_no in range(len(data)):
                item = QtWidgets.QTableWidgetItem()
                item.setData(QtCore.Qt.EditRole, data[col_no])
                table_widget.setItem(
                    table_widget_row_no, col_no, item,
                )

    def _check_ins_apply_fee_case_type(self):
        self.ui.tableWidget_case_xml.setRowCount(0)

        xml_file_name = nhi_utils.get_ins_xml_file_name(
            self.system_settings, self.apply_type_code, self.apply_date
        )
        if not os.path.isfile(xml_file_name):
            return

        tree = ET.parse(xml_file_name)

        root = tree.getroot()
        self._parse_case_ddata(root)
        self._calculate_ins_apply_fee_case_type()
        self._calculate_total(self.ui.tableWidget_case_xml)

        for row in range(self.ui.tableWidget_case_xml.rowCount()):
            for column in range(1, self.ui.tableWidget_case_xml.columnCount()):
                item = self.ui.tableWidget_case_xml.item(row, column)
                if item is not None:
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _parse_case_ddata(self, root):
        dhead = root.xpath('//outpatient/ddata/dhead')
        dbody = root.xpath('//outpatient/ddata/dbody')

        record_count = len(dbody)
        progress_dialog = QtWidgets.QProgressDialog(
            '正在統計案件分類申報業績, 請稍後...', '取消', 0, record_count, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for xml_row_no, hdata, ddata in zip(range(record_count), dhead, dbody):
            progress_dialog.setValue(xml_row_no)

            xdata = xml_utils.convert_node_to_dict(ddata)
            xhdata = xml_utils.convert_node_to_dict(hdata)
            case_type = xhdata['d1']
            self._parse_ddata(xdata, self.ui.tableWidget_case_xml, case_type)

        progress_dialog.setValue(record_count)

    def _parse_ddata(self, ddata, table_widget, case_type):
        row_no = None
        for i in range(table_widget.rowCount()):
            item = table_widget.item(i, 0)
            if item is None:
                break

            if item.text() == case_type:
                row_no = i
                break

        if row_no is None:
            row_no = table_widget.rowCount()
            table_widget.setRowCount(row_no+1)

        last_total_count = self._get_cell_value(table_widget, row_no, 1)
        last_diag_fee = self._get_cell_value(table_widget, row_no, 2)
        last_drug_fee = self._get_cell_value(table_widget, row_no, 3)
        last_pharmacy_fee = self._get_cell_value(table_widget, row_no, 4)
        last_treat_fee = self._get_cell_value(table_widget, row_no, 5)
        last_total_fee = self._get_cell_value(table_widget, row_no, 6)
        last_share_fee = self._get_cell_value(table_widget, row_no, 7)
        last_apply_fee = self._get_cell_value(table_widget, row_no, 8)

        ddata_fee = {
            'total_count': last_total_count,
            'diag_fee': last_diag_fee,
            'drug_fee': last_drug_fee,
            'pharmacy_fee': last_pharmacy_fee,
            'treat_fee': last_treat_fee,
            'total_fee': last_total_fee,
            'share_fee': last_share_fee,
            'apply_fee': last_apply_fee,
        }

        ddata_fee['total_count'] += 1

        try:
            ddata_fee['diag_fee'] += number_utils.get_integer(ddata['d36'])
        except:
            pass

        try:
            ddata_fee['drug_fee'] += number_utils.get_integer(ddata['d32'])
        except:
            pass

        try:
            ddata_fee['pharmacy_fee'] += number_utils.get_integer(ddata['d38'])
        except:
            pass

        try:
            ddata_fee['treat_fee'] += number_utils.get_integer(ddata['d33'])
        except:
            pass

        try:
            ddata_fee['total_fee'] += number_utils.get_integer(ddata['d39'])
        except:
            pass

        try:
            ddata_fee['share_fee'] += number_utils.get_integer(ddata['d40'])
        except:
            pass

        try:
            ddata_fee['apply_fee'] += number_utils.get_integer(ddata['d41'])
        except:
            pass

        data = [
            case_type,
            ddata_fee['total_count'],
            ddata_fee['diag_fee'],
            ddata_fee['drug_fee'],
            ddata_fee['pharmacy_fee'],
            ddata_fee['treat_fee'],
            ddata_fee['total_fee'],
            ddata_fee['share_fee'],
            ddata_fee['apply_fee'],
        ]

        for col_no in range(len(data)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, data[col_no])
            table_widget.setItem(
                row_no, col_no, item,
            )

    def _calculate_ins_apply_fee_case_type(self):
        for row_no in range(self.ui.tableWidget_case_xml.rowCount()):
            case_type_item = self.ui.tableWidget_case_xml.item(row_no, 0)
            if case_type_item is None:
                continue

            case_type_item = case_type_item.text()
            total_fee = number_utils.get_integer(self.ui.tableWidget_case_xml.item(row_no, 6).text())
            share_fee = number_utils.get_integer(self.ui.tableWidget_case_xml.item(row_no, 7).text())
            ins_apply_fee = total_fee - share_fee

            data = [
                [0, case_type_item],
                [8, ins_apply_fee],
            ]

            for col_no in range(len(data)):
                item = QtWidgets.QTableWidgetItem()
                item.setData(QtCore.Qt.EditRole, data[col_no][1])
                self.ui.tableWidget_case_xml.setItem(
                    row_no, data[col_no][0], item,
                )

    def export_doctor_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出醫師申報業績表",
            '{0}年{1}月醫師申報業績表.xlsx'.format(
                self.apply_year, self.apply_month
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options=options
        )
        if not excel_file_name:
            return

        title = '{clinic_name} {year}年{month}月份醫師申報業績表'.format(
            clinic_name=self.system_settings.field('院所名稱'),
            year=self.apply_year,
            month=self.apply_month,
        )
        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_doctor_xml, None, [1, 2, 3, 4, 5, 6, 7, 8], title
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>醫師申報業績表{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def export_case_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出案件分類申報業績表",
            '{0}年{1}月案件分類申報業績表.xlsx'.format(
                self.apply_year, self.apply_month
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options=options
        )
        if not excel_file_name:
            return

        title = '{clinic_name} {year}年{month}月份案件分類申報業績表'.format(
            clinic_name=self.system_settings.field('院所名稱'),
            year=self.apply_year,
            month=self.apply_month,
        )
        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_case_xml, None, [1, 2, 3, 4, 5, 6, 7, 8], title
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>案件分類申報業績表{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def _plot_chart(self):
        self._plot_doctor_chart()
        self._plot_case_type_chart()

    def _plot_doctor_chart(self):
        series = QtChart.QPieSeries()
        for row_no in range(self.ui.tableWidget_doctor_xml.rowCount()-1):
            doctor_name = self.ui.tableWidget_doctor_xml.item(row_no, 0).text()
            ins_apply_fee = number_utils.get_integer(self.ui.tableWidget_doctor_xml.item(row_no, 8).text())
            series.append(doctor_name, ins_apply_fee)

            slice = series.slices()[row_no]
            slice.setExploded()
            slice.setLabelVisible()

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('醫師申報業績')
        chart.legend().hide()
        chart.setAnimationOptions(QtChart.QChart.AllAnimations)

        chartView = QtChart.QChartView(chart)
        chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        chartView.setFixedWidth(700)
        chartView.setFixedHeight(450)
        self.ui.verticalLayout_chart.addWidget(chartView)

    def _plot_case_type_chart(self):
        case_type_list = []
        bar_set = []
        series = QtChart.QBarSeries()
        for row_no in range(self.ui.tableWidget_case_xml.rowCount()-1):
            case_type = self.ui.tableWidget_case_xml.item(row_no, 0).text()
            ins_apply_fee = number_utils.get_integer(self.ui.tableWidget_case_xml.item(row_no, 8).text())

            case_type_list.append(case_type)
            bar_set.append(QtChart.QBarSet(case_type))
            bar_set[row_no] << ins_apply_fee
            series.append(bar_set[row_no])

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('案件分類申報統計表')
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        categories = ['申報金額']

        axis = QtChart.QBarCategoryAxis()
        axis.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis, series)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(QtCore.Qt.AlignBottom)

        chartView = QtChart.QChartView(chart)
        chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        chartView.setFixedWidth(700)
        self.ui.verticalLayout_chart.addWidget(chartView)
