from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import copy

from libs import string_utils
from libs import number_utils


light_blue = PatternFill(start_color='99CCFF', end_color='99CCFF', fill_type='solid')
light_yellow = PatternFill(start_color='FFFF99', end_color='FFFF99', fill_type='solid')
light_gray = PatternFill(start_color='C0C0C0', end_color='C0C0C0', fill_type='solid')
salmon = PatternFill(start_color='FFB266', end_color='FFB266', fill_type='solid')
purple = PatternFill(start_color='FF9999', end_color='FF9999', fill_type='solid')
align_center = Alignment(horizontal='center', vertical='center')
bold = Font(bold=True)
side = Side(border_style='thin', color = '000000')
border = Border(top=side, bottom=side, left=side, right=side)


def export_table_widget_to_excel(excel_file_name, table_widget, hidden_column=None):
    wb = Workbook()
    ws = wb.active
    ws.title = '預約門診資料'

    header_row = []
    for col_no in range(table_widget.columnCount()):
        if hidden_column is not None and col_no in hidden_column:
            continue

        header_row.append(table_widget.horizontalHeaderItem(col_no).text())

    ws.append(header_row)

    for row_no in range(table_widget.rowCount()):
        row = []
        for col_no in range(table_widget.columnCount()):
            if hidden_column is not None and col_no in hidden_column:
                continue

            item = table_widget.item(row_no, col_no)
            if item is not None:
                item_text = item.text()
            else:
                item_text = ''

            row.append(item_text)

        ws.append(row)

    wb.save(excel_file_name)


# 匯出日報表 From medical_record_list 2019.07.01
def export_daily_medical_records_to_excel(database, system_settings, excel_file_name, table_widget):
    row_range = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U'
    ]

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = '門診日報表資料'

    sheet.append([
        '{clinic_name} 日報表'.format(
            clinic_name=system_settings.field('院所名稱'),
        )
    ])
    sheet.merge_cells('A1:U1')
    row_property = sheet.row_dimensions[1]
    row_property.height = 30
    row_property.alignment = align_center
    row_property.font = bold

    header_row = [
        '日期', '班別', '醫師', '保險', '病歷號', '病患姓名', '診號', '卡序', '療程',
        '掛號費', '門診負擔', '藥品負擔', '自費品項', '自費金額',
        '推拿金額', '推拿自費品項', '推拿自費金額', '推拿師', '押單', '備註', '合計',
    ]
    sheet.append(header_row)
    sheet.row_dimensions[2].height = 30

    sheet.column_dimensions['A'].width = 14
    sheet.column_dimensions['B'].width = 5
    sheet.column_dimensions['D'].width = 5
    sheet.column_dimensions['G'].width = 6
    sheet.column_dimensions['H'].width = 6
    sheet.column_dimensions['I'].width = 5
    sheet.column_dimensions['M'].width = 24
    sheet.column_dimensions['P'].width = 24
    sheet.column_dimensions['Q'].width = 12

    total_regist_fee = 0
    total_diag_share_fee = 0
    total_drug_share_fee = 0
    total_purchase_item_fee = 0
    total_massage_item_fee = 0
    total_deposit_fee = 0
    ins_count = 0

    daily_regist_fee = 0
    daily_diag_share_fee = 0
    daily_drug_share_fee = 0
    daily_purchase_item_fee = 0
    daily_massage_item_fee = 0
    daily_deposit_fee = 0
    daily_total = 0
    daily_ins_count = 0

    for row_no in range(table_widget.rowCount()):
        check_box = table_widget.cellWidget(row_no, 1)
        if not check_box.isChecked():
            continue

        case_key = table_widget.item(row_no, 0).text()
        sql = '''
            SELECT 
                cases.DepositFee, cases.Massager, patient.DiscountType
            FROM cases
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                CaseKey = {case_key}
        '''.format(
            case_key=case_key
        )
        case_row = database.select_record(sql)
        if len(case_row) > 0:
            case_row = case_row[0]
            deposit_fee = number_utils.get_integer(case_row['DepositFee'])
            massager = string_utils.xstr(case_row['Massager'])
            discount_type = string_utils.xstr(case_row['DiscountType'])
        else:
            deposit_fee = 0
            massager = ''
            discount_type = ''

        case_date = table_widget.item(row_no, 2).text()[:10]
        period = table_widget.item(row_no, 3).text()[:1]
        next_case_date = table_widget.item(row_no+1, 2)
        if next_case_date is not None:
            next_case_date = next_case_date.text()[:10]

        next_period = table_widget.item(row_no+1, 3)
        if next_period is not None:
            next_period = next_period.text()[:1]

        ins_type = table_widget.item(row_no, 12).text()
        if ins_type == '健保':
            ins_count += 1

        card = table_widget.item(row_no, 15).text()
        if card == '不需取得':
            card = ''

        regist_fee = number_utils.get_integer(table_widget.item(row_no, 21).text())
        diag_share_fee = number_utils.get_integer(table_widget.item(row_no, 22).text())
        drug_share_fee = number_utils.get_integer(table_widget.item(row_no, 23).text())

        total_regist_fee += regist_fee
        total_diag_share_fee += diag_share_fee
        total_drug_share_fee += drug_share_fee
        total_deposit_fee += deposit_fee

        sale_item = ''

        row = [
            case_date,
            period,
            table_widget.item(row_no, 17).text(),
            ins_type,
            table_widget.item(row_no, 8).text(),
            table_widget.item(row_no, 9).text(),
            table_widget.item(row_no, 7).text(),
            card,
            table_widget.item(row_no, 16).text(),

            regist_fee,
            diag_share_fee,
            drug_share_fee,
            sale_item,
            number_utils.get_integer(table_widget.item(row_no, 24).text()),
            None, None,
            0,  # massage_fee
            massager,
            deposit_fee,
            discount_type,
        ]
        sql = '''
            SELECT * FROM prescript
            WHERE
                CaseKey = {case_key} AND
                MedicineSet = 2 AND
                Amount > 0
            ORDER BY PrescriptKey
        '''.format(
            case_key=case_key,
        )
        prescript_rows = database.select_record(sql)
        if len(prescript_rows) <= 0:
            sheet.append(row)
        else:
            for prescript_row_no, prescript_row in zip(range(len(prescript_rows)), prescript_rows):
                if massager == '':
                    purchase_item = string_utils.xstr(prescript_row['MedicineName'])
                    purchase_item_fee = number_utils.get_integer(prescript_row['Amount'])
                    massage_item = ''
                    massage_item_fee = 0
                    total_purchase_item_fee += purchase_item_fee
                else:
                    purchase_item = ''
                    purchase_item_fee = 0
                    massage_item = string_utils.xstr(prescript_row['MedicineName'])
                    massage_item_fee = number_utils.get_integer(prescript_row['Amount'])
                    total_massage_item_fee += massage_item_fee

                row[12] = purchase_item
                row[13] = purchase_item_fee
                row[15] = massage_item
                row[16] = massage_item_fee

                if prescript_row_no > 0:
                    row[3] = ''
                    row[7] = ''
                    row[8] = ''
                    row[9] = 0
                    row[10] = 0
                    row[11] = 0

                sheet.append(row)

        if (case_date == next_case_date and period != next_period) or (case_date != next_case_date):
            subtotal = total_regist_fee + total_diag_share_fee + total_drug_share_fee + \
                       total_purchase_item_fee + total_massage_item_fee + total_deposit_fee
            subtotal_row = [
                row[0], row[1], None,
                ins_count,
                None, None, None, None, None,
                total_regist_fee,
                total_diag_share_fee,
                total_drug_share_fee,
                None,
                total_purchase_item_fee,
                None, None,
                total_massage_item_fee,
                None,
                total_deposit_fee,
                None,
                subtotal,
            ]
            sheet.append(subtotal_row)

            for col in row_range:
                cell = sheet['{col}{row_no}'.format(col=col, row_no=sheet._current_row)]
                cell.fill = salmon
                cell.font = bold

            daily_ins_count += ins_count
            daily_regist_fee += total_regist_fee
            daily_diag_share_fee += total_diag_share_fee
            daily_drug_share_fee += total_drug_share_fee
            daily_purchase_item_fee += total_purchase_item_fee
            daily_massage_item_fee += total_massage_item_fee
            daily_deposit_fee += total_deposit_fee
            daily_total += subtotal

            ins_count = 0
            total_regist_fee = 0
            total_diag_share_fee = 0
            total_drug_share_fee = 0
            total_purchase_item_fee = 0
            total_massage_item_fee = 0
            total_deposit_fee = 0

        if case_date != next_case_date:
            sheet.append([
                row[0], '全', None,
                daily_ins_count,
                None, None, None, None, None,
                daily_regist_fee,
                daily_diag_share_fee,
                daily_drug_share_fee,
                None,
                daily_purchase_item_fee,
                None, None,
                daily_massage_item_fee,
                None,
                daily_deposit_fee,
                None,
                daily_total,
            ])
            for col in row_range:
                cell = sheet['{col}{row_no}'.format(col=col, row_no=sheet._current_row)]
                cell.fill = purple
                cell.font = bold

            daily_ins_count = 0
            daily_regist_fee = 0
            daily_diag_share_fee = 0
            daily_drug_share_fee = 0
            daily_purchase_item_fee = 0
            daily_massage_item_fee = 0
            daily_deposit_fee = 0
            daily_total = 0

    for row_no in ['E2', 'F2', 'G2', 'H2', 'I2']:
        sheet[row_no].fill = light_blue
        sheet[row_no].font = bold
        sheet[row_no].alignment = align_center

    for row_no in ['J2', 'K2', 'L2']:
        sheet[row_no].fill = light_yellow
        sheet[row_no].font = bold
        sheet[row_no].alignment = align_center

    for row_no in ['M2', 'N2', 'O2', 'P2', 'Q2', 'R2']:
        sheet[row_no].fill = light_gray
        sheet[row_no].font = bold
        sheet[row_no].alignment = align_center

    for row_no in range(2, len(sheet['A'])+1):
        for col in row_range:
            cell = sheet['{col}{row_no}'.format(col=col, row_no=row_no)]
            cell.border = border
            cell.alignment = align_center
            if row_no == 2:
                cell.font = bold

    for row_no in [2, 3]:
        for col in row_range+['V']:
            cell = sheet['{col}{row_no}'.format(col=col, row_no=row_no)]
            sheet.freeze_panes = cell

    workbook.save(excel_file_name)
