import base64
import io

import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, dash_table, Input, Output, State, MATCH, ALL, no_update
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

# Initialize the app with the Solar theme
app = Dash(__name__, external_stylesheets=[dbc.themes.SOLAR], suppress_callback_exceptions=True)

# Define constants
PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

# Define the search bar
search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(type="search", placeholder="Search")),
        dbc.Col(
            dbc.Button(
                "Search", color="primary", className="ms-2", n_clicks=0
            ),
            width="auto",
        ),
    ],
    className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

# Define the navbar with the group logo and the search bar
navbar = dbc.Navbar(
    dbc.Container(
        [
            # Group Logo and Name
            dbc.Row(
                [
                    dbc.Col(html.Img(src='assets/logo.png', height="50px"), width="auto"),
                    dbc.Col(html.H3('GoReport!📈'), width="auto"),
                ],
                align="center",
                className="g-0",
            ),
            # Navbar toggler for responsive layout
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            # Collapse section for search bar
            dbc.Collapse(
                search_bar,
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
)

# Define the app layout
app.layout = html.Div([
    # Integrating Navbar into the layout
    navbar,

    # Main content container
    dbc.Container([
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
                multiple=False
            ), width=12)
        ], justify="center"),

        # Data table display area
        html.Div(id='data-table-container', children=[]),

        # Charts container with Add Chart button at the bottom
        html.Div(id='charts-container', children=[
            dbc.Row([
                dbc.Col(
                    dbc.Button("Add Chart", id="add-chart-btn", color="primary",
                               className="mt-3 mb-3", style={'display': 'none'}),
                    width={"size": 6, "offset": 5},
                    style={'textAlign': 'center'}
                )
            ])
        ])
    ], fluid=True),
])


# Callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


# Callback to handle file upload and display data
@app.callback(
    [Output('data-table-container', 'children'),
     Output('add-chart-btn', 'style')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def process_uploaded_file(contents, filename):
    if contents is None:
        return [], {'display': 'none'}

    # Decode the file
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    # Read the file
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename or 'xlsx' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return [html.Div("Unsupported file type")], {'display': 'none'}
        
        # Prepare data for display
        data_table = dbc.Card([
            dbc.CardHeader(f"Uploaded File: {filename}"),
            dbc.CardBody([
                dash_table.DataTable(
                    id='uploaded-data-table',
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=df.to_dict('records'),
                    page_size=10,
                    style_table={'overflowX': 'auto'},
                    filter_action='native',
                    sort_action='native'
                )
            ])
        ])

        # Return the data table and make the "Add Chart" button visible
        return [data_table], {'display': 'block'}

    except Exception as e:
        return [html.Div(f"Error processing file: {str(e)}")], {'display': 'none'}

@app.callback(
    [
        Output({'type': 'y-axis-dropdown', 'index': MATCH}, 'style'),
        Output({'type': 'y-axis-dropdown', 'index': MATCH, 'label': True}, 'style'),
        Output({'type': 'x-axis-dropdown', 'index': MATCH}, 'width'),
        Output({'type': 'chart-type-dropdown', 'index': MATCH}, 'width')
    ],
    Input({'type': 'chart-type-dropdown', 'index': MATCH}, 'value')
)
def adjust_layout(chart_type):
    if chart_type == 'pie':  # Pie chart does not use Y-Axis
        return (
            {'display': 'none'},  # Hide Y-axis dropdown
            {'display': 'none'},  # Hide Y-axis label
            6,  # Expand X-axis dropdown
            6   # Expand Chart Type dropdown
        )
    return (
        {'display': 'block'},  # Show Y-axis dropdown
        {'display': 'block'},  # Show Y-axis label
        4,  # Default width for X-axis dropdown
        4   # Default width for Chart Type dropdown
    )

# Callback to add a new chart
@app.callback(
    Output('charts-container', 'children'),
    Input('add-chart-btn', 'n_clicks'),
    State('upload-data', 'contents'),
    State('charts-container', 'children'),
    prevent_initial_call=True
)
def add_chart(n_clicks, contents, existing_charts):
    if contents is None:
        return existing_charts

    # Decode the file
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    # Read the file
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    # Determine numeric and non-numeric columns
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    non_numeric_columns = df.select_dtypes(exclude=['int64', 'float64']).columns.tolist()

    all_columns = df.columns.tolist()

    # Create a new chart configuration
    chart_id = sum(1 for child in existing_charts if isinstance(child, dict))  # Count existing charts

    new_chart = dbc.Card([
        dbc.CardHeader(f"Chart {chart_id }"),
        dbc.CardBody([
            dbc.Row([
                # Chart Type Dropdown
                dbc.Col([
                    html.Label("Chart Type"),
                    dcc.Dropdown(
                        id={'type': 'chart-type-dropdown', 'index': chart_id},
                        options=[
                            {'label': 'Line Chart', 'value': 'line'},
                            {'label': 'Bar Chart', 'value': 'bar'},
                            {'label': 'Bubble Chart', 'value': 'bubble'},
                            {'label': 'Pie Chart', 'value': 'pie'},
                            {'label': 'Radar Chart', 'value': 'radar'}
                        ],
                        value='line',
                        clearable=False
                    )
                ], id={'type': 'chart-type-col', 'index': chart_id}, width=4),

                # X-Axis Dropdown
                dbc.Col([
                    html.Label("X-Axis"),
                    dcc.Dropdown(
                        id={'type': 'x-axis-dropdown', 'index': chart_id},
                        options=[{'label': col, 'value': col} for col in all_columns],
                        value=non_numeric_columns[0] if non_numeric_columns else None,
                        clearable=False
                    )
                ], id={'type': 'x-axis-col', 'index': chart_id}, width=4),

                # Y-Axis Dropdown
                dbc.Col([
                    html.Label("Y-Axis", id={'type': 'y-axis-dropdown', 'index': chart_id, 'label': True},
                               style={'display': 'block'}),
                    dcc.Dropdown(
                        id={'type': 'y-axis-dropdown', 'index': chart_id},
                        options=[{'label': col, 'value': col} for col in all_columns],
                        value=numeric_columns[0] if numeric_columns else None,
                        clearable=False,
                        style={'display': 'block'}  # Default to visible
                    )
                ], width=4)
            ], className="mb-3"),

            # Graph container
            dcc.Graph(
                id={'type': 'chart-graph', 'index': chart_id},
                figure={}
            )
        ])
    ], className="mb-3 mt-3")

    # Append the new chart and ensure "Add Chart" button is the last child
    return existing_charts[:-1] + [new_chart, existing_charts[-1]]


# Callback to generate charts
@app.callback(
    Output({'type': 'chart-graph', 'index': MATCH}, 'figure'),
    [Input({'type': 'chart-type-dropdown', 'index': MATCH}, 'value'),
     Input({'type': 'x-axis-dropdown', 'index': MATCH}, 'value'),
     Input({'type': 'y-axis-dropdown', 'index': MATCH}, 'value')],
     Input('uploaded-data-table', 'derived_virtual_data')
)
def update_chart(chart_type, x_col, y_col, contents):
    if not contents:
        return {}

    df = pd.DataFrame(contents)

    custom_colors = ['#FF0000', '#0000FF', '#FFFF00', '#00FF00', '#800080', '#FFA500']

    # Generate chart based on type
    if chart_type == 'line':
        fig = px.line(df, x=x_col, y=y_col,
                      title=f'Line Chart: {y_col} vs {x_col}',
                      color_discrete_sequence=custom_colors,
                      hover_data={x_col: True, y_col: True})
    elif chart_type == 'bar':
        # Bar chart with custom colors
        fig = px.bar(df,
                     x=x_col,
                     y=y_col,
                     title=f'Bar Chart: {y_col} by {x_col}',
                     color=df.index % len(custom_colors),
                     color_discrete_map={i: custom_colors[i] for i in range(len(custom_colors))},
                     barmode="group",
                     hover_data={x_col: True, y_col: True})
    elif chart_type == 'bubble':
        # Ensure x-column is numeric and sorted
        try:
            df[x_col] = pd.to_numeric(df[x_col])
        except:
            df[x_col] = df[x_col].astype(str)

        df = df.sort_values(by=x_col, ascending=True)

        # Choose a size column
        size_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        size_col = size_cols[1] if len(size_cols) > 1 else y_col

        # Convert size column to numeric
        df[size_col] = pd.to_numeric(df[size_col], errors='coerce')
        df = df.dropna(subset=[size_col])

        # Calculate size reference for bubbles
        max_size = df[size_col].max()
        sizeref = 1. * max_size / (60 ** 2)

        fig = px.scatter(df, x=x_col, y=y_col, size=size_col,
                         color=df.index % len(custom_colors),
                         color_discrete_map={i: custom_colors[i] for i in range(len(custom_colors))},
                         title=f'Bubble Chart: {y_col} vs {x_col}',
                         hover_data={size_col: True, x_col: True, y_col: True})

        fig.update_traces(
            marker=dict(
                sizemode='area',
                sizeref=sizeref,
                showscale=True,
            )
        )
    elif chart_type == 'pie':
        # Aggregate data for doughnut chart
        aggregated_data = df[x_col].value_counts()

        fig = go.Figure(data=[go.Pie(
            labels=aggregated_data.index,
            values=aggregated_data.values,
            hole=.3,
            hoverinfo='label+percent+value',
            hovertemplate=(
                'Label: %{label}<br>'
                'Count: %{value}<br>'
                'Percentage: %{percent:.2f}%'
            ),
            marker=dict(colors=[custom_colors[i % len(custom_colors)] for i in range(len(aggregated_data))])
        )])

        fig.update_layout(title=f'Doughnut Chart: Distribution of {x_col}')
    elif chart_type == 'radar':
        print('test')
        # Radar chart logic
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
    else:
        return {}

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
