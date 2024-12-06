import base64
import datetime
import io

from numpy import size
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, dash_table, Input, Output, State, MATCH, no_update
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd



# Initialize the app with the SOLAR theme
app = Dash(__name__, external_stylesheets=[dbc.themes.SOLAR], suppress_callback_exceptions=True)

app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1('GoReport!📈', style={'textAlign': 'center'}), width=12),  # Full width for title
        ], style={'margin-bottom': '20px'}),

        dbc.Row([
            dbc.Col(html.H3('Dashboard of Multiple Chart Types', style={'textAlign': 'center'}), width=12),  # Full width for subtitle
        ], style={'margin-bottom': '30px'}),

        dbc.Row([
            dbc.Col(dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select CSV/XLS Files')
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
            ), width=12)  # Full width for file upload
        ], justify="center"),  # Center the file upload button

        html.Div(id='output-data-upload', children=[]),
    ], fluid=True),
])


@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              State('output-data-upload', 'children'),
              prevent_initial_call=True
              )
def update_output(contents, filename, date, children):
    if contents is not None:
        children = []  # for getting new CSV/XLS file fix error

        for i, (c, n, d) in enumerate(zip(contents, filename, date)):
            content_type, content_string = contents[i].split(',')

            decoded = base64.b64decode(content_string)
            try:
                if 'csv' in filename[i]:
                    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                elif 'xls' in filename[i]:
                    df = pd.read_excel(io.BytesIO(decoded))

                # Convert all numeric columns to string
                numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
                df[numeric_columns] = df[numeric_columns].astype(str)

                all_columns = df.columns.tolist()

                children.append(dbc.Card([  # Wrap the content in a Card
                    dbc.CardHeader(html.H5(filename[i])),  # Display file name as card header
                    dbc.CardBody([  # Card body to hold the data table and other content
                        dash_table.DataTable(
                            df.to_dict('records'),
                            [{'name': i, 'id': i, 'selectable': True} for i in df.columns],
                            page_size=5,
                            filter_action='native',
                            column_selectable='single',
                            selected_columns=[df.columns[4]],
                            style_table={'overflowX': 'auto'},
                            style_cell={'color': 'black', 'fontFamily': 'Arial', 'fontSize': '14px'},  # Set text color
                            style_header={'backgroundColor': '#f7f7f9', 'fontWeight': 'bold', 'color': 'black'},  # Header style
                            style_data={'backgroundColor': '#ffffff', 'color': 'black'},  # Row data style
                            id={'type': 'dynamic-table', 'index': i},
                        ),
                        
                        # Dropdowns for x and y axis
                        html.Div([
                            html.Div([
                                html.Label('X-Axis:'),
                                dcc.Dropdown(
                                    id={'type': 'x-axis-dropdown', 'index': i},
                                    options=[{'label': col, 'value': col} for col in all_columns],
                                    value=all_columns[1],
                                    style={'color': 'black', 'backgroundColor': '#f7f7f7'}  # Set dropdown text color
                                )
                            ], style={'width': '48%', 'display': 'inline-block'}),

                            html.Div([
                                html.Label('Y-Axis:'),
                                dcc.Dropdown(
                                    id={'type': 'y-axis-dropdown', 'index': i},
                                    options=[{'label': col, 'value': col} for col in numeric_columns],
                                    value=numeric_columns[0] if numeric_columns else None,
                                    style={'color': 'black', 'backgroundColor': '#f7f7f7'}  # Set dropdown text color
                                )
                            ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
                        ], style={'padding': '10px'}),

                        # Multiple graph types (line, bar, bubble, etc.)
                        dbc.Row([
                            dbc.Col(dcc.Graph(id={'type': 'line-graph', 'index': i}, figure={}), width=12, lg=6, 
                                    style={
                                        'marginBottom': '20px',
                                        'marginTop': '10px',
                                        'borderRadius': '10px',  # Round the corners
                                        'backgroundColor': '#f7f7f7',  # Optional: Add background color for visibility
                                        'padding': '15px'  # Optional: Add padding for content spacing
                                        }),
                            dbc.Col(dcc.Graph(id={'type': 'bar-graph', 'index': i}, figure={}), width=12,  lg=6, 
                                    style={
                                        'marginBottom': '20px',
                                        'marginTop': '10px',
                                        'borderRadius': '10px',  # Round the corners
                                        'backgroundColor': '#f7f7f7',  # Optional: Add background color for visibility
                                        'padding': '15px'  # Optional: Add padding for content spacing
                                        }),
                            ]),
                        dbc.Row([
                            dbc.Col(dcc.Graph(id={'type': 'bubble-graph', 'index': i}, figure={}), width=12, lg=6,  
                                    style={
                                        'marginBottom': '20px',
                                        'marginTop': '10px',
                                        'borderRadius': '10px',  # Round the corners
                                        'backgroundColor': '#f7f7f7',  # Optional: Add background color for visibility
                                        'padding': '15px'  # Optional: Add padding for content spacing
                                        }),
                            dbc.Col(dcc.Graph(id={'type': 'doughnut-graph', 'index': i}, figure={}), width=12, lg=6,  
                                    style={
                                        'marginBottom': '20px',
                                        'marginTop': '10px',
                                        'borderRadius': '10px',  # Round the corners
                                        'backgroundColor': '#f7f7f7',  # Optional: Add background color for visibility
                                        'padding': '15px'  # Optional: Add padding for content spacing
                                        }),
                        ]),
                        dbc.Row([
                            dbc.Col(dcc.Graph(id={'type': 'radar-graph', 'index': i}, figure={}), width=12, lg=12, 
                                    style={
                                        'marginBottom': '20px',
                                        'marginTop': '10px',
                                        'borderRadius': '10px',  # Round the corners
                                        'backgroundColor': '#f7f7f7',  # Optional: Add background color for visibility
                                        'padding': '15px'  # Optional: Add padding for content spacing
                                        }),
                        ]),
                    ])
                ]))  # Close the Card

            except Exception as e:
                print(e)
                return html.Div([
                    'There was an error processing this file.'
                ])
        return children
    else:
        return ""



# Line Chart Callback
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
    df = df.sort_values(by=x_col, ascending=True) # sorted in ascending order
    fig = px.line(df, x=x_col, y=y_col,
                  title=f'Line Chart: {y_col} vs {x_col}',
                  hover_data={x_col: True, y_col: True})
    return fig


# Bar Chart Callback
@app.callback(
    Output({'type': 'bar-graph', 'index': MATCH}, 'figure'),
    [Input({'type': 'dynamic-table', 'index': MATCH}, 'derived_virtual_data'),
     Input({'type': 'x-axis-dropdown', 'index': MATCH}, 'value'),
     Input({'type': 'y-axis-dropdown', 'index': MATCH}, 'value')]
)
def create_bar_chart(filtered_data, x_col, y_col):
    if not filtered_data or not x_col or not y_col:
        return {}
    df = pd.DataFrame(filtered_data)
    # Ensure y_col is numeric
    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
    
    # Drop rows where y_col is NaN
    df = df.dropna(subset=[y_col])
    
    # Aggregate by x_col (Age) and sum y_col (Total Spend)
    df_aggregated = df.groupby(x_col).agg({y_col: 'sum'}).reset_index()

    # Sort the data based on x_col (Age)
    df_aggregated = df_aggregated.sort_values(by=x_col, ascending=True)

    custom_colors = ['#FF0000', '#0000FF', '#FFFF00', '#00FF00', '#800080', '#FFA500']

    fig = px.bar(df, x=x_col, y=y_col, 
                 title=f'Bar Chart: {y_col} by {x_col}', 
                 color=df.index % len(custom_colors),
                 color_discrete_map={i: custom_colors[i] for i in range(len(custom_colors))},
                 barmode="group", 
                 hover_data={x_col: True, y_col: True})
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col,
    )
    return fig


# Bubble Chart Callback
@app.callback(
    Output({'type': 'bubble-graph', 'index': MATCH}, 'figure'),
    [Input({'type': 'dynamic-table', 'index': MATCH}, 'derived_virtual_data'),
     Input({'type': 'x-axis-dropdown', 'index': MATCH}, 'value'),
     Input({'type': 'y-axis-dropdown', 'index': MATCH}, 'value')]
)
def create_bubble_chart(filtered_data, x_col, y_col):
    if not filtered_data or not x_col or not y_col:
        return {}

    df = pd.DataFrame(filtered_data)
    df = df.sort_values(by=x_col, ascending=True)
    
    size_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    size_col = size_cols[1] if len(size_cols) > 1 else y_col
    
    df[size_col] = pd.to_numeric(df[size_col], errors='coerce')
    df = df.dropna(subset=[size_col])
    
    max_size = df[size_col].max()
    sizeref = 1. * max_size / (60 ** 2)
    
    fig = px.scatter(df, x=x_col, y=y_col, size=size_col, color=size_col, 
                     color_continuous_scale='Viridis', title=f'Bubble Chart: {y_col} vs {x_col}', 
                     hover_data={size_col: True, x_col: True, y_col: True})
    fig.update_traces(
        marker=dict(
            sizemode = 'area',
            sizeref = sizeref,
            showscale = True,
        )
    )
    return fig


# Doughnut Chart Callback
@app.callback(
    Output({'type': 'doughnut-graph', 'index': MATCH}, 'figure'),
    [Input({'type': 'dynamic-table', 'index': MATCH}, 'derived_virtual_data'),
     Input({'type': 'x-axis-dropdown', 'index': MATCH}, 'value')]
)
def create_doughnut_chart(filtered_data, x_col):
    if not filtered_data or not x_col:
        return {}

    df = pd.DataFrame(filtered_data)
    df = df.sort_values(by=x_col, ascending=True)
    
    aggregated_data = df[x_col].value_counts()

    fig = go.Figure(data=[go.Pie(labels=aggregated_data.index,
                                 values=aggregated_data.values,
                                 hole=.3, 
                                 hoverinfo='label+percent+value',  # Show label, percentage, and value on hover
                                hovertemplate=(
                                    'Label: %{label}<br>'  # Label
                                    'Count: %{value}<br>'  # Count of items
                                    'Percentage: %{percent:.2f}%'  # Percentage representation
                                )
        )])
    fig.update_layout(title=f'Doughnut Chart: Distribution of {x_col}')
    return fig


# Radar Chart Callback
@app.callback(
    Output({'type': 'radar-graph', 'index': MATCH}, 'figure'),
    [Input({'type': 'dynamic-table', 'index': MATCH}, 'derived_virtual_data'),
     Input({'type': 'x-axis-dropdown', 'index': MATCH}, 'value'),
     Input({'type': 'y-axis-dropdown', 'index': MATCH}, 'value')]
)
def create_radar_chart(filtered_data, x_col, y_col):
    if not filtered_data or not x_col or not y_col:
        return {}

    df = pd.DataFrame(filtered_data)
    df = df.sort_values(by=x_col, ascending=True)
    
    fig = go.Figure(data=go.Scatterpolar(
        r=df[y_col],
        theta=df[x_col],
        fill='toself',
        hoverinfo='r+theta'
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True)
        ),
        title=f'Radar Chart: {y_col} vs {x_col}'
    )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
