import base64
import io
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from fpdf import FPDF
import tempfile
import os

# Set page config
st.set_page_config(
    page_title="GoReport!",
    page_icon="📈",
    layout="wide",
)

# Initialize the session state attribute if not already initialized
if "filters_applied" not in st.session_state:
    st.session_state.filters_applied = False

# Navbar
st.markdown(
    """
    <style>
    .navbar {
        position: fixed;
        top: 0;
        width: 100%;
        background-color: #333;
        padding: 10px;
        z-index: 1000;
        color: white;
        font-family: "Poppins", sans-serif;
        font-size: 20px;
        text-align: center;
    }

    .sidebar-title {
        font-family: "Poppins", sans-serif;
        font-size: 25px;
        color: #333;
        background-color: #F2F2F2;
        padding: 10px;
        text-align: center;
        margin-bottom: 20px;
        border-radius: 10px;
        text-decoration : none;
    }

    .sidebar-header {
        font-family: "Poppins", sans-serif;
        font-size: 40px;  /* Increased font size for better visibility */
        color: #4a78c3;  /* Lighter blue color */
        font-weight: bold;
        text-align: center;
        margin-top: 10px;  /* Reduced top margin */
        margin-bottom: 20px;  /* Adjusted bottom margin */
    }
    
    .sidebar-header a {
                    text-decoration: none; /* Removes underline */
                    color: #4a78c3; /* Keep the color consistent with your header */
                }
                .sidebar-header a:hover {
                    color: #333; /* Optional: Change color on hover */
                }
    
    </style>
    <div class="navbar">GoReport📈</div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br><br>", unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader("Drag and Drop or Select CSV/XLS Files", type=["csv", "xls", "xlsx"])
if uploaded_file:
    try:
        # Read file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type!")
            st.stop()
        
        st.success(f"Uploaded {uploaded_file.name} successfully!")

        # Initialize filtered_df here, to be used later
        filtered_df = df.copy()

        # Sidebar with custom title and Universal Filters and Chart Management
        with st.sidebar:
            # Sidebar Title "GoReport!📈"
            st.markdown('<div class="sidebar-header"><a href="/">GoReport!📈</a></div>', unsafe_allow_html=True)

            # Chart Management Section
            st.sidebar.title("Chart Management")
            add_chart = st.sidebar.button("Add Chart")
            
            # Initialize the chart list
            charts = st.session_state.get("charts", [])

            if len(charts) > 0:
                chart_ids = [f"Chart {chart['id']}" for chart in charts]
                chart_to_delete = st.selectbox("Delete Chart", chart_ids, index=0)
                delete_chart = st.button("Delete Selected Chart")
                
                if delete_chart:
                    selected_chart_id = int(chart_to_delete.split(" ")[1])
                    charts = [chart for chart in charts if chart["id"] != selected_chart_id]
                    
                    # Re-index the remaining charts
                    for i, chart in enumerate(charts):
                        chart["id"] = i + 1
                    st.session_state["charts"] = charts
                    st.success(f"Chart {selected_chart_id} deleted successfully!")

            if add_chart:
                # Ensure DataFrame is not empty
                if filtered_df.empty:
                    st.error("The uploaded file is empty!")
                    st.stop()

                # Set initial values for x_col and y_col
                initial_x_col = filtered_df.columns[0] if filtered_df.shape[1] > 0 else None
                initial_y_col = filtered_df.columns[1] if filtered_df.shape[1] > 1 else None

                charts.append({
                    "id": len(charts) + 1,
                    "x_col": initial_x_col,
                    "y_col": initial_y_col,
                    "chart_type": "line"
                })
                st.session_state["charts"] = charts

            # Dashboard Management Section
            st.title("Dashboard Management")

            # Universal Filters
            with st.expander("Universal Filters", expanded=False):
                for column in df.columns:
                    filter_column = False

                    # Check if the column is boolean
                    if pd.api.types.is_bool_dtype(df[column]):
                        selected_value = st.selectbox(f"Filter {column}", options=[True, False], index=0)
                        if selected_value != df[column].iloc[0]:
                            filter_column = True
                        if filter_column:
                            filtered_df = filtered_df[filtered_df[column] == selected_value]

                    elif pd.api.types.is_numeric_dtype(df[column]):
                        min_value = df[column].min()
                        max_value = df[column].max()
                        selected_range = st.slider(
                            f"Filter {column} by range", min_value=min_value, max_value=max_value,
                            value=(min_value, max_value)
                        )
                        if selected_range != (min_value, max_value):
                            filter_column = True
                        if filter_column:
                            filtered_df = filtered_df[(filtered_df[column] >= selected_range[0]) & (filtered_df[column] <= selected_range[1])]
                    
                    else:
                        unique_values = df[column].dropna().unique()
                        selected_values = st.multiselect(f"Filter {column} by", options=unique_values, default=unique_values)
                        if set(selected_values) != set(unique_values):
                            filter_column = True
                        if filter_column:
                            filtered_df = filtered_df[filtered_df[column].isin(selected_values)]

                    # Track filter application
                    if filter_column:
                        st.session_state.filters_applied = True

                    # Check if filtering results in an empty DataFrame
                    if filtered_df.empty:
                        st.error("No data available after applying the filters.")
                        st.stop()  # Stop processing if the DataFrame is empty

        # Reset the filtered_df if no filters are applied
        if not st.session_state.filters_applied:
            filtered_df = df.copy()



        def get_chart_interpretation(chart, filtered_df):
            interpretation = ""

            # Line Chart Interpretation
            if chart["chart_type"] == "line":
                interpretation = f"The line chart shows the trend of {chart['y_col']} over {chart['x_col']}. " \
                                "It helps in understanding the relationship and changes over time or categories. "
                max_value = filtered_df[chart['y_col']].max()
                min_value = filtered_df[chart['y_col']].min()
                interpretation += f"The highest value of {chart['y_col']} is {max_value}, and the lowest value is {min_value}. "

            # Bar Chart Interpretation
            elif chart["chart_type"] == "bar":
                interpretation = f"The bar chart compares the {chart['y_col']} across different categories of {chart['x_col']}. " \
                                "This helps identify the category with the highest or lowest values."
                max_category = filtered_df[chart['y_col']].idxmax()
                min_category = filtered_df[chart['y_col']].idxmin()
                max_value = filtered_df[chart['y_col']].max()
                min_value = filtered_df[chart['y_col']].min()
                interpretation += f"The highest value of {chart['y_col']} is {max_value} in the category {max_category}, " \
                                f"and the lowest value is {min_value} in the category {min_category}. "

            # Pie Chart Interpretation
            elif chart["chart_type"] == "pie":
                interpretation = f"The pie chart shows the proportion of {chart['x_col']} values. " \
                                "Each slice represents the contribution of each category to the whole."
                largest_slice = filtered_df[chart['x_col']].value_counts().idxmax()
                interpretation += f"The largest slice of the pie is from the category '{largest_slice}', " \
                                f"indicating it has the most significant proportion of the total."

            # Bubble Chart Interpretation
            elif chart["chart_type"] == "bubble":
                interpretation = f"The bubble chart shows the relationship between {chart['x_col']} and {chart['y_col']}, " \
                        
                interpretation += f"The largest bubble, indicating the highest 'Total Spend', has a value of , " \
                                f"while the smallest bubble has a 'Total Spend' of . "

            # Radar Chart Interpretation
            elif chart["chart_type"] == "radar":
                interpretation = f"The radar chart represents the distribution of {chart['y_col']} across different categories of {chart['x_col']}. " \
                                "The chart's radial axis shows the relative size of each category."
                largest_value = filtered_df[chart['y_col']].max()
                largest_category = filtered_df[chart['y_col']].idxmax()
                interpretation += f"The category with the largest value of {chart['y_col']} is {largest_category}, " \
                                f"with a value of {largest_value}. "

            return interpretation

        # Create a PDF file with charts
        def create_pdf(charts, filtered_df):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Ensure the 'temp' directory exists
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)

            # Cover Page
            pdf.add_page()
            pdf.set_font("Times", style="B", size=28)
            pdf.cell(0, 20, txt="GoReport!".encode('latin-1', 'replace').decode('latin-1'), ln=True, align="C")
            pdf.ln(20)

            pdf.set_font("Times", size=16)
            pdf.cell(0, 10, txt="by:", ln=True, align="C")
            pdf.ln(10)

            authors = [
                "Daquigan, Jeffrey M.",
                "Dyogi, Sean Timothy Archer M.",
                "Fajardo, Sealtiel P.",
                "Marbella, Gorel Kaiser G.",
                "Molon, Miriam Juliene F."
            ]

            pdf.set_font("Times", size=14)
            for author in sorted(authors):
                pdf.cell(0, 10, txt=author, ln=True, align="C")
            pdf.ln(20)

            pdf.set_font("Times", style="B", size=16)
            pdf.cell(0, 10, txt="CS Elective 3 - Data Analytics", ln=True, align="C")
            pdf.cell(0, 10, txt="Data Visualization/Analytics Web Application", ln=True, align="C")
            pdf.ln(10)

            pdf.set_font("Times", size=14)
            pdf.cell(0, 10, txt="BSCS 4-1 2024", ln=True, align="C")
            pdf.ln(30)

            # Generate charts and include interpretation
            for chart in charts:
                fig = None
                interpretation = get_chart_interpretation(chart, filtered_df)

                if chart["chart_type"] == "line":
                    fig = px.line(filtered_df, x=chart["x_col"], y=chart["y_col"])
                elif chart["chart_type"] == "bar":
                    fig = px.bar(filtered_df, x=chart["x_col"], y=chart["y_col"], color=chart["x_col"])
                elif chart["chart_type"] == "pie":
                    fig = px.pie(filtered_df, names=chart["x_col"], hole=0.3)
                elif chart["chart_type"] == "bubble":
                    if pd.api.types.is_numeric_dtype(filtered_df[chart["x_col"]]) and pd.api.types.is_numeric_dtype(filtered_df[chart["y_col"]]):
                        fig = px.scatter(filtered_df, x=chart["x_col"], y=chart["y_col"], size=2, color="Membership Type", size_max=60)

                # Save chart to temp folder
                if fig:
                    pdf.add_page()
                    pdf.set_font("Times", size=12)
                    pdf.cell(200, 10, txt=f"Chart {chart['id']}: {chart['chart_type']}", ln=True)
                    pdf.ln(10)
                    pdf.set_font("Times", size=10)
                    pdf.multi_cell(0, 10, txt=f"{interpretation}", align="L")
                    pdf.ln(10)

                    chart_path = os.path.join(temp_dir, f"chart_{chart['id']}.png")
                    fig.write_image(chart_path)
                    pdf.image(chart_path, x=10, y=pdf.get_y(), w=180)
                    pdf.ln(100)

            # Output PDF to buffer
            buf = io.BytesIO()
            pdf.output(dest="S").encode("latin1")
            buf.write(pdf.output(dest="S").encode("latin1"))
            buf.seek(0)

            return buf.getvalue()

        
        # Make the table hideable using an expander
        with st.expander("Table Data", expanded=True):
            st.dataframe(filtered_df)
            
        # Display Charts
        for chart in charts:
            st.subheader(f"Chart {chart['id']}")

            cols = list(filtered_df.columns)
            chart["chart_type"] = st.selectbox(
                "Chart Type",
                ["line", "bar", "pie", "bubble", "radar"],
                key=f"chart_type_{chart['id']}",
                index=["line", "bar", "pie", "bubble", "radar"].index(chart.get("chart_type", "line")),
            )
            chart["x_col"] = st.selectbox(
                "X-Axis",
                cols,
                key=f"x_col_{chart['id']}",
                index=cols.index(chart.get("x_col", cols[0])) if chart.get("x_col") in cols else 0,
            )
            chart["y_col"] = st.selectbox(
                "Y-Axis",
                cols,
                key=f"y_col_{chart['id']}",
                index=cols.index(chart.get("y_col", cols[1] if len(cols) > 1 else cols[0])) if chart.get("y_col") in cols else 1,
            ) if chart["chart_type"] != "pie" else None

            # Generate chart
            fig = None
            if chart["chart_type"] == "line":
                fig = px.line(filtered_df, x=chart["x_col"], y=chart["y_col"])
            elif chart["chart_type"] == "bar":
                fig = px.bar(filtered_df, x=chart["x_col"], y=chart["y_col"], color=chart["x_col"])
            elif chart["chart_type"] == "pie":
                fig = px.pie(filtered_df, names=chart["x_col"], hole=0.3)
            elif chart["chart_type"] == "bubble":
                # Prefer numeric columns for size
                numeric_columns = filtered_df.select_dtypes(include=['float64', 'int64']).columns.tolist()

                # Try to find a suitable size column
                size_column = None
                preferred_size_columns = ["Total spend", "Items purchased", "Age"]

                for col in preferred_size_columns:
                    if col in numeric_columns:
                        size_column = col
                        break

                # If no preferred column, use the first numeric column
                if size_column is None and numeric_columns:
                    size_column = numeric_columns[0]

                # If both x and y are numeric columns
                if pd.api.types.is_numeric_dtype(filtered_df[chart["x_col"]]) and \
                        pd.api.types.is_numeric_dtype(filtered_df[chart["y_col"]]):

                    if size_column:
                        fig = px.scatter(filtered_df,
                                         x=chart["x_col"],
                                         y=chart["y_col"],
                                         size=size_column,  # Use a valid column name
                                         color="Membership type" if "Membership type" in filtered_df.columns else filtered_df.columns[0],
                                         size_max=60,
                                         title=f"Bubble Chart: {chart['x_col']} vs {chart['y_col']}")
                    else:
                        # Fallback if no numeric size column found
                        fig = px.scatter(filtered_df,
                                         x=chart["x_col"],
                                         y=chart["y_col"],
                                         color="Membership type" if "Membership type" in filtered_df.columns else filtered_df.columns[0],
                                         title=f"Scatter Plot: {chart['x_col']} vs {chart['y_col']}")
                else:
                    st.error("For the bubble chart, both X and Y axes must be numeric.")
            if chart["chart_type"] == "radar":
                if pd.api.types.is_numeric_dtype(filtered_df[chart["y_col"]]):
                    fig = go.Figure(data=go.Scatterpolar(
                        r=filtered_df[chart["y_col"]],
                        theta=filtered_df[chart["x_col"]],
                        fill='toself',
                        line=dict(color='blue', width=2),  # Thicker line for better visibility
                        mode='markers+lines',  # Added lines connecting the points
                        marker=dict(size=8, color='red'),  # Red marker for better contrast
                        text=filtered_df[chart["x_col"]],
                        textposition='middle center',  # Positioning text labels at the top of the points
                    ))
                    fig.update_layout(
                        polar=dict(
                            angularaxis=dict(
                                tickangle=45,  # Rotate axis labels for better readability
                                tickmode="array",  # Specify tick values for categories
                                tickvals=filtered_df[chart["x_col"]],  # Set tick values to the categories
                                ticks="outside",  # Positioning ticks outside the chart
                            ),
                            radialaxis=dict(
                                visible=True,
                                range=[0, max(filtered_df[chart["y_col"]])],  # Range based on data max value
                                showticklabels=True,  # Show labels on the radial axis
                                tickfont=dict(size=10),  # Size of the radial axis tick labels
                            ),
                        ),
                        title=f"Radar Chart: {chart['y_col']} vs {chart['x_col']}",
                        showlegend=False,
                        width=800,  # Increased chart width for better layout
                        height=800,  # Increased chart height for better clarity
                        plot_bgcolor="white",  # Set background color to white
                        margin=dict(t=50, b=50, l=50, r=50),  # Adjust margin to fit labels
                    )
                else:
                        st.error("For the bubble chart, Y axis must be numeric.")

            # Display chart
            if fig:
                st.plotly_chart(fig, key=f"plotly_chart_{chart['id']}")

        # PDF download button
        if st.button("Generate PDF"):
            pdf_bytes = create_pdf(charts, filtered_df)  # Ensure this returns bytes, not a BytesIO object
            st.session_state["pdf_bytes"] = pdf_bytes  # Store the PDF bytes in session state

        # Check if the PDF has been generated and offer a download button
        if "pdf_bytes" in st.session_state:
            st.download_button(
                label="Download PDF",
                data=st.session_state["pdf_bytes"],
                file_name="GoReport-Report.pdf",
                mime="application/pdf"
            )


    except Exception as e:
        st.error(f"Error: {e}")
