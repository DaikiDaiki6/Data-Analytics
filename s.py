from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import io
import base64

# Initialize the app with a Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])

# Placeholder for initial DataFrame
df = pd.DataFrame()

# App layout
app.layout = dbc.Container([
    dbc.Row([
        html.Div('Dynamic CSV Visualization App', className='text-primary text-center fs-3')
    ]),
    html.Hr(),
    dbc.Row([
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select a CSV File')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center'
            },
            multiple=False
        )
    ]),
    dbc.Row([
        html.Div(id='file-info', className='text-success mt-2')
    ]),
    dbc.Row([
        dcc.RadioItems(
            options=[
                {'label': 'Bubble Chart', 'value': 'bubble'},
                {'label': 'Bar Chart', 'value': 'bar'},
                {'label': 'Doughnut Chart', 'value': 'doughnut'},
                {'label': 'Polar Area Chart', 'value': 'polar'},
                {'label': 'Line Chart', 'value': 'line'}
            ],
            value='bubble',
            inline=True,
            id='radio-items-final'
        )
    ]),
    dbc.Row([
        dcc.Dropdown(id='x-axis', placeholder='Select X-axis'),
        dcc.Dropdown(id='y-axis', placeholder='Select Y-axis'),
        dcc.Dropdown(id='group-column', placeholder='Select Grouping Column (Optional for Bar Chart)', multi=False)
    ]),
    dash_table.DataTable(id='data-table', page_size=12, style_table={'overflowX': 'auto'}),
    dcc.Graph(id='my-first-graph-final', figure={})
], fluid=True)

# Callback for file upload
@callback(
    [Output('file-info', 'children'),
     Output('data-table', 'data'),
     Output('data-table', 'columns'),
     Output('x-axis', 'options'),
     Output('y-axis', 'options'),
     Output('group-column', 'options')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def parse_contents(contents, filename):
    if contents is None:
        return 'No file uploaded yet.', [], [], [], [], []
    
    # Parse the uploaded file
    content_type, content_string = contents.split(',')
    decoded = io.StringIO(base64.b64decode(content_string).decode('utf-8'))
    uploaded_df = pd.read_csv(decoded)
    
    # Generate options for dropdowns
    options = [{'label': col, 'value': col} for col in uploaded_df.columns]
    
    # Display data
    return (
        f"Uploaded File: {filename}",
        uploaded_df.to_dict('records'),
        [{'name': col, 'id': col} for col in uploaded_df.columns],
        options, options, options
    )


# Callback for updating the graph
@callback(
    Output('my-first-graph-final', 'figure'),
    [Input('radio-items-final', 'value'),
     Input('x-axis', 'value'),
     Input('y-axis', 'value'),
     Input('group-column', 'value')],
    [State('data-table', 'data')]
)
def update_graph(chart_type, x_axis, y_axis, group_column, table_data):
    if not table_data or not x_axis or not y_axis:
        return go.Figure().update_layout(title="Please upload a file and select appropriate columns.")

    # Convert table data to DataFrame
    df = pd.DataFrame(table_data)

    # Ensure Y-axis values are numeric
    df[y_axis] = pd.to_numeric(df[y_axis], errors='coerce')

    # Drop rows with NaN in the Y-axis
    df = df.dropna(subset=[y_axis])

    # Generate the appropriate chart
    if chart_type == 'doughnut' and group_column:
        fig = px.pie(df, names=group_column, title=f"Doughnut Chart: {group_column} Distribution", hole=0.3)
        fig.update_traces(hovertemplate='%{label}: %{percent:.2f}%')
    elif chart_type == 'bar':
        fig = px.bar(df, x=x_axis, y=y_axis, title=f"Bar Chart: {x_axis} vs {y_axis}")
        fig.update_traces(hovertemplate=f'{x_axis}: %{x}<br>{y_axis}: %{y}')
    elif chart_type == 'polar' and group_column:
        group_counts = df[group_column].value_counts()

        fig = go.Figure(go.Barpolar(
            r=group_counts.values,
            theta=[f'{g}' for g in group_counts.index],
            marker=dict(
                color=group_counts.values,
                colorscale='Rainbow',  # Use a better color scale
                line=dict(color='black', width=2)  # Add outline for better contrast
            ),
            text=group_counts.index,
            hoverinfo='text+r'
        ))

        fig.update_layout(
            title=f"Polar Area Chart: {group_column} Distribution",
            polar=dict(
                radialaxis=dict(visible=True, range=[0, group_counts.max()])
            ),
            showlegend=False,
            paper_bgcolor='rgb(240, 240, 240)',  # Light background
            plot_bgcolor='rgb(240, 240, 240)',  # Light plot background
            font=dict(family='Arial', size=14, color='black'),  # Readable font
            margin=dict(l=50, r=50, t=100, b=50)  # Add some padding for better layout
        )
        fig.update_traces(hovertemplate='Category: %{theta}<br>Value: %{r}')
    elif chart_type == 'line':
        # Sort data by the x-axis (Age) for line charts only
        df = df.sort_values(by=x_axis)
        
        # Check if a group column is selected
        if group_column:
            fig = px.line(df, x=x_axis, y=y_axis, color=group_column, title=f"Line Chart: {x_axis} vs {y_axis}",
                          line_shape='linear', template='plotly', markers=True)
            fig.update_traces(hovertemplate=f'{x_axis}: %{x}<br>{y_axis}: %{y}<br>{group_column}: %{text}')
        else:
            fig = px.line(df, x=x_axis, y=y_axis, title=f"Line Chart: {x_axis} vs {y_axis}",
                          line_shape='linear', template='plotly', markers=True)
            fig.update_traces(hovertemplate=f'{x_axis}: %{x}<br>{y_axis}: %{y}')
    elif chart_type == 'bubble':
        if group_column:
            # Ensure group_column has numeric data for sizing
            df[group_column] = pd.to_numeric(df[group_column], errors='coerce')
            df = df.dropna(subset=[group_column])  # Drop rows with invalid values
            
            # Calculate size reference for consistent scaling
            max_size = df[group_column].max()
            sizeref = 2.0 * max_size / (60 ** 2)  # Adjust maximum size (e.g., 60)

            # Create Bubble Chart using plotly.graph_objects
            fig = go.Figure(data=go.Scatter(
                x=df[x_axis],
                y=df[y_axis],
                mode='markers',
                marker=dict(
                    size=df[group_column],
                    sizemode='area',
                    sizeref=sizeref,
                    color=df[group_column],  # Heatmap-like coloring
                    colorscale='Viridis',
                    showscale=True  # Show color scale
                ),
                text=df[group_column],  # Optional: Add hover text
                hoverinfo='text+x+y'
            ))
            fig.update_layout(
                title=f"Bubble Chart: {x_axis} vs {y_axis} (Size: {group_column})",
                xaxis_title=x_axis,
                yaxis_title=y_axis,
                paper_bgcolor='rgb(243, 243, 243)',
                plot_bgcolor='rgb(243, 243, 243)',
            )
            fig.update_traces(hovertemplate=f'{x_axis}: %{x}<br>{y_axis}: %{y}<br>{group_column}: %{text}')
        else:
            fig = go.Figure().update_layout(
                title="Bubble Chart: Grouping Column Required for Bubble Size",
                xaxis_title=x_axis,
                yaxis_title=y_axis
            )
    else:
        fig = go.Figure().update_layout(title="Invalid chart type or insufficient data.")
    
    return fig





if __name__ == '__main__':
    app.run(debug=True)
