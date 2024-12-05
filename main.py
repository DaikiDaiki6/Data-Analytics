import base64
import datetime
import io
import os

from dash import Dash, dcc, html, dash_table, Input, Output, State, MATCH, no_update
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import dash_bootstrap_components as dbc

app = Dash(__name__,
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)

# Color Palette Configuration
CUSTOM_COLORS = {
    'line': '#1E88E5',  # Material Blue
    'bar': '#4CAF50',  # Material Green
    'bubble': '#FF5722',  # Material Deep Orange
    'doughnut': '#9C27B0',  # Material Purple
    'polar': '#FFC107'  # Material Amber
}

app.layout = html.Div([
    html.H1('Advanced Data Visualization Dashboard',
            style={'textAlign': 'center', 'color': '#333'}),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True
    ),

    # Progress Bar for File Upload
    dbc.Progress(id='upload-progress', value=0,
                 style={'height': '20px', 'margin': '10px 0'}),

    html.Div(id='output-data-upload', children=[]),
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))

        # Enhanced Column Selection
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        all_columns = df.columns.tolist()

        return df, numeric_columns, all_columns
    except Exception as e:
        print(e)
        return None, [], []


@app.callback(
    [Output('output-data-upload', 'children'),
     Output('upload-progress', 'value')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename'),
     State('upload-data', 'last_modified')],
    prevent_initial_call=True
)
def update_output(contents, filename, date):
    children = []
    progress = 0

    if contents is not None:
        for i, (c, n, d) in enumerate(zip(contents, filename, date)):
            # Update progress
            progress = int((i + 1) / len(contents) * 100)

            df, numeric_columns, all_columns = parse_contents(c, n, d)

            if df is not None:
                children.append(create_file_section(df, n, numeric_columns, all_columns, i))

    return children, progress


def create_file_section(df, filename, numeric_columns, all_columns, index):
    return html.Div([
        html.H5(filename),

        # Enhanced Styled Table
        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i, 'selectable': True} for i in df.columns],
            page_size=10,
            filter_action='native',
            sort_action='native',
            column_selectable='single',
            selected_columns=[df.columns[0]],
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)'},
            id={'type': 'dynamic-table', 'index': index},
        ),

        # Axis Configuration
        html.Div([
            html.Div([
                html.Label('X-Axis:', style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id={'type': 'x-axis-dropdown', 'index': index},
                    options=[{'label': col, 'value': col} for col in all_columns],
                    value=all_columns[0]
                )
            ], style={'width': '48%', 'display': 'inline-block'}),

            html.Div([
                html.Label('Y-Axis:', style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id={'type': 'y-axis-dropdown', 'index': index},
                    options=[{'label': col, 'value': col} for col in numeric_columns],
                    value=numeric_columns[0] if numeric_columns else None
                )
            ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
        ], style={'padding': '10px'}),

        # Enhanced Graphs with Custom Styling
        dcc.Graph(id={'type': 'line-graph', 'index': index}, figure={}),
        dcc.Graph(id={'type': 'bar-graph', 'index': index}, figure={}),
        dcc.Graph(id={'type': 'bubble-graph', 'index': index}, figure={}),
        dcc.Graph(id={'type': 'doughnut-graph', 'index': index}, figure={}),
        dcc.Graph(id={'type': 'polar-graph', 'index': index}, figure={}),

        html.Hr()
    ])


# Line Chart with Enhanced Customization
@app.callback(
    Output({'type': 'line-graph', 'index': MATCH}, 'figure'),
    [Input({'type': 'dynamic-table', 'index': MATCH}, 'derived_virtual_data'),
     Input({'type': 'x-axis-dropdown', 'index': MATCH}, 'value'),
     Input({'type': 'y-axis-dropdown', 'index': MATCH}, 'value')]
)
def create_line_chart(filtered_data, x_col, y_col):
    if not filtered_data or not x_col or not y_col:
        return {}

    df = pd.DataFrame(filtered_data)

    fig = px.line(df, x=x_col, y=y_col,
                  title=f'Line Chart: {y_col} vs {x_col}',
                  color_discrete_sequence=[CUSTOM_COLORS['line']],
                  hover_data=[x_col, y_col])

    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col,
        plot_bgcolor='rgba(240,240,240,0.5)'
    )
    return fig


# Additional chart creation functions would follow similar enhancements...
# (Bar, Bubble, Doughnut, Polar chart callbacks with similar customizations)

if __name__ == '__main__':
    app.run_server(debug=True)