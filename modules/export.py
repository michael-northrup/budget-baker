"""
Export Module - CSV and PDF export functionality
"""

import polars as pl
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from io import BytesIO
import tempfile
import os


def export_to_csv(df: pl.DataFrame) -> bytes:
    """
    Export categorized transactions to CSV

    Args:
        df: Polars DataFrame with categorized transactions

    Returns:
        CSV file as bytes
    """
    # Format the dataframe for export
    export_df = df.select([
        'date',
        'description',
        'amount',
        'category',
        'confidence',
        'type',
        'check_number',
        'original_category'
    ])

    # Convert to CSV bytes
    csv_string = export_df.write_csv()
    return csv_string.encode('utf-8')


def export_to_pdf(
    df: pl.DataFrame,
    summary_stats: dict,
    pie_chart: go.Figure = None,
    bar_chart: go.Figure = None
) -> bytes:
    """
    Export categorized transactions to PDF report

    Args:
        df: Polars DataFrame with categorized transactions
        summary_stats: Dictionary with income, expenses, net
        pie_chart: Plotly pie chart figure (optional)
        bar_chart: Plotly bar chart figure (optional)

    Returns:
        PDF file as bytes
    """
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for PDF elements
    story = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4CAF50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12
    )

    # Title
    story.append(Paragraph("Budget Baker - Transaction Analysis Report", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Date range
    min_date = df['date'].min()
    max_date = df['date'].max()
    date_range_text = f"Period: {min_date.strftime('%m/%d/%Y')} - {max_date.strftime('%m/%d/%Y')}"
    story.append(Paragraph(date_range_text, styles['Normal']))

    generated_text = f"Generated: {datetime.now().strftime('%m/%d/%Y %I:%M %p')}"
    story.append(Paragraph(generated_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Summary Statistics
    story.append(Paragraph("Summary", heading_style))

    summary_data = [
        ['Metric', 'Amount'],
        ['Total Income', f"${summary_stats.get('income', 0):,.2f}"],
        ['Total Expenses', f"${summary_stats.get('expenses', 0):,.2f}"],
        ['Net', f"${summary_stats.get('net', 0):,.2f}"],
        ['Total Transactions', str(summary_stats.get('total_transactions', len(df)))]
    ]

    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))

    # Category Breakdown
    story.append(Paragraph("Spending by Category", heading_style))

    # Get category summary (expenses only)
    expenses = df.filter(pl.col('type') == 'Expense')
    if len(expenses) > 0:
        category_summary = expenses.group_by('category').agg([
            pl.count().alias('count'),
            pl.col('amount').sum().abs().alias('total'),
            pl.col('amount').mean().abs().alias('average')
        ]).sort('total', descending=True)

        category_data = [['Category', '# Trans', 'Total', 'Average']]
        for row in category_summary.iter_rows():
            category_data.append([
                row[0],
                str(row[1]),
                f"${row[2]:,.2f}",
                f"${row[3]:,.2f}"
            ])

        category_table = Table(category_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch])
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        story.append(category_table)
    else:
        story.append(Paragraph("No expense transactions found.", styles['Normal']))

    story.append(Spacer(1, 0.3*inch))

    # Add charts if provided
    if pie_chart or bar_chart:
        story.append(PageBreak())
        story.append(Paragraph("Visual Analysis", heading_style))
        story.append(Spacer(1, 0.2*inch))

        # Convert charts to images using kaleido
        temp_files = []  # Keep track of temp files to clean up later

        if pie_chart:
            try:
                # Export chart as PNG
                img_bytes = pie_chart.to_image(format="png", width=600, height=400)

                # Create temporary file for the image (don't delete yet)
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                tmp_file.write(img_bytes)
                tmp_file.close()
                temp_files.append(tmp_file.name)

                # Add image to PDF
                img = Image(tmp_file.name, width=5*inch, height=3.33*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                story.append(Paragraph(f"Note: Pie chart visualization not available", styles['Normal']))

        if bar_chart:
            try:
                # Export chart as PNG
                img_bytes = bar_chart.to_image(format="png", width=600, height=400)

                # Create temporary file for the image (don't delete yet)
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                tmp_file.write(img_bytes)
                tmp_file.close()
                temp_files.append(tmp_file.name)

                # Add image to PDF
                img = Image(tmp_file.name, width=5*inch, height=3.33*inch)
                story.append(img)
            except Exception as e:
                story.append(Paragraph(f"Note: Bar chart visualization not available", styles['Normal']))

    # Transaction Details (first 50 transactions)
    story.append(PageBreak())
    story.append(Paragraph("Transaction Details", heading_style))
    story.append(Paragraph("(Showing first 50 transactions)", styles['Italic']))
    story.append(Spacer(1, 0.2*inch))

    # Sample transactions -- use named rows for robustness regardless of column order
    sample_df = df.head(50)
    trans_data = [['Date', 'Description', 'Amount', 'Category']]

    for row in sample_df.iter_rows(named=True):
        date_val = row['date'].strftime('%m/%d/%Y') if row['date'] else ''
        desc_val = str(row['description'])[:40] + '...' if len(str(row['description'])) > 40 else str(row['description'])
        amount_val = f"${row['amount']:,.2f}"
        category_val = str(row['category'])

        trans_data.append([date_val, desc_val, amount_val, category_val])

    trans_table = Table(trans_data, colWidths=[1*inch, 2.5*inch, 1*inch, 1.5*inch])
    trans_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))

    story.append(trans_table)

    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Generated by Budget Baker - Privacy-first transaction categorization", footer_style))

    # Build PDF
    doc.build(story)

    # Clean up temporary image files
    for tmp_path in temp_files:
        try:
            os.unlink(tmp_path)
        except:
            pass

    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
