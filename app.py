from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # Ensure this is imported
import dash_bootstrap_components as dbc

# Load data
df = pd.read_csv('E-commerce-Customer-Behavior-Sheet1.csv')


# Convert columns to numeric, coercing errors to NaN
df['Total Spend'] = pd.to_numeric(df['Total Spend'], errors='coerce')
df['Items Purchased'] = pd.to_numeric(df['Items Purchased'], errors='coerce')

# Map Satisfaction Level to numeric values: Satisfied -> 3, Neutral -> 2, Unsatisfied -> 1
satisfaction_mapping = {'Satisfied': 3, 'Neutral': 2, 'Unsatisfied': 1}
df['Satisfaction Level'] = df['Satisfaction Level'].map(satisfaction_mapping)

# Debug: Print the DataFrame after mapping Satisfaction Level
print("Cleaned Data with Mapped Satisfaction Level:")
print(df.head())

# Drop rows with NaN values in relevant columns
df = df.dropna(subset=['Total Spend', 'Items Purchased', 'Satisfaction Level'])

# Debug: Print the DataFrame after dropping NaN rows
print("Data After Dropping NaN Rows:")
print(df.head())

# Initialize the app with a Bootstrap theme
a = [dbc.themes.CERULEAN]
app = Dash(__name__, external_stylesheets=a)

# Layout of the app
app.layout = dbc.Container([
    dbc.Row([
        html.Div('My First App with Data, Graph, and Controls', className='text-primary text-center fs-3')
    ]),
    html.Hr(),
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
        ),
    ]),
    dash_table.DataTable(data=df.to_dict('records'), page_size=12, style_table={'overflowX': 'auto'}),
    dcc.Graph(figure={}, id='my-first-graph-final')
], fluid=True)

# Callback function to update the graph based on selected chart type
@callback(
    Output(component_id='my-first-graph-final', component_property='figure'),
    Input(component_id='radio-items-final', component_property='value')
)
def update_graph(chart_type):
    if chart_type == 'doughnut':
        # Doughnut Chart: Membership Type (count of customers)
        fig = px.pie(df, names='Membership Type', title="Doughnut Chart: Membership Type Distribution", hole=0.3)
    elif chart_type == 'bar':
        # Bar Chart: Membership Type vs. Total Spend
        fig = px.bar(df, x='Membership Type', y='Total Spend', title="Bar Chart: Membership Type vs. Total Spend")
    elif chart_type == 'polar':
        # Polar Area Chart: Gender distribution (count of occurrences)
        gender_counts = df['Gender'].value_counts()

        fig = go.Figure(go.Barpolar(
            r=gender_counts.values,  # Values for the radius (size of the slices)
            theta=gender_counts.index,  # Categories (e.g., Male, Female)
            width=[20] * len(gender_counts),  # Width of each slice (adjust as needed)
            marker=dict(color=gender_counts.values, colorscale='Blues'),  # Color based on values
            text=gender_counts.index,  # Add text labels inside the slices
            hoverinfo='text+r',  # Show both the text and the radius value on hover
        ))

        fig.update_layout(
            title="Polar Area Chart: Gender Distribution",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, gender_counts.max()]  # Scale the radius based on max count
                ),
                angularaxis=dict(showline=False)  # Hide the lines between the slices
            ),
            showlegend=False
        )
    elif chart_type == 'line':
        # Line Chart: Days Since Last Purchase vs. Age
        fig = px.line(df, x='Days Since Last Purchase', y='Age', title="Line Chart: Days Since Last Purchase vs. Age")
    else:
        # Default case: If no chart type matches, create a simple empty chart or fallback
        fig = {}

    return fig

if __name__ == '__main__':
    app.run(debug=True)
