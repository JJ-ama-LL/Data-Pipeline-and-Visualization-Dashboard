import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import requests

def download_file(url, path):
    if path.exists():
        return
     
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def clean_data(df):
    # Define critical columns
    critical_columns = ["tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", 
                    "DOLocationID", "fare_amount"]
    
    # Drop rows with missing values in critical columns
    df = df.dropna(subset=critical_columns)

    # Filter out invalid trips
    df = df[
    (df["trip_distance"] > 0) &
    (df["fare_amount"] > 0) &
    (df["fare_amount"] <= 500) &
    (df["tpep_dropoff_datetime"] >= df["tpep_pickup_datetime"])
    ]

    # Calculate trip duration in minutes
    df["trip_duration_minutes"] = (
    (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"])
    .dt.total_seconds() / 60
    )

    # Extract pickup hour
    df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour

    # Extract pickup day of week
    df["pickup_day_of_week"] = df["tpep_pickup_datetime"].dt.day_name()

    # Calculate trip speed in mph, handling cases where duration is zero
    df["trip_speed_mph"] = 0.0
    mask = df["trip_duration_minutes"] > 0
    df.loc[mask, "trip_speed_mph"] = (
        df.loc[mask, "trip_distance"] /
        (df.loc[mask, "trip_duration_minutes"] / 60)
    )
    return df

# Set Streamlit page configuration
st.set_page_config(
    page_title="NYC Yellow Taxi Data Dashboard",
    page_icon="🚕",
    layout="wide"
)

# Add a title to the dashboard
st.title("NYC Yellow Taxi Data Dashboard")

st.markdown("""
        This dashboard provides insights into the NYC Yellow Taxi trips for January 2024. The data has been programmatically downloaded, validated and cleaned to ensure 
        accuracy and reliability from which the dashboard then displays metrics and graphical visualizations of the data such as bar charts, line charts, histograms, pie charts,
        and heatmaps in order to help users understand patterns in taxi usage. Make use of the filters in the sidebar to explore different aspects of the data, 
        by adjusting ranges including trip dates, pickup hours and payment types to dynamically update the visualizations accordingly to your desired selections. 
""")

# Create tabs for different visualizations
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Metrics Overview",
    "Top Pickup Zones Bar Chart",
    "Avg Fare by Hour Line Chart",
    "Trip Distance Distribution Histogram",
    "Payment Type Breakdown Pie Chart",
    "Trips by Day of Week and Hour Heatmap"
])

# Load Cleaned data with caching to optimize performance
@st.cache_data
def load_data():
    taxi_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
    zone_url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

    BASE_DIR = Path(__file__).resolve().parent.parent
    data_dir = BASE_DIR / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)

    taxi_path = data_dir / "yellow_tripdata_2024-01.parquet"
    zone_path = data_dir / "taxi_zone_lookup.csv"

    download_file(taxi_url, taxi_path)
    download_file(zone_url, zone_path)

    df = pd.read_parquet(taxi_path)

    df = df.sample(n=1000000, random_state=42) 

    df = clean_data(df)
    zones_df = pd.read_csv(zone_path)

    return df, zones_df

df, zones_df = load_data()

# Display key metrics 
with tab1:
    col1, col2, col3, col4, col5 = st.columns(5) 
    col1.metric("Total Trips", f"{len(df):,}") 
    col2.metric("Average Fare", f"${df['fare_amount'].mean():.2f}")
    col3.metric("Total Revenue", f"${df['fare_amount'].sum():,.2f}")
    col4.metric("Average Trip Distance", f"{df['trip_distance'].mean():.2f} miles") 
    col5.metric("Average Trip Duration", f"{(df['trip_duration_minutes'].mean()):.2f} min")

# Add sidebar filters
st.sidebar.header("Filters")

payment_labels = {
    1: "Credit Card",
    2: "Cash",
    3: "No Charge",
    4: "Dispute",
    0: "Unknown"
}
df["payment_type_label"] = df["payment_type"].map(payment_labels)

min_date = df["tpep_pickup_datetime"].min().date()
max_date = df["tpep_pickup_datetime"].max().date()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))

payment_types = st.sidebar.multiselect(
    "Select Payment Types",
    options=list(payment_labels.values()),
    default=list(payment_labels.values())
)

# Apply filters to the DataFrame
filtered_df = df[
    (df["tpep_pickup_datetime"] >= pd.to_datetime(date_range[0])) &
    (df["tpep_pickup_datetime"] <= pd.to_datetime(date_range[1])) &
    (df["pickup_hour"] >= hour_range[0]) &
    (df["pickup_hour"] <= hour_range[1]) &
    (df["payment_type_label"].isin(payment_types))
]

with tab2:
    # Counting top 10 pickup zones
    top_zones = (
        filtered_df["PULocationID"]
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_zones.columns = ["PULocationID", "Count"]

    # Merge with zones to get zone names
    top_zones = top_zones.merge(
        zones_df[["LocationID", "Zone"]],
        left_on="PULocationID",
        right_on="LocationID",
        how="left"
    )

    # Sort by count for better visualization
    top_zones = top_zones.sort_values("Count", ascending=True)

    # Create Horizontal Bar Chart for top pickup zones with visual enhancements
    fig1 = px.bar(
        top_zones,
        x="Count",
        y="Zone",
        orientation="h",
        text="Count",
        color="Count",
        color_continuous_scale="Greens",
        hover_data={"PULocationID": True, "Count": True},
    )

    # Bar Chart Formatting
    fig1.update_traces(textposition="outside")

    fig1.update_layout(
        title={"text": "Top 10 Pickup Zones by Trip Count", "x":0.5},
        xaxis_title="Trip Count",
        yaxis_title="Pickup Zone",
        template="plotly_dark",
        margin=dict(l=250)
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("""The above horizontal bar chart shows the top pickup zones by their total trip count from the sample of the dataset. 
                It can be seen that a very small amount of zones, being the top four, account for a large majority of the total trips. We can 
                infer from this that the top four zones possesses a very high demand for taxis which may correlate to the level of activity seen
                in these areas. Below these top four zones, there is a small decrease in the amount of total trips seen suggesting that these areas 
                consists of less activity or maybe even the demand for taxis in these areas is much lower.
    """)

with tab3:
    # Groups average fare amount by pickup hour
    hourly_fare = (
        filtered_df.groupby("pickup_hour")["fare_amount"]
        .mean()
        .reset_index()
    )

    # Create Line chart for average fare by hour of day
    fig2 = px.line(
        hourly_fare,
        x="pickup_hour",
        y="fare_amount",
        markers=True,
        labels={
            "pickup_hour": "Hour of Day",
            "fare_amount": "Average Fare ($)"
        }
    )

    # Formatting x and y axes
    fig2.update_xaxes(
        tickmode="linear",
        tick0=0,
        dtick=1,
        title="Hour of Day"
    )

    fig2.update_yaxes(tickprefix="$", tickformat=".2f", title="Average Fare ($)")

    fig2.update_layout(
        template="plotly_dark",
        title={"text": "Average Fare by Hour of Day", "x": 0.5}
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""The above line graph displays the fare amount seen at each hour of the day. From this graph we see a very
                high increase in the fare amount compared to other hours in the early morning of the day however, a few hours 
                before this spike, we also see the lowest fare amount. We can infer from this that the lowest fare amount is due to not 
                many people requiring a taxi as they may still be at home or asleep and we can account the very large spike in the fare to 
                correlate to the time when most people are on their way to work, school or any of their other daily activities. The fare from 
                then on remains at a consistent value throughout the day.            
    """)

with tab4:
    # Filter out trips with unrealistic distances for better visualization
    hist_filtered = filtered_df[
    (filtered_df['trip_distance'] > 0) & (filtered_df['trip_distance'] < 20)
    ]

    # Create histogram for trip distance distribution
    fig3 = px.histogram(
        hist_filtered,
        x="trip_distance",
        nbins=50,
        title="Distribution of Trip Distances",
        labels={"trip_distance": "Trip Distance (miles)", "count": "Number of Trips"},
        template="plotly_white",
        color_discrete_sequence=["green"],
        opacity=0.8,
        hover_data={"trip_distance": True}
    )

    # Histogram formatting
    fig3.update_traces(marker_line_width=0.5, marker_line_color="white", hovertemplate='Trip Distance: %{x}<br>Count: %{y}<extra></extra>')

    fig3.update_layout(
        title=dict(text="Distribution of Trip Distances (Trips ≤ 20 miles)", x=0.5, font=dict(size=20)),
        xaxis=dict(range=[0, 20], title="Trip Distance (miles)", tick0=0, dtick=2),
        yaxis=dict(title="Number of Trips", showgrid=True),
        font=dict(family="Arial", size=12),
        bargap=0.05
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("""The above histogram show a distribution of the trip distances seen from the dataset. From this we can 
                infer that only very rarely do people take very long taxi rides differing greatly from the amount of trips 
                we see with very short distances. This provides the insight that most people prefer to not spend the added 
                costs attached to a very long taxi trip but rather use taxis as method of convenience.
    """)

with tab5:
    color_sequence = ["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728", "#7f7f7f"]

    # Count trips by payment type
    payment_counts = filtered_df["payment_type"].value_counts().reset_index()
    payment_counts.columns = ["payment_type", "count"]

    # Replace numeric codes with labels for plotting
    payment_counts["payment_type"] = payment_counts["payment_type"].map(payment_labels)

    # Create pie chart
    fig4 = px.pie(
        payment_counts,
        names="payment_type",
        values="count",
        title="Payment Type Breakdown",
        hole=0.4,
        template="plotly_white",
        color_discrete_sequence=color_sequence
    )

    # Format pie chart to show percentages and labels
    fig4.update_traces(
        textinfo="percent+label",
        textposition="inside",
        hovertemplate='%{label}: %{percent:.1%} (%{value} trips)<extra></extra>'
    )

    fig4.update_layout(
        title=dict(text="Payment Type Breakdown", x=0.5, font=dict(size=20)),
        font=dict(family="Arial", size=12)
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("""The above pie chart shows the breakdown of the most used payment types across all trips in the dataset. We can 
                see that an extremely large amount of the payments are confirmed usign Credit Cards with Cash following behind. We can 
                infer from this that the taxi industry of New York City consists mostly of digital transactions rather than physical cash ones. 
                This also shows that many of the people of make use of the taxi service frequently are those who are qualified and able to possess a credit card.
    """)

with tab6:
    # Create heatmap data by counting trips for each combination of pickup day of week and hour
    heatmap_data = (
        filtered_df.groupby(["pickup_day_of_week", "pickup_hour"])
        .size()
        .reset_index(name="trip_count")
    )

    # Define weekday order for consistent plotting
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Create heatmap for trips by day of week and hour
    fig5 = px.density_heatmap(
        heatmap_data,
        x="pickup_hour",
        y="pickup_day_of_week",
        z="trip_count",
        category_orders={"pickup_day_of_week": weekday_order},
        title="Trips by Day of Week and Hour",
        labels={
            "pickup_hour": "Hour of Day",
            "pickup_day_of_week": "Day of Week",
            "trip_count": "Number of Trips"
        },
        template="plotly_white"
    )

    # Formatting heatmap
    fig5.update_traces(
        zmin=0,
        zmax=heatmap_data["trip_count"].max()
    )

    fig5.update_yaxes(categoryorder="array", categoryarray=weekday_order[::-1])
    fig5.update_xaxes(tick0=0, dtick=1)

    fig5.update_layout(
        title=dict(text="Trips by Day of Week and Hour", x=0.5, font=dict(size=20)),
        font=dict(family="Arial", size=12),
        width=1000,
        height=600,
        margin=dict(l=80, r=80, t=100, b=80),
        coloraxis_colorbar=dict(
            title="Number of Trips",
            tickformat=",",
            thickness=15,
            lenmode="fraction",
            len=0.75
        )
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("""Lastly, this heatmap displays trips grouped and organized by their associated day and hour of pickup. 
                From this map, we see that the busiest period for taxis is Wednesday between hours 15 - 19. Alongside this 
                we can also see significant activity at this axact time across all days of the week excluding Sunday. This 
                can be tied to the fact during the weekday, a lot of people are travelling to different places and the overall 
                activity is high. This time everyday also correlates to aa very common time where most businesses or schools may 
                close for the day which also plays a role in the increased activity seen.
    """)