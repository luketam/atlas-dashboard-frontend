import dash
from dash import dcc, html, ctx
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Required for deployment

app.index_string = '''
<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Berkshire+Swash&family=Lato:wght@300;400;700&family=Arvo:wght@400;700&display=swap" rel="stylesheet">
</head>
<body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
'''

# API Base URL
API_BASE_URL = "https://atlas-dashboard-backend.onrender.com/api/"

# Function to fetch and clean data from API
def fetch_data(endpoint):
    response = requests.get(f"{API_BASE_URL}{endpoint}")
    if response.status_code == 200:
        df = pd.DataFrame(response.json()).replace("", pd.NA)  # Replace empty strings with NaN
        return df
    return pd.DataFrame()

# Load initial datasets
unit_parameters, sun_data, unit_measurements, plant_growth, plant_harvest = (
    fetch_data(endpoint) for endpoint in
    ["unit-parameters", "sun-data", "unit-measurements", "plant-growth", "plant-harvest"]
)

# Ensure "Plant" column exists in both datasets
plant_growth["Plant"] = plant_growth["Level"].astype(str) + "-" + plant_growth["Side"].astype(str)
plant_harvest["Plant"] = plant_harvest["Level"].astype(str) + "-" + plant_harvest["Side"].astype(str)  # Fix applied here

# Convert "Hours of Daylight" from HH:MM:SS to decimal hours
if "Hours of Daylight" in sun_data.columns:
    sun_data["Hours of Daylight"] = pd.to_timedelta(sun_data["Hours of Daylight"]).dt.total_seconds() / 3600

# Clean unit measurements dataset by removing rows with missing key values
unit_measurements_chart = unit_measurements.dropna(subset=["Depth", "pH", "EC", "PPM", "Temperature"])

# Aggregate plant growth data by date
plant_growth["Date"] = pd.to_datetime(plant_growth["Date"], errors="coerce")  # Convert to datetime
numeric_columns = plant_growth.select_dtypes(include=["int64", "float64"]).columns
plant_growth_summary = plant_growth.groupby("Date")[numeric_columns].mean().reset_index()

# Function to create an individual info card with updated fonts
def create_info_card(icon, title, value, bg_color):
    """Generates a styled card with Arvo for the title and Lato for the data."""
    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col(DashIconify(icon=icon, width=55, height=55, color="white"), width="auto",
                        style={"display": "flex", "alignItems": "center", "justifyContent": "center"}),

                dbc.Col(html.H4(title, className="text-white",
                                style={"fontSize": "22px", "fontWeight": "bold",
                                       "fontFamily": "Arvo", "textAlign": "center"}),
                        width=True, style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
            ], align="center", className="mb-3"),

            html.H3(value, className="text-white",
                    style={"fontSize": "26px", "fontWeight": "bold",
                           "fontFamily": "Lato", "textAlign": "center"})
        ]),

        style={"backgroundColor": bg_color, "padding": "25px", "borderRadius": "12px",
               "boxShadow": "0px 4px 10px rgba(255, 255, 255, 0.2)", "margin": "10px",
               "textAlign": "center"}
    )

# Extract values from unit_parameters DataFrame
unit_id = unit_parameters["Unit ID"].iloc[0]
plant_type = unit_parameters["Plant Type 1"].iloc[0]
plant_count = unit_parameters["Plant Count 1"].iloc[0]
medium = unit_parameters["Medium"].iloc[0]

# Nutrients
n_value = unit_parameters["N"].iloc[0]
p_value = unit_parameters["P"].iloc[0]
k_value = unit_parameters["K"].iloc[0]

# Light & Uptime
artificial_light = unit_parameters["Artificial Light (Hours)"].iloc[0]
uptime = unit_parameters["Uptime (Hours)"].iloc[0]
downtime = unit_parameters["Downtime (Hours)"].iloc[0]

# Watering Schedule
watering_duration_uptime = unit_parameters["Watering Duration Uptime (Minutes)"].iloc[0]
watering_interval_uptime = unit_parameters["Watering Interval Uptime (Minutes)"].iloc[0]
watering_duration_downtime = unit_parameters["Watering Duration Downtime (Minutes)"].iloc[0]
watering_interval_downtime = unit_parameters["Watering Interval Downtime (Minutes)"].iloc[0]

# Function to create styled line charts with enhanced customization
def create_chart(df, x_col, y_col, title, y_label, description, show_avg=True):
    fig = px.line(df, x=x_col, y=y_col, template="plotly_dark", labels={y_col: y_label})

    if show_avg:
        avg_value = df[y_col].mean()
        fig.add_trace(go.Scatter(x=df[x_col], y=[avg_value] * len(df), mode="lines",
                                 name="Average", line=dict(dash="dash", color="red")))

    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        font_family="Lato",  # Modern font for consistency
        title_font_family="Arvo",  # Different modern font for titles
        font_color="white",
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        xaxis=dict(title=x_col, tickangle=-45),  # Improve X-axis readability
    )

    return html.Div([
        html.H3(title, style={"textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"}),
        html.P(description, style={"textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"}),
        dcc.Graph(figure=fig)
    ])

# Create environmental condition charts with improved descriptions
depth_chart = create_chart(unit_measurements_chart, "Timestamp", "Depth",
                           "Water Depth Over Time", "Water Depth (Inches)",
                           "This chart monitors changes in water depth within the hydroponic system. "
                           "A consistent water level is crucial for optimal plant growth and nutrient absorption.")

ph_chart = create_chart(unit_measurements_chart, "Timestamp", "pH",
                        "pH Levels Over Time", "pH Level",
                        "pH levels affect nutrient availability and plant health. "
                        "Maintaining a stable pH ensures plants receive the right balance of nutrients.")

ec_chart = create_chart(unit_measurements_chart, "Timestamp", "EC",
                        "Electrical Conductivity (EC) Over Time", "EC (mS/cm)",
                        "Electrical Conductivity (EC) reflects the concentration of nutrients in the water. "
                        "Stable EC levels indicate balanced nutrient delivery.")

ppm_chart = create_chart(unit_measurements_chart, "Timestamp", "PPM",
                         "Parts Per Million (PPM) Over Time", "Nutrient Concentration (PPM)",
                         "PPM values represent the total dissolved solids in the system. "
                         "Monitoring PPM helps ensure plants are getting the correct nutrient strength.")

temperature_chart = create_chart(unit_measurements_chart, "Timestamp", "Temperature",
                                 "Temperature Over Time", "Temperature (Degrees Fahrenheit)",
                                 "Temperature fluctuations can impact plant metabolism. "
                                 "Maintaining an optimal range supports strong growth and photosynthesis.")

# Create Sunlight Chart with Average Line and Adjusted X-Axis Intervals
def create_sunlight_chart(df, x_col, y_col, title, y_label, description):
    fig = px.line(df, x=x_col, y=y_col, template="plotly_dark", labels={y_col: y_label})

    # Compute and add average sunlight line
    avg_value = df[y_col].mean()
    fig.add_trace(go.Scatter(x=df[x_col], y=[avg_value] * len(df), mode="lines",
                             name="Average", line=dict(dash="dash", color="red")))

    # Adjust X-axis to show fewer tick intervals
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        font_family="Lato",
        title_font_family="Arvo",
        font_color="white",
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        xaxis=dict(
            tickmode="array",
            tickvals=df[x_col][::len(df) // 5],  # Show only 5 evenly spaced date intervals
            tickangle=-45,
            title="Date"
        )
    )

    return html.Div([
        html.H3(title, style={"textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"}),
        html.P(description, style={"textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"}),
        dcc.Graph(figure=fig)
    ])

# Define the Sunlight Chart using the updated function
sunlight_chart = create_sunlight_chart(
    sun_data, "Date", "Hours of Daylight",
    "Sunlight Hours Over Time", "Hours of Sunlight",
    "This chart tracks daily sunlight exposure, which is essential for plant photosynthesis. "
    "Ensuring optimal sunlight duration promotes healthy plant growth."
)

# Function to create a styled box plot
def create_box_plot(df, y_col, title, y_label, description):
    """Generates a box plot with a dark theme and formatted labels."""
    fig = px.box(df, y=y_col, boxmode="overlay", labels={y_col: y_label}, template="plotly_dark")
    fig.update_layout(
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        font_color="white",
        title_font_family="Arvo",
        font_family="Lato",
        showlegend=False
    )

    return html.Div([
        html.H3(title, style={"textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"}),
        html.P(description, style={"textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"}),
        dcc.Graph(figure=fig)
    ])

# Harvest Yield Distribution Box Plot
yield_chart = create_box_plot(
    plant_harvest, "Yield (Grams)", "Distribution of Harvest Yield (Grams)",
    "Harvest Yield (Grams)",
    "This box plot visualizes the distribution of harvest yields among individual plants. "
    "It helps assess variability in yield and detect any outliers."
)

# Root Length Distribution Box Plot
roots_chart = create_box_plot(
    plant_harvest, "Roots (Millimeters)", "Distribution of Root Length (Millimeters)",
    "Root Length (mm)",
    "This box plot illustrates the variation in root lengths across all harvested plants. "
    "Monitoring root growth is crucial for assessing plant health and nutrient uptake efficiency."
)

# Brix Score Distribution Box Plot
brix_chart = create_box_plot(
    plant_harvest, "Brix", "Distribution of Brix Score",
    "Brix Score (Sugar Content)",
    "This box plot represents the distribution of sugar content (Brix Score) in harvested plants. "
    "Higher Brix values generally indicate better fruit quality and flavor."
)

# Aggregate "Brix Line" counts for the pie chart
brix_line_counts = plant_harvest["Brix Line"].value_counts().reset_index()
brix_line_counts.columns = ["Brix Line", "Count"]

# Define a dark custom color palette with exactly 6 colors
dark_colors = ["#7B241C", "#A04000", "#196F3D", "#154360", "#512E5F", "#4D2C19"]

# Create Pie Chart with dark colors
brix_pie_chart = px.pie(
    brix_line_counts, names="Brix Line", values="Count",
    template="plotly_dark",
    color_discrete_sequence=dark_colors  # Apply custom dark colors
)

# Update layout for readability
brix_pie_chart.update_layout(
    paper_bgcolor="#1e1e1e",
    font_color="white",
    title_font_family="Arvo",
    font_family="Lato",
    showlegend=False  # Remove legend since labels are already displayed
)

# Ensure pie slice labels are white for better contrast
brix_pie_chart.update_traces(
    textinfo="percent+label",
    textfont=dict(color="white")
)

brix_pie_chart_div = html.Div([
    html.H3("Brix Line Composition", style={"textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"}),
    html.P("This pie chart displays the distribution of Brix Line values, representing variations in sugar content among harvested plants and highlighting overall sweetness trends. ",
           style={"textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"}),
    dcc.Graph(figure=brix_pie_chart)
])

# Extend plant growth with arbitrary projections and fluctuations
def extend_growth_data(df, column, days=10, growth_rate=1.02, noise_factor=0.03):
    """Generates fluctuating projected values for the specified column."""
    last_value = df[column].iloc[-1]
    future_dates = pd.date_range(df["Date"].max() + pd.Timedelta(days=1), periods=days)

    projections = []
    for _ in range(days):
        fluctuation = np.random.uniform(-noise_factor, noise_factor)
        last_value *= (growth_rate + fluctuation)
        projections.append(last_value)

    return pd.DataFrame({"Date": future_dates, column: projections})

# Generate projections
height_projection_df = extend_growth_data(plant_growth_summary, "Height (Inches)")
width_projection_df = extend_growth_data(plant_growth_summary, "Width (Inches)")
leaf_projection_df = extend_growth_data(plant_growth_summary, "Leaf (Inches)")

# Line chart with projections
def create_projection_chart(df_actual, df_proj, x_col, y_col, title, y_label, description):
    """Creates a line chart with actual and projected values."""
    df_proj = pd.concat([df_actual.tail(1), df_proj], ignore_index=True)

    fig = px.line(df_actual, x=x_col, y=y_col, template="plotly_dark", labels={y_col: y_label})
    fig.add_trace(go.Scatter(x=df_proj[x_col], y=df_proj[y_col],
                             mode="lines", name="Forecast",
                             line=dict(dash="dot", color="red")))

    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        font_family="Lato",
        title_font_family="Arvo",
        font_color="white",
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        showlegend=True
    )

    return html.Div([
        html.H3(title, style={"textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"}),
        html.P(description, style={"textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"}),
        dcc.Graph(figure=fig)
    ])

# Heatmap generator
def create_heatmap(df, x_col, y_col, z_col, title, description):
    """Creates a heatmap using raw (non-aggregated) values."""
    df = df.dropna(subset=[z_col])
    pivot = df.pivot(index=y_col, columns=x_col, values=z_col)

    fig = px.imshow(
        pivot, color_continuous_scale="blues",
        labels={"color": z_col}, aspect="auto", template="plotly_dark"
    )

    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        font_family="Lato",
        title_font_family="Arvo",
        font_color="white",
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e"
    )

    return html.Div([
        html.H3(title, style={"textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"}),
        html.P(description, style={"textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"}),
        dcc.Graph(figure=fig)
    ])

# Generate line charts with projections
height_chart = create_projection_chart(
    plant_growth_summary, height_projection_df, "Date", "Height (Inches)",
    "Average Plant Height", "Plant Height (Inches)",
    "This chart illustrates the average plant height over time, including a forecasted extension to help visualize future growth trends."
)

width_chart = create_projection_chart(
    plant_growth_summary, width_projection_df, "Date", "Width (Inches)",
    "Average Plant Width", "Plant Width (Inches)",
    "This chart displays the average plant width progression, followed by a short-term projection to anticipate lateral growth patterns."
)

leaf_chart = create_projection_chart(
    plant_growth_summary, leaf_projection_df, "Date", "Leaf (Inches)",
    "Average Largest Leaf Size", "Largest Leaf Size (Inches)",
    "This chart tracks the average size of the largest leaf per plant, with a projected trendline indicating potential size increase over the next several days."
)

# Generate heatmaps
height_heatmap = create_heatmap(plant_growth, "Date", "Plant", "Height (Inches)",
                                "Plant Height Heatmap",
                                "This heatmap highlights unit-level variations in average plant height over time, helping identify which growing areas are performing above or below expectations.")

width_heatmap = create_heatmap(plant_growth, "Date", "Plant", "Width (Inches)",
                               "Plant Width Heatmap",
                               "This heatmap reveals differences in plant width measurements across units, enabling quick comparison of lateral growth distribution throughout the system.")

leaf_heatmap = create_heatmap(plant_growth, "Date", "Plant", "Leaf (Inches)",
                              "Largest Leaf Size Heatmap",
                              "This heatmap shows how the largest leaf sizes vary across units and time, helping to identify spatial trends and growth anomalies in canopy development.")

# Reusable alert card generator
def get_alert_card(icon, title, message_top, message_bottom, color):
    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col(DashIconify(icon=icon, width=70, height=70, color="white"), width="auto",
                        style={"display": "flex", "alignItems": "center", "justifyContent": "center"}),
                dbc.Col(html.H4(title, className="text-white", style={
                    "fontSize": "22px", "fontFamily": "Arvo", "textAlign": "center"}), width=True,
                        style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
            ], className="mb-3"),
            # Top paragraph
            html.P(message_top, className="text-white", style={
                "fontSize": "16px", "fontFamily": "Lato", "textAlign": "center", "marginBottom": "8px"
            }),
            # Bottom paragraph
            html.P(message_bottom, className="text-white", style={
                "fontSize": "16px", "fontFamily": "Lato", "textAlign": "center", "marginBottom": "0"
            })
        ]),
        style={
            "backgroundColor": color,
            "padding": "30px",
            "borderRadius": "12px",
            "boxShadow": "0px 4px 10px rgba(255, 255, 255, 0.2)",
            "margin": "10px",
            "textAlign": "center"
        }
    )

def get_yield_insight():
    avg_yield = plant_harvest["Yield (Grams)"].mean()
    if avg_yield < 30:
        return get_alert_card("mdi:barley", "Yield: Critical",
            f"Yield is well below the optimal 50g+ range. Current: {avg_yield:.1f}g.",
            "Improve nutrient delivery, verify EC and pH levels, and increase lighting exposure.",
            "#dc3545")
    elif avg_yield < 50:
        return get_alert_card("mdi:barley", "Yield: Warning",
            f"Yield is slightly under the expected threshold of 50g+. Current: {avg_yield:.1f}g.",
            "Consider adjusting nutrients, lighting duration, and irrigation strategy.",
            "#e0a800")
    return get_alert_card("mdi:barley", "Yield: Normal",
        f"Yield is within the optimal range (50g+). Current: {avg_yield:.1f}g.",
        "Maintain your current growing conditions and keep monitoring regularly.",
        "#28a745")

def get_ph_insight():
    avg_ph = unit_measurements["pH"].mean()
    if avg_ph < 5.2:
        return get_alert_card("mdi:scale-balance", "pH: Critical",
            f"pH is too acidic. Optimal range: 5.5–6.5. Current: {avg_ph:.2f}.",
            "Apply a base solution to raise pH and prevent root damage.",
            "#dc3545")
    elif avg_ph > 6.8:
        return get_alert_card("mdi:scale-balance", "pH: Critical",
            f"pH is too alkaline. Optimal range: 5.5–6.5. Current: {avg_ph:.2f}.",
            "Use a mild acid like phosphoric acid to bring the pH down gradually.",
            "#dc3545")
    elif avg_ph < 5.5 or avg_ph > 6.5:
        return get_alert_card("mdi:scale-balance", "pH: Warning",
            f"pH is slightly outside the target range of 5.5–6.5. Current: {avg_ph:.2f}.",
            "Stabilize with pH adjusters and monitor levels over the next few days.",
            "#e0a800")
    return get_alert_card("mdi:scale-balance", "pH: Normal",
        f"pH is in the ideal range (5.5–6.5). Current: {avg_ph:.2f}.",
        "No adjustments needed—continue current monitoring routine.",
        "#28a745")

def get_ec_insight():
    avg_ec = 3.33  # Hardcoded mS/cm
    if avg_ec < 0.7:
        return get_alert_card("mdi:water-percent", "EC: Critical",
            f"Electrical conductivity is far below the optimal range (1.0–2.0 S/m). Current: {avg_ec:.2f}.",
            "Add more nutrients to enrich the solution and support plant growth.",
            "#dc3545")
    elif avg_ec > 2.5:
        return get_alert_card("mdi:water-percent", "EC: Critical",
            f"Electrical conductivity is too high. Target range is 1.0–2.0 S/m. Current: {avg_ec:.2f}.",
            "Dilute with fresh water or flush the system to reduce salt buildup.",
            "#dc3545")
    elif avg_ec < 1.0 or avg_ec > 2.0:
        return get_alert_card("mdi:water-percent", "EC: Warning",
            f"EC is slightly outside the optimal range (1.0–2.0 S/m). Current: {avg_ec:.2f}.",
            "Fine-tune the nutrient mix and recheck levels after the next feeding.",
            "#e0a800")
    return get_alert_card("mdi:water-percent", "EC: Normal",
        f"Electrical conductivity is stable and within the 1.0–2.0 S/m range. Current: {avg_ec:.2f}.",
        "Maintain consistent feeding schedule and check weekly.",
        "#28a745")

def get_light_insight():
    avg_natural = sun_data["Hours of Daylight"].mean()
    artificial = float(unit_parameters.get("Artificial Light (Hours)", pd.Series([0])).iloc[0])
    total_light = min(avg_natural + artificial, 24)

    if total_light < 6:
        return get_alert_card("mdi:white-balance-sunny", "Light: Critical",
            f"Total light exposure is too low. Minimum required: 6 hours/day. Current: {total_light:.1f} hrs.",
            "Increase artificial lighting or reposition plants for more sun.",
            "#dc3545")
    return get_alert_card("mdi:white-balance-sunny", "Light: Normal",
        f"Total light exposure exceeds the 6-hour minimum. Current: {total_light:.1f} hrs.",
        "Light availability is sufficient—no changes needed at this time.",
        "#28a745")

def get_leaf_size_insight():
    avg_leaf_size = plant_growth["Leaf (Inches)"].mean()
    if avg_leaf_size < 2.0:
        return get_alert_card("mdi:leaf", "Leaf Size: Critical",
            f"Leaf size is far below the optimal threshold (3+ inches). Current: {avg_leaf_size:.1f}\".",
            "Apply micronutrients and improve airflow and humidity control.",
            "#dc3545")
    elif avg_leaf_size < 3.0:
        return get_alert_card("mdi:leaf", "Leaf Size: Warning",
            f"Leaf size is slightly under the 3-inch target. Current: {avg_leaf_size:.1f}\".",
            "Review nutrient balance and increase light intensity if needed.",
            "#e0a800")
    return get_alert_card("mdi:leaf", "Leaf Size: Normal",
        f"Average leaf size meets the optimal 3-inch threshold. Current: {avg_leaf_size:.1f}\".",
        "Continue current growth strategy and monitor leaf expansion.",
        "#28a745")

def get_brix_insight():
    avg_brix = plant_harvest["Brix"].mean()
    if avg_brix < 6:
        return get_alert_card("mdi:fruit-grapes", "Brix Score: Critical",
            f"Brix value is below ideal levels. Goal is 8+ for high-quality produce. Current: {avg_brix:.1f}.",
            "Increase potassium uptake and optimize ripening conditions.",
            "#dc3545")
    elif avg_brix < 8:
        return get_alert_card("mdi:fruit-grapes", "Brix Score: Warning",
            f"Brix score is approaching optimal but not quite there. Current: {avg_brix:.1f}.",
            "Improve nutrient timing and boost light exposure during fruit development.",
            "#e0a800")
    return get_alert_card("mdi:fruit-grapes", "Brix Score: Normal",
        f"Brix score is at or above target levels (8+). Current: {avg_brix:.1f}.",
        "Maintain your current practices to preserve sweetness and quality.",
        "#28a745")

# Dashboard Layout with Tabs
app.layout = html.Div([

    html.H1("Hydroponic Monitoring Dashboard", style={
        "fontFamily": "'Berkshire Swash', cursive",
        "fontSize": "48px",
        "textAlign": "center",
        "color": "#F39C12",
        "marginTop": "30px",
        "marginBottom": "10px"
    }),

    html.P(
        "This interactive dashboard provides real-time monitoring of environmental conditions, plant growth metrics, harvest trends, and system health insights. Select a tab below to explore detailed charts, alerts, and recommendations tailored to your hydroponic system.",
        style={
            "fontFamily": "Lato",
            "fontSize": "18px",
            "color": "white",
            "textAlign": "center",
            "maxWidth": "900px",
            "margin": "0 auto 30px auto"  # center + spacing before tabs
        }
    ),

    dcc.Tabs(id="tabs", value="environmental-conditions",
         style={
             "backgroundColor": "#1e1e1e",
             "padding": "10px",
             "borderRadius": "8px",
             "boxShadow": "0px 4px 12px rgba(0,0,0,0.3)",
             "fontFamily": "Arvo",
             "fontSize": "20px",
             "marginTop": "100px",
             "marginBottom": "100px"
         },
         colors={
             "border": "white",
             "primary": "#F39C12",  # Active tab underline color
             "background": "#1e1e1e"  # Unselected tab background
         },
        parent_className="custom-tabs",
        className="tab-container", children=[

        dcc.Tab(
            label="Environmental Conditions",
            value="environmental-conditions",
            style={
                "color": "white",
                "fontFamily": "Arvo",
                "fontSize": "20px",
                "padding": "12px 24px",
                "backgroundColor": "#1e1e1e",
                "border": "2px solid white",
                "borderRadius": "8px",
                "marginRight": "12px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.2)"
            },
            selected_style={
                "color": "#F39C12",
                "fontFamily": "Arvo",
                "fontSize": "20px",
                "padding": "12px 24px",
                "backgroundColor": "#1e1e1e",
                "border": "2px solid #F39C12",
                "borderRadius": "8px",
                "marginRight": "12px",
                "boxShadow": "0 4px 12px rgba(243, 156, 18, 0.4)"
            },
            children=[
                html.H2("🌿 Environmental Conditions", style={
                    "color": "white",
                    "fontFamily": "Arvo",
                    "textAlign": "center",
                    "marginTop": "40px"
                }),
                html.P(
                    "This page summarizes the key parameters of your hydroponic unit, including plant type and count, artificial light exposure, watering schedules, and system uptime. "
                    "It also includes real-time sensor data trends for water depth, pH, electrical conductivity (EC), nutrient concentration (PPM), temperature, and natural sunlight. "
                    "Use this data to monitor environmental stability and make informed adjustments for optimal plant growth.",
                    style={
                        "textAlign": "center",
                        "fontSize": "16px",
                        "color": "white",
                        "fontFamily": "Lato",
                        "marginBottom": "40px"
                    }
                ),

                # Info Cards (3 per row with diverse colors)
                dbc.Container([

                    # First Row
                    dbc.Row([
                        dbc.Col(create_info_card("mdi:identifier", "Unit ID", unit_id, "#5DADE2"),  # Bright blue-gray
                                width=4, style={"width": "100%"}),
                        dbc.Col(create_info_card("mdi:seedling", "Plant Type", plant_type, "#45B39D"),  # Teal
                                width=4, style={"width": "100%"}),
                        dbc.Col(create_info_card("mdi:numeric", "Plant Count", plant_count, "#EB984E"),  # Orange-red
                                width=4, style={"width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"}),

                    # Second Row
                    dbc.Row([
                        dbc.Col(create_info_card("mdi:grass", "Growing Medium", medium, "#58D68D"),  # Light green
                                width=4, style={"width": "100%"}),
                        dbc.Col(create_info_card("mdi:leaf", "Nutrients (N-P-K)", f"{n_value} - {p_value} - {k_value}",
                                                 "#AF7AC5"),  # Purple
                                width=4, style={"width": "100%"}),
                        dbc.Col(
                            create_info_card("mdi:white-balance-sunny", "Artificial Light", f"{artificial_light} Hours",
                                             "#F7DC6F"),  # Soft amber
                            width=4, style={"width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"}),

                    # Third Row
                    dbc.Row([
                        dbc.Col(create_info_card("mdi:clock-outline", "System Uptime", f"{uptime} Hours", "#3498DB"),
                                # Blue
                                width=4, style={"width": "100%"}),
                        dbc.Col(create_info_card("mdi:water", "Watering (Uptime)",
                                                 f"{watering_duration_uptime} min every {watering_interval_uptime} min",
                                                 "#48C9B0"),  # Aqua
                                width=4, style={"width": "100%"}),
                        dbc.Col(create_info_card("mdi:water-off", "Watering (Downtime)",
                                                 f"{watering_duration_downtime} min every {watering_interval_downtime} min",
                                                 "#F1948A"),  # Coral
                                width=4, style={"width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"})

                ], fluid=True, className="mt-4"),

                # Line Charts Section
                dbc.Container([

                    # Row 1
                    dbc.Row([
                        dbc.Col(depth_chart, width=6, style={"padding": "20px", "width": "100%"}),
                        dbc.Col(ph_chart, width=6, style={"padding": "20px", "width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"}),

                    # Row 2
                    dbc.Row([
                        dbc.Col(ec_chart, width=6, style={"padding": "20px", "width": "100%"}),
                        dbc.Col(ppm_chart, width=6, style={"padding": "20px", "width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"}),

                    # Row 3
                    dbc.Row([
                        dbc.Col(temperature_chart, width=6, style={"padding": "20px", "width": "100%"}),
                        dbc.Col(sunlight_chart, width=6, style={"padding": "20px", "width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"}),

                ], fluid=True)
            ]),

        dcc.Tab(
            label="Plant Growth & Harvest",
            value="plant-growth-harvest",
            style={
                "color": "white",
                "fontFamily": "Arvo",
                "fontSize": "20px",
                "padding": "12px 24px",
                "backgroundColor": "#1e1e1e",
                "border": "2px solid white",
                "borderRadius": "8px",
                "marginRight": "12px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.2)"
            },
            selected_style={
                "color": "#F39C12",
                "fontFamily": "Arvo",
                "fontSize": "20px",
                "padding": "12px 24px",
                "backgroundColor": "#1e1e1e",
                "border": "2px solid #F39C12",
                "borderRadius": "8px",
                "marginRight": "12px",
                "boxShadow": "0 4px 12px rgba(243, 156, 18, 0.4)"
            },
            children=[

            html.H2("🌾 Plant Growth & Harvest", style={
                "color": "white",
                "fontFamily": "Arvo",
                "textAlign": "center",
                "marginTop": "40px"
            }),
            html.P(
                "This page provides an overview of plant growth trends and harvest performance. "
                "You can view average plant height, width, and leaf size over time, including forecasts. "
                "Use the dropdown to analyze individual plants or view all data collectively. ",
                style={
                    "textAlign": "center",
                    "fontSize": "16px",
                    "color": "white",
                    "fontFamily": "Lato",
                    "marginBottom": "40px"
                }
            ),

            # Dropdown for plant selection
            html.Div([
                html.Label("🌱 Select a Plant", style={
                    "color": "#F39C12",  # Vibrant orange
                    "fontFamily": "Arvo",
                    "fontSize": "22px",
                    "textAlign": "center",
                    "marginBottom": "12px",
                    "textShadow": "1px 1px 2px rgba(0, 0, 0, 0.6)"
                }),
                dcc.Dropdown(
                    id="plant-selector",
                    options=[{"label": "All Plants", "value": "all"}] +
                            [{"label": plant, "value": plant} for plant in sorted(plant_growth["Plant"].unique())],
                    value="all",
                    style={
                        "width": "300px",
                        "margin": "0 auto",
                        "fontFamily": "Lato",
                        "fontSize": "16px",
                        "color": "black",
                        "backgroundColor": "#FDEBD0",  # Soft background color
                        "border": "2px solid #F39C12",
                        "borderRadius": "8px",
                        "boxShadow": "0 0 8px rgba(243, 156, 18, 0.6)"
                    },
                    placeholder="Choose a plant",
                    searchable=False,
                    clearable=False
                )
            ], style={"textAlign": "center", "padding": "30px 20px 20px 20px"}),

            html.Div(id="harvest-info-cards", style={"padding": "0 20px", "marginBottom": "20px"}),

            # Summary section (box plots & pie chart) - Hidden when selecting an individual plant
            html.Div(id="summary-section", children=[

                dbc.Container([

                    # Row 1: Yield & Roots Box Plots
                    dbc.Row([
                        dbc.Col(yield_chart, width=6, style={"padding": "20px", "width": "100%"}),
                        dbc.Col(roots_chart, width=6, style={"padding": "20px", "width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"}),

                    # Row 2: Brix Box Plot & Pie Chart
                    dbc.Row([
                        dbc.Col(brix_chart, width=6, style={"padding": "20px", "width": "100%"}),
                        dbc.Col(brix_pie_chart_div, width=6, style={"padding": "20px", "width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"})

                ], fluid=True)

            ]),

            # Line Charts & Heatmaps — All Plants Only
            html.Div(id="all-plants-section", children=[

                dbc.Container([

                    # Row 1: Height
                    dbc.Row([
                        dbc.Col([
                            html.H3("Average Plant Height", style={
                                "textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"
                            }),
                            html.P(
                                "This chart visualizes the average height of plants across all units, along with a forecast to illustrate potential future growth patterns.",
                                style={
                                    "textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"
                                }),
                            dcc.Graph(id="height-line-chart")
                        ], width=6, style={"padding": "20px", "width": "100%"}),

                        dbc.Col(id="height-heatmap", children=[height_heatmap], width=6, style={"padding": "20px", "width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"}),

                    # Row 2: Width
                    dbc.Row([
                        dbc.Col([
                            html.H3("Average Plant Width", style={
                                "textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"
                            }),
                            html.P(
                                "This chart displays how the average width of plants changes over time, including a projection to anticipate lateral expansion trends.",
                                style={
                                    "textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"
                                }),
                            dcc.Graph(id="width-line-chart")
                        ], width=6, style={"padding": "20px", "width": "100%"}),

                        dbc.Col(id="width-heatmap", children=[width_heatmap], width=6, style={"padding": "20px", "width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"}),

                    # Row 3: Leaf Size
                    dbc.Row([
                        dbc.Col([
                            html.H3("Average Largest Leaf Size", style={
                                "textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"
                            }),
                            html.P(
                                "This chart tracks the average size of the largest leaf per plant, highlighting growth trends and forecasting potential size increases.",
                                style={
                                    "textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"
                                }),
                            dcc.Graph(id="leaf-line-chart")
                        ], width=6, style={"padding": "20px", "width": "100%"}),

                        dbc.Col(id="leaf-heatmap", children=[leaf_heatmap], width=6, style={"padding": "20px", "width": "100%"})
                    ], className="mb-4", justify="between",
                        style={"display": "flex", "justifyContent": "space-between"})

                ], fluid=True)
            ]),

            # Individual Plant Charts – initially hidden
            html.Div(id="individual-plant-charts", style={"padding": "20px", "display": "none"})

        ]),

        dcc.Tab(
            label="Alert Center",
            value="insights",
            style={
                "color": "white",
                "fontFamily": "Arvo",
                "fontSize": "20px",
                "padding": "12px 24px",
                "backgroundColor": "#1e1e1e",
                "border": "2px solid white",
                "borderRadius": "8px",
                "marginRight": "12px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.2)"
            },
            selected_style={
                "color": "#F39C12",
                "fontFamily": "Arvo",
                "fontSize": "20px",
                "padding": "12px 24px",
                "backgroundColor": "#1e1e1e",
                "border": "2px solid #F39C12",
                "borderRadius": "8px",
                "marginRight": "12px",
                "boxShadow": "0 4px 12px rgba(243, 156, 18, 0.4)"
            },
            children=[

            html.H2("🚨 Alert Center", style={
                "color": "white",
                "fontFamily": "Arvo",
                "textAlign": "center",
                "marginTop": "40px"
            }),
            html.P(
                "This page highlights key plant health indicators and environmental metrics that may require your attention. "
                "Each alert card summarizes whether values such as yield, pH, EC, light, and leaf size fall within optimal thresholds. "
                "Use these alerts to identify critical issues, review minor warnings, and confirm stable growing conditions across your hydroponic system.",
                style={
                    "textAlign": "center",
                    "fontSize": "16px",
                    "color": "white",
                    "fontFamily": "Lato",
                    "marginBottom": "40px"
                }
            ),

            dbc.Container([
                # First Row: Yield & pH Insights
                dbc.Row([
                    dbc.Col(get_yield_insight(), width=6, style={"width": "100%"}),
                    dbc.Col(get_ph_insight(), width=6, style={"width": "100%"})
                ], className="mb-4", justify="between", style={"display": "flex", "justifyContent": "space-between"}),

                # Second Row: EC & Sunlight Insights
                dbc.Row([
                    dbc.Col(get_ec_insight(), width=6, style={"width": "100%"}),
                    dbc.Col(get_light_insight(), width=6, style={"width": "100%"})
                ], className="mb-4", justify="between", style={"display": "flex", "justifyContent": "space-between"}),

                # Third Row: Leaf Size & Brix Score Insights
                dbc.Row([
                    dbc.Col(get_leaf_size_insight(), width=6, style={"width": "100%"}),
                    dbc.Col(get_brix_insight(), width=6, style={"width": "100%"})
                ], className="mb-4", justify="between", style={"display": "flex", "justifyContent": "space-between"})
            ], fluid=True, className="mt-4")
        ])
    ])
], style={"backgroundColor": "#121212", "padding": "30px"})

@app.callback(
    Output("height-line-chart", "figure"),
    Output("width-line-chart", "figure"),
    Output("leaf-line-chart", "figure"),
    Output("summary-section", "style"),
    Output("all-plants-section", "style"),
    Output("individual-plant-charts", "children"),
    Output("individual-plant-charts", "style"),
    Output("harvest-info-cards", "children"),
    Input("plant-selector", "value")
)
def update_growth_and_layout(selected_plant):
    if selected_plant == "all":
        df = plant_growth_summary.copy()
        title_suffix = ""
        summary_style = {"display": "block"}
        all_plants_style = {"display": "block"}
        individual_section = None
        individual_style = {"display": "none"}
        info_cards = None
    else:
        df = plant_growth[plant_growth["Plant"] == selected_plant].copy()
        df = df.groupby("Date")[["Height (Inches)", "Width (Inches)", "Leaf (Inches)"]].mean().reset_index()
        title_suffix = f" — {selected_plant}"
        summary_style = {"display": "none"}
        all_plants_style = {"display": "none"}
        individual_style = {"display": "block"}

        # Projections
        height_proj = extend_growth_data(df, "Height (Inches)")
        width_proj = extend_growth_data(df, "Width (Inches)")
        leaf_proj = extend_growth_data(df, "Leaf (Inches)")

        # Line Charts (Individual Layout: 2 + 1 format)
        individual_section = dbc.Container([

            # Row 1: Height + Width
            dbc.Row([
                dbc.Col([
                    html.H3(f"Plant Height{title_suffix}", style={
                        "textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"
                    }),
                    html.P(
                        "This chart forecasts vertical growth for the selected plant, based on past measurements and modeled trends.",
                        style={"textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"}),
                    dcc.Graph(
                        figure=create_projection_chart(df, height_proj, "Date", "Height (Inches)", "", "", "").children[
                            -1].figure)
                ], width=6, style={"padding": "20px", "width": "100%"}),

                dbc.Col([
                    html.H3(f"Plant Width{title_suffix}", style={
                        "textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"
                    }),
                    html.P("This chart projects lateral growth trends for the selected plant, using recent width data.",
                           style={"textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"}),
                    dcc.Graph(
                        figure=create_projection_chart(df, width_proj, "Date", "Width (Inches)", "", "", "").children[
                            -1].figure)
                ], width=6, style={"padding": "20px", "width": "100%"})
            ], className="mb-4", justify="between", style={"display": "flex", "justifyContent": "space-between"}),

            # Second Row: Leaf Size (centered and half-width)
            dbc.Row([
                dbc.Col([
                    html.H3(f"Largest Leaf Size{title_suffix}", style={
                        "textAlign": "center", "fontSize": "24px", "color": "white", "fontFamily": "Arvo"
                    }),
                    html.P(
                        "This chart estimates trends in maximum leaf size, projecting potential expansion over time.",
                        style={"textAlign": "center", "fontSize": "16px", "color": "white", "fontFamily": "Lato"}),
                    dcc.Graph(figure=create_projection_chart(
                        df, leaf_proj, "Date", "Leaf (Inches)", "", "", ""
                    ).children[-1].figure)
                ], width=6, style={"padding": "20px", "width": "100%"}),

                dbc.Col([], width=6, style={"padding": "20px", "width": "100%"})  # Empty column to maintain row structure
            ], className="mb-4", justify="between", style={"display": "flex", "justifyContent": "space-between"})

        ], fluid=True)

        # Info Cards for Individual Plant
        harvest_df = plant_harvest[plant_harvest["Plant"] == selected_plant]
        if not harvest_df.empty:
            latest = harvest_df.sort_values("Date").iloc[-1]

            def build_info_card(icon, label, value, color):
                return dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            DashIconify(icon=icon, width=40, height=40, color="white"),
                            html.H5(label, style={"fontFamily": "Arvo", "fontSize": "18px", "color": "#f8f9fa", "textAlign": "center", "marginTop": "10px"}),
                            html.H4(str(value), style={"fontFamily": "Lato", "fontSize": "22px", "color": "#ced4da", "textAlign": "center"})
                        ]),
                        style={"backgroundColor": color, "padding": "20px", "borderRadius": "10px",
                               "boxShadow": "0px 4px 10px rgba(255, 255, 255, 0.1)", "margin": "10px"}
                    ),
                    width=3
                )

            info_cards = dbc.Container([
                dbc.Row([
                    dbc.Col(create_info_card("mdi:barley", "Harvest Yield (g)", latest["Yield (Grams)"], "#2C3E50"),
                            width=2, style={"width": "100%"}),
                    dbc.Col(create_info_card("mdi:grass", "Root Length (mm)", latest["Roots (Millimeters)"], "#16A085"),
                            width=2, style={"width": "100%"}),
                    dbc.Col(create_info_card("mdi:fruit-grapes", "Brix Score", latest["Brix"], "#8E44AD"),
                            width=2, style={"width": "100%"}),
                    dbc.Col(create_info_card("mdi:calendar", "Harvest Date", pd.to_datetime(latest["Date"]).date(),
                                             "#E67E22"),
                            width=2, style={"width": "100%"}),
                ], className="mb-4", justify="between", style={"display": "flex", "justifyContent": "space-between"})
            ], fluid=True, className="mt-4")
        else:
            info_cards = html.Div("No harvest data available for this plant.", style={
                "color": "white", "textAlign": "center", "fontFamily": "Lato"
            })

    # All-plant charts (for when "all" is selected)
    height_fig = create_projection_chart(df, extend_growth_data(df, "Height (Inches)"), "Date", "Height (Inches)",
                                         f"Average Plant Height{title_suffix}", "Plant Height (Inches)",
                                         "This chart visualizes the average height of plants across all units, along with a forecast to illustrate potential future growth patterns.")

    width_fig = create_projection_chart(df, extend_growth_data(df, "Width (Inches)"), "Date", "Width (Inches)",
                                        f"Average Plant Width{title_suffix}", "Plant Width (Inches)",
                                        "This chart displays how the average width of plants changes over time, including a projection to anticipate lateral expansion trends.")

    leaf_fig = create_projection_chart(df, extend_growth_data(df, "Leaf (Inches)"), "Date", "Leaf (Inches)",
                                       f"Average Largest Leaf Size{title_suffix}", "Largest Leaf Size (Inches)",
                                       "This chart tracks the average size of the largest leaf per plant, highlighting growth trends and forecasting potential size increases.")

    return (
        height_fig.children[-1].figure,
        width_fig.children[-1].figure,
        leaf_fig.children[-1].figure,
        summary_style,
        all_plants_style,
        individual_section,
        individual_style,
        info_cards
    )

@app.callback(
    Output("plant-selector", "value"),
    Input("tabs", "value"),
    State("plant-selector", "value"),
    prevent_initial_call=True
)
def reset_dropdown_on_tab_change(active_tab, current_value):
    # If leaving the Plant Growth tab, reset dropdown
    if active_tab != "plant-growth-harvest" and current_value != "all":
        return "all"
    raise dash.exceptions.PreventUpdate

# Run Server
if __name__ == "__main__":
    app.run(debug=True)