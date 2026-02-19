import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="NYC Yellow Taxi Data Dashboard",
    page_icon="🚕",
    layout="wide"
)

st.title("NYC Yellow Taxi Data Dashboard")

@st.cache_data
def load_data():
    df = pd.read_parquet("data/clean/yellow_tripdata_2024-01_clean.parquet")
    return df

df = load_data()
 
# Display key metrics 
col1, col2, col3, col4, col5 = st.columns(5) 
col1.metric("Total Trips", f"{len(df):,}") 
col2.metric("Average Fare", f"${df['fare_amount'].mean():.2f}")
col3.metric("Total Revenue", f"${df['fare_amount'].sum():,.2f}")
col4.metric("Average Trip Distance", f"{df['trip_distance'].mean():.2f} miles") 
col5.metric("Average Trip Duration", f"{(df['trip_duration_minutes'].mean()):.2f} min")

st.sidebar.success("Select a page above")