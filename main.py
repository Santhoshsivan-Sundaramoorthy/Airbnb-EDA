## Libraries
import math

from pymongo import MongoClient
from streamlit_folium import folium_static
import folium
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

sns.set()
##streamlit Page configuration:
st.set_page_config(
    page_title="AirBnB Exploratory Data Analysis",
    page_icon="airbnb_icon.png",
    layout="wide"
)
image_path = "airbnb_icon.png"
image = st.image(image_path, width=50)
st.subheader('AirBnB Exploratory Data Analysis')

header_col1, header_col2, header_col3 = st.columns(3)
body_col1, body_col2 = st.columns(2)
eda_col1, eda_col2, eda_col3 = st.columns(3)
eda2_col1, eda2_col2 = st.columns(2)


## Setting up MongoDB Atlas connection

# MongoDB Atlas connection string
mongo_uri = "mongodb+srv://santhoshsivan29101999:1234567890@cluster0.7pjahhx.mongodb.net/?retryWrites=true&w=majority"

# Create a MongoClient instance with SSL support
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)

# Connect to the database
db = client.sample_airbnb

# Access the collection
collection = db.listingsAndReviews

## Retrieve the data from MongoDB and convert it to a DataFrame

# Retrieve all documents from the collection
cursor = collection.find({})

# Convert the cursor to a list of dictionaries
data = list(cursor)

# Convert the list of dictionaries to a DataFrame
rawdata = pd.DataFrame(data)

## Pre-Processing the raw data
df = rawdata.drop(['security_deposit','cleaning_fee','weekly_price', 'monthly_price','reviews_per_month','last_review','first_review','last_scraped','calendar_last_scraped'], axis = 1)
df = df.dropna(axis=0)
df['price'] = list(map(str, df['price']))
df['price'] = list(map(float, df['price']))
df['guests_included'] = list(map(str, df['guests_included']))
df['guests_included'] = list(map(int, df['guests_included']))
df['extra_people'] = list(map(str, df['extra_people']))
df['extra_people_price'] = list(map(float, df['extra_people']))
df = df.drop('extra_people', axis=1)
df['amenities_count'] = df['amenities'].apply(len)
q = df['price'].quantile(0.99)
df = df[df['price']<q]
df['availability_30'] = df['availability'].apply(lambda x: x.get('availability_30', 0))
df['availability_60'] = df['availability'].apply(lambda x: x.get('availability_60', 0))
df['availability_90'] = df['availability'].apply(lambda x: x.get('availability_90', 0))
df['availability_365'] = df['availability'].apply(lambda x: x.get('availability_365', 0))
df.drop('availability', axis=1, inplace=True)
df.reset_index(drop=True, inplace=True)



def popup_list(x):
    if x == 'Price':
        return f"${row['price']}"
    if x == 'Type':
        return f"{row['property_type']}"
    if x == 'Bedrooms':
        return f"Bedrooms Available: {row['bedrooms']}"





cat = ['Type', 'Price', 'Bedrooms']
with header_col2:
    with st.spinner("Please wait..."):
        selected_country = st.selectbox("Select the country", df['address'].apply(lambda x: x['country']).unique())
with body_col1:
    selected_cat = st.selectbox("Select the catagory", cat)
if selected_country:

    filtered_df = df[df['address'].apply(lambda x: x['country']) == selected_country]
    # Now, extract the latitude and longitude coordinates
    coordinates = filtered_df['address'].apply(lambda x: x['location']['coordinates'])
    # Get the coordinates for the selected country
    li_latitude = coordinates.apply(lambda x: x[1])
    li_longitude = coordinates.apply(lambda x: x[0])
    # Convert degrees to radians
    latitudes_radians = [math.radians(lat) for lat in li_latitude]
    longitudes_radians = [math.radians(lon) for lon in li_longitude]
    # Calculate the average latitude and longitude in radians
    avg_latitude_radian = sum(latitudes_radians) / len(li_latitude)
    avg_longitude_radian = sum(longitudes_radians) / len(li_longitude)
    latitude = math.degrees(avg_latitude_radian)
    longitude = math.degrees(avg_longitude_radian)
    m = folium.Map(location=[latitude, longitude], zoom_start=6, tiles='Stamen Terrain')

    for index, row in df.iterrows():
        if selected_country == row['address']['country']:
            lon, lat = row['address']['location']['coordinates']
            popup = folium.Popup(popup_list(selected_cat), show=True, close_button=False)
            folium.Marker([lat, lon], popup=popup).add_to(m)

    selected_country_data = df[df['address'].str['country'] == selected_country]
    prices = selected_country_data['price']

    # Visualize price distribution for each selected row
    plt.figure(figsize=(12, 6))
    sns.histplot(prices, bins=30, kde=True)
    plt.title(f'Price Distribution of {selected_country}')
    plt.xlabel('Price')
    plt.ylabel('Count')
    with eda_col1:
        st.pyplot(plt)

    # Visualize average price by property type
    plt.figure(figsize=(12, 6))
    sns.barplot(x='property_type', y='price', data=selected_country_data)
    plt.title(f'Average Price by Property Type in {selected_country}')
    plt.xticks(rotation=90)
    plt.xlabel('Property Type')
    plt.ylabel('Average Price')
    with eda_col2:
        st.pyplot(plt)

    # Visualize price trends across different seasons
    # Select the relevant columns for analysis
    availability_cols = ['availability_30', 'availability_60', 'availability_90', 'availability_365']

    # Calculate the availability for each season
    selected_country_data['First Quater'] = selected_country_data['availability_30']
    selected_country_data['Second Quater'] = selected_country_data['availability_60'] - selected_country_data[
        'availability_30']
    selected_country_data['Third Quater'] = selected_country_data['availability_90'] - selected_country_data[
        'availability_60']
    selected_country_data['Fourth Quater'] = selected_country_data['availability_365'] - selected_country_data[
        'availability_90']

    # Select the relevant columns for analysis
    availability_col2 = ['First Quater', 'Second Quater', 'Third Quater', 'Fourth Quater']

    selected_country_data[availability_col2].mean().plot(kind='bar', figsize=(10, 5))
    plt.title('Average Availability by Season')
    plt.xlabel('Quater')
    plt.ylabel('Average Availability')
    with eda_col3:
        st.pyplot(plt)

    ##Top 10 Property Types available
    top_10_property_types = selected_country_data['property_type'].value_counts().head(10)
    plt.figure(figsize=(10, 6))
    sns.countplot(data=selected_country_data, y='property_type', order=top_10_property_types.index)
    plt.title(f'Top 10 Property Types in {selected_country}')
    plt.xticks(rotation=45)
    plt.xlabel('Property Type')
    plt.ylabel('Count')
    with eda2_col1:
        st.pyplot(plt)
    # f'Distribution of Room Types'
    plt.figure(figsize=(10, 6))
    roomtype_counts = selected_country_data['room_type'].value_counts()
    plt.pie(roomtype_counts, labels=roomtype_counts.index, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title(f'Distribution of Room Types in {selected_country}')
    with eda2_col2:
        st.pyplot(plt)
with body_col1:
    folium_static(m)
