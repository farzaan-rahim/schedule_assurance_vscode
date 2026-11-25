"""Streaming Excel projection. No comparisons, formulas or scheduling calls."""
from io import BytesIO
from datetime import datetime
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from app.reporting.formatting import (
    BODY_ALIGNMENT, BODY_FONT, FILLS, HEADER_FILL, HEADER_FONT, NAVY, NUMBER_FORMATS, excel_value,
)
from app.reporting.limits import ReportLimitError

FILENAME = "Schedule Assurance Forensic Change Report.xlsx"
MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def row_value(row,key):
    if key in row.cells:return row.cells[key]
    if key in ('classification','availability','provenance','diagnostics'):return getattr(row,key)
    return getattr(row.context,key,None) if row.context is not None else None


class ExcelReportRenderer:
    def render(self, report):
        workbook=Workbook(write_only=True)
        workbook.properties.title=report.metadata.report_title
        workbook.properties.creator=report.metadata.generated_by or 'Schedule Assurance'
        workbook.properties.description='Imported comparison and application results remain separate. Aware timestamps are displayed in UTC; naive P6 dates retain source clock time.'
        for section in report.sections:
            if len(section.rows)>1_048_570:
                raise ReportLimitError('Excel worksheet row limit exceeded; no records were truncated.')
            sheet=workbook.create_sheet(section.sheet_name)
            sheet.sheet_view.showGridLines=False
            sheet.sheet_format.defaultRowHeight=32
            sheet.sheet_properties.pageSetUpPr.fitToPage=True
            sheet.sheet_properties.outlinePr.summaryRight=False
            sheet.freeze_panes='D7' if any(c.key=='activity_id' for c in section.columns) else 'A7'
            sheet.sheet_properties.tabColor=NAVY
            sheet.print_title_rows='1:6'
            sheet.row_dimensions[1].height=30
            sheet.row_dimensions[2].height=30
            sheet.row_dimensions[3].height=30
            sheet.row_dimensions[4].height=26
            sheet.row_dimensions[5].height=54
            for n in range(1,6):
                sheet.merged_cells.add(f'A{n}:{get_column_letter(min(8,len(section.columns)))}{n}')
            sheet.row_dimensions[6].height=45
            for index,column in enumerate(section.columns,1):
                sheet.column_dimensions[get_column_letter(index)].width=column.width
            def text_row(text,bold=False):
                cell=WriteOnlyCell(sheet,value=excel_value(text));cell.data_type='s'
                cell.font=Font(name='Calibri',size=16 if bold else 11,bold=bold,color=NAVY)
                cell.alignment=BODY_ALIGNMENT
                return [cell]
            meta=report.metadata
            sheet.append(text_row(meta.report_title,True))
            sheet.append(text_row(f"Source: {meta.baseline.filename}   Data Date: {meta.baseline.data_date or 'Unavailable'}"))
            sheet.append(text_row(f"Current: {meta.current.filename}   Data Date: {meta.current.data_date or 'Unavailable'}"))
            sheet.append(text_row(f"{section.title}   Records: {section.count}   Availability: {section.availability.value}",True))
            selected=meta.selected_analysis_anchor
            selected_code=getattr(selected,'activity_code',None) if selected is not None else None
            sheet.append(text_row(f"Report {meta.report_identifier}   Generated {meta.generated_at.isoformat()}   Completion authority: {meta.completion_authority_status}; Selected Analysis Anchor: {selected_code}" + ('\n'+section.message if section.message else '')))
            headers=[]
            for column in section.columns:
                cell=WriteOnlyCell(sheet,value=column.title);cell.font=HEADER_FONT;cell.fill=HEADER_FILL;cell.alignment=BODY_ALIGNMENT;headers.append(cell)
            sheet.append(headers)
            sheet.auto_filter.ref=f'A6:{get_column_letter(len(section.columns))}{max(6,len(section.rows)+6)}'
            if not section.rows:
                sheet.row_dimensions[7].height=60
                sheet.merged_cells.add(f'A7:{get_column_letter(min(8,len(section.columns)))}7')
                sheet.append(text_row(section.message or 'No changes identified'))
            for row in section.rows:
                output=[]
                for column in section.columns:
                    value=excel_value(row_value(row,column.key))
                    cell=WriteOnlyCell(sheet,value=value)
                    # Force external text to string: activity labels must never become formulas.
                    if isinstance(value,str):cell.data_type='s'
                    cell.font=BODY_FONT;cell.alignment=BODY_ALIGNMENT
                    cell.number_format=NUMBER_FORMATS['date'] if isinstance(value,datetime) else NUMBER_FORMATS.get(column.data_type,'General')
                    if column.key in {'classification','availability','calculation_availability','free_float_availability'}:
                        if str(value) in FILLS:cell.fill=FILLS[str(value)]
                    output.append(cell)
                sheet.append(output)
        buffer=BytesIO();workbook.save(buffer)
        return buffer.getvalue()
