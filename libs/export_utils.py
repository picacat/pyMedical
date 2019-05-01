from openpyxl import Workbook


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

