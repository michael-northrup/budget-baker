"""
Visualization Module - Interactive charts using Plotly
Converts Polars DataFrames to Pandas for Plotly compatibility
"""

import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import pandas as pd
from typing import Optional

# Baking-themed color palette
BAKING_PALETTE = [
    '#D97706',  # Amber (primary)
    '#EA580C',  # Orange
    '#DC2626',  # Red
    '#F59E0B',  # Yellow-orange
    '#B45309',  # Brown
    '#92400E',  # Dark brown
    '#FCD34D',  # Golden
    '#FB923C',  # Light orange
    '#FDBA74',  # Peach
    '#FCA5A5',  # Rose
    '#F97316',  # Vibrant orange
    '#C2410C',  # Deep orange
]

# Chart layout defaults for baking theme
CHART_LAYOUT_DEFAULTS = {
    'plot_bgcolor': '#FFFBF0',      # Cream background
    'paper_bgcolor': '#FEF3E2',     # Match app background
    'font': dict(
        family='Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        color='#292524',
        size=14
    )
}


def create_expense_pie_chart(df: pl.DataFrame) -> go.Figure:
    """
    Create pie chart showing expense distribution by category
    Excludes Income and Transfers
    """
    # Filter to expenses only (Polars)
    expenses = df.filter(pl.col('type') == 'Expense')

    if len(expenses) == 0:
        # Create empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No expense transactions to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=400)
        return fig

    # Group by category and sum amounts (make positive for display)
    category_totals = expenses.group_by('category').agg([
        pl.col('amount').sum().abs().alias('total')
    ]).sort('total', descending=True)

    # Convert to pandas for Plotly
    category_totals_pd = category_totals.to_pandas().set_index('category')['total']

    # Create pie chart with baking palette
    fig = px.pie(
        values=category_totals_pd.values,
        names=category_totals_pd.index,
        title="🍰 Spending by Category",
        hole=0.45,  # Larger donut = mixing bowl feel
        color_discrete_sequence=BAKING_PALETTE
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percent: %{percent}<extra></extra>',
        marker=dict(line=dict(color='#FFFFFF', width=2))  # White borders between slices
    )

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=12)
        ),
        title=dict(
            font=dict(size=18, color='#92400E'),
            x=0.5,
            xanchor='center'
        )
    )

    return fig


def create_category_bar_chart(df: pl.DataFrame) -> go.Figure:
    """
    Create bar chart showing spending by category
    Sorted by amount (descending)
    """
    # Filter to expenses only (Polars)
    expenses = df.filter(pl.col('type') == 'Expense')

    if len(expenses) == 0:
        # Create empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No expense transactions to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=400)
        return fig

    # Group by category and sum amounts (make positive)
    category_totals = expenses.group_by('category').agg([
        pl.col('amount').sum().abs().alias('total')
    ]).sort('total', descending=False)  # Ascending for horizontal bar

    # Convert to pandas for Plotly
    category_totals_pd = category_totals.to_pandas().set_index('category')['total']

    # Create bar chart with baking gradient
    fig = go.Figure([go.Bar(
        x=category_totals_pd.values,
        y=category_totals_pd.index,
        orientation='h',
        marker=dict(
            color=category_totals_pd.values,
            colorscale=[
                [0, '#FCD34D'],    # Golden (low)
                [0.5, '#F59E0B'],  # Yellow-orange (medium)
                [1, '#D97706']     # Amber (high)
            ],
            line=dict(color='#92400E', width=1)
        ),
        hovertemplate='<b>%{y}</b><br>Total: $%{x:,.2f}<extra></extra>'
    )])

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        title=dict(
            text="📊 Category Totals",
            font=dict(size=18, color='#92400E'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Total Spent ($)",
            gridcolor='#FED7AA',
            tickfont=dict(family='Inter')
        ),
        yaxis=dict(
            title="Category",
            gridcolor='#FED7AA'
        ),
        height=max(400, len(category_totals_pd) * 30),  # Dynamic height based on categories
        showlegend=False
    )

    return fig


def create_monthly_trend_chart(df: pl.DataFrame) -> Optional[go.Figure]:
    """
    Create line chart showing spending trends over time
    Only created if data spans multiple months
    """
    # Check if data spans multiple months
    date_range = (df['date'].max() - df['date'].min()).days

    if date_range < 30:
        return None  # Not enough data for monthly trend

    # Add month column (Polars)
    df_with_month = df.with_columns([
        pl.col('date').dt.strftime('%Y-%m').alias('month')
    ])

    # Group by month and type
    monthly_data = df_with_month.group_by(['month', 'type']).agg([
        pl.col('amount').sum().alias('amount')
    ]).sort('month')

    # Convert to pandas for Plotly
    monthly_data_pd = monthly_data.to_pandas()

    # Separate income and expenses
    income_data = monthly_data_pd[monthly_data_pd['type'] == 'Income']
    expense_data = monthly_data_pd[monthly_data_pd['type'] == 'Expense'].copy()
    expense_data['amount'] = expense_data['amount'].abs()

    # Create figure
    fig = go.Figure()

    # Add income trace with gradient fill
    if len(income_data) > 0:
        fig.add_trace(go.Scatter(
            x=income_data['month'],
            y=income_data['amount'],
            mode='lines+markers',
            name='💰 Income',
            line=dict(color='#10B981', width=3),
            marker=dict(size=8, line=dict(color='#FFFFFF', width=2)),
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.1)',
            hovertemplate='<b>Income</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
        ))

    # Add expense trace with gradient fill
    if len(expense_data) > 0:
        fig.add_trace(go.Scatter(
            x=expense_data['month'],
            y=expense_data['amount'],
            mode='lines+markers',
            name='💸 Expenses',
            line=dict(color='#D97706', width=3),
            marker=dict(size=8, line=dict(color='#FFFFFF', width=2)),
            fill='tozeroy',
            fillcolor='rgba(217, 119, 6, 0.1)',
            hovertemplate='<b>Expenses</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
        ))

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        title=dict(
            text="📈 Monthly Trend",
            font=dict(size=18, color='#92400E'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Month",
            gridcolor='#FED7AA',
            showgrid=True
        ),
        yaxis=dict(
            title="Amount ($)",
            gridcolor='#FED7AA',
            showgrid=True,
            tickfont=dict(family='Inter')
        ),
        height=400,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )

    return fig


def export_chart_as_image(fig: go.Figure, filename: str = "chart.png") -> bytes:
    """
    Export Plotly chart as static image (PNG)
    Used for PDF export in Phase 7

    Requires kaleido package
    """
    try:
        img_bytes = fig.to_image(format="png", width=800, height=600)
        return img_bytes
    except Exception as e:
        print(f"Error exporting chart: {e}")
        return None
