import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import folium

# states
if "lat_location" not in st.session_state:
    st.session_state['lat_location'] = 36.839

if "lon_location" not in st.session_state:
    st.session_state['lon_location'] = 54.436

if st.session_state.get('lat_lon',False):
    st.session_state['lat_location'], st.session_state['lon_location'] = st.session_state.pop('lat_lon')
    st.session_state['city_name'] = ''
    st.session_state['set_search'] = True

# css (just to add some queries)
with open("styles.css",'r') as f:
    css_file = f.read()
st.markdown(f"<style>{css_file}</style>",unsafe_allow_html=True)

# some info
st.info("All dates and times are based on geo location time")
st.info("You can search for city in any language but results will be in English")

# Select Unit section
st.write("##### select units")
cols = st.columns(2)
with cols[0]:
    temp_unit = st.selectbox("select temperature unit",options=["℃","℉"],key='temp_unit')
with cols[1]:
    metric_unit = st.selectbox("select metric unit",options=["Km","Miles"],key="metric_unit")

# General Variables
response = None

# ------Start Search Section------
st.write("##### Search")
msg = st.empty()
# Search by city
cols = st.columns([3,1])
with cols[0]:
    city = st.text_input("City:",key='city_name')

with cols[1]:
    if st.button("Search",key="search_by_city"):
        if city:
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                st.session_state['lat_location'] = float(data["nearest_area"][0]["latitude"])
                st.session_state['lon_location'] = float(data["nearest_area"][0]["longitude"])
                
        else:
            msg.error('Please enter a city name')

# Search by Geo Location
cols = st.columns(3)
with cols[0]:
    latitude = st.number_input("Latitude",format="%.4f",key="lat_location")
with cols[1]:
    longitude = st.number_input("Longitude",format="%.4f",key="lon_location")
with cols[2]:
    if st.button("Search",key="search_by_geo_location"):
        st.session_state['lat_lon'] = [latitude,longitude]
        st.rerun(scope='app')

# Search by Map
st.write("##### Or Pick a Location on Map")
msg = st.empty()

m = folium.Map(location=[latitude, longitude], zoom_start=6)  
m.add_child(folium.LatLngPopup())  # allows user to click and show lat/lon
m.add_child(folium.Marker(location=[latitude, longitude],popup=f"Latitude: {latitude:.4f}\nLongitude: {longitude:.4f}",icon=folium.Icon(color='red')))

map_data = st_folium(m, height=400, width=700,returned_objects=["last_clicked"])

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.session_state['lat_lon'] = [lat,lon]
    st.rerun(scope='app')

# ------End of Search Sectoin------

# Make API call with coordinates
if st.session_state.get('set_search',False):
    st.session_state.pop("set_search")
    try:
        url = f"https://wttr.in/{latitude},{longitude}?format=j1"
        response = requests.get(url)
        msg.success(f"Selected Location: {latitude:.4f}, {longitude:.4f}")
    except:
        msg.error("No weather info for selected location")
    
data = ""  
if response:
    if response.status_code == 200:
        data = response.json()
        # Weather Conditions
        current_condition = data["current_condition"][0]
        cloud_cover = current_condition["cloudcover"]
        temp_c = current_condition["temp_C"]
        temp_f = current_condition["temp_F"]
        temp = temp_c if temp_unit == "℃" else temp_f
        observation_datetime = current_condition["localObsDateTime"]
        windspeed_kmph = current_condition["windspeedKmph"]
        windspeed_miles = current_condition["windspeedMiles"]
        windspeed = windspeed_kmph if metric_unit == "Km" else windspeed_miles
        humidity = current_condition["humidity"]
        weather = current_condition["weatherDesc"][0]["value"]
        condition = current_condition["weatherDesc"][0]["value"]

        # Geo data
        geo_data = data["nearest_area"][0]
        city_name = geo_data["areaName"][0]["value"]
        country_name = geo_data["country"][0]["value"]
        region_name = geo_data["region"][0]["value"]
        pop = geo_data["population"]
        lat = geo_data["latitude"]
        lon = geo_data["longitude"]

    else:
        st.error("something went wrong")
if data:
    # show current Weather
    st.write("##### Current Weather")
    st.write(f"🌧️ weather: **{weather}**")
    st.write(f"⛅ cloud cover: **{cloud_cover}%**")
    st.write(f"🌡️ temperature: **{temp}{temp_unit}**")
    st.write(f"💧 humidity: **{humidity}%**")
    st.write(f"💨 wind speed: **{windspeed} {metric_unit} per hour**")
    st.write(f"⏲️ Observation date/time: **{observation_datetime}**")

    # show Geo info
    st.write("##### Location Geo Informations")
    with st.container(key="geo_table"):
        table_geo = [{"city":city_name,"region":region_name,"country":country_name,
                        "population":pop,"latitude":lat,"longitude":lon}]
        st.table(table_geo)

    with st.container(key="geo_small"):
        st.write(f"city: **{city_name}**")
        st.write(f"region: **{region_name}**")
        st.write(f"country: **{country_name}**")
        st.write(f"population: **{pop}**")
        st.write(f"latitude: **{lat}**")
        st.write(f"longitude: **{lon}**")

    # Forecast Section
    # data
    st.write("##### Forecast Weather")
    dates = [data["weather"][i]["date"] for i in [0,1,2]]
    selected_date = st.selectbox("Select Date",options=dates,key="forecast_date")
    selected_index = next(index for index,date in enumerate(dates) if date == selected_date)
    selected_weather = data["weather"][selected_index]
    sunrise_time = selected_weather["astronomy"][0]["sunrise"]
    sunset_time = selected_weather["astronomy"][0]["sunset"]

    # for Iran it considers +1 hour in first 6 months of year that is wrong and we correct it
    if country_name == "Iran" and (3,20) < (datetime.today().month,datetime.today().day) < (10,23):
        new_time = datetime.strptime(sunrise_time, "%I:%M %p") - timedelta(hours=1)
        sunrise_time = new_time.strftime("%I:%M %p")
        new_time = datetime.strptime(sunset_time, "%I:%M %p") - timedelta(hours=1)
        sunset_time = new_time.strftime("%I:%M %p")

    if temp_unit == "℃":
        max_temp = selected_weather["maxtempC"]
        min_temp = selected_weather["mintempC"]
        avg_temp = selected_weather["avgtempC"]
    else:
        max_temp = selected_weather["maxtempF"]
        min_temp = selected_weather["mintempF"]
        avg_temp = selected_weather["avgtempF"]

    # show daily
    st.write("##### Daily")
    with st.container(key="daily_table"):
        table_daily = [{"sunrise":sunrise_time,"sunset":sunset_time,f"max {temp_unit}":max_temp+temp_unit,
                    f"min {temp_unit}":min_temp+temp_unit,f"average {temp_unit}":avg_temp+temp_unit}]
        st.table(table_daily)

    with st.container(key="daily_small"):
        st.write(f"sunrise: **{sunrise_time}**")
        st.write(f"sunset: **{sunset_time}**")
        st.write(f"max temperature: **{max_temp}{temp_unit}**")
        st.write(f"min temperature: **{min_temp}{temp_unit}**")
        st.write(f"average temperature: **{avg_temp}{temp_unit}**")

    # show hourly
    
    with st.expander("Hourly Details"):
        counter_time = datetime.strptime("12:00 AM","%I:%M %p")
        df = pd.DataFrame(columns=["time","temperature"])

        for hour in selected_weather["hourly"]:
            weather = hour["weatherDesc"][0]["value"]
            cloud_cover = hour["cloudcover"]
            temp_c = hour["HeatIndexC"]
            temp_f = hour["HeatIndexF"]
            temp = temp_c if temp_unit == "℃" else temp_f
            humidity = hour["humidity"]
            windspeed_kmph = hour["WindGustKmph"]
            windspeed_miles = hour["WindGustMiles"]
            windspeed = windspeed_kmph if metric_unit == "Km" else windspeed_miles

            new_df = pd.DataFrame([{"time":counter_time.strftime("%H:%M"),"temperature":int(temp), "weather":weather}])
            df = pd.concat([df,new_df]).reset_index(drop=True)

            start_time = counter_time.strftime("%I:%M %p")
            end_time = (counter_time + timedelta(hours=3)).strftime("%I:%M %p")
            st.write(f"**{start_time} to {end_time}**")
            with st.container(key=f"hourly_table_{counter_time}"):
                table_daily = [{"🌧️ weather":weather,"⛅ cloud cover":cloud_cover+"%","🌡️ temperature":temp+temp_unit,
                    "💧 humidity":humidity+'%',"💨 wind speed":f"{windspeed} {metric_unit} per hour"}]
                st.table(table_daily)

            with st.container(key=f"hourly_small_{counter_time}"):
                st.write(f"🌧️ weather: **{weather}**")
                st.write(f"⛅ cloud cover: **{cloud_cover}%**")
                st.write(f"🌡️ temperature: **{temp}{temp_unit}**")
                st.write(f"💧 humidity: **{humidity}%**")
                st.write(f"💨 wind speed: **{windspeed} {metric_unit} per hour**")

            st.markdown("<hr>",unsafe_allow_html=True)

            counter_time += timedelta(hours=3)

    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df["time"],df["temperature"])
    ax.set_title("Hourly Temperature")
    ax.set_xlabel("Time")
    ax.grid(True)
    ax.set_ylabel(f"Temperature ({temp_unit})")
    st.pyplot(fig)
    cols = st.columns(8)
    counter = 0
    df['temperature'] = df["temperature"].astype(str) + temp_unit
    st.dataframe(df.set_index('time'))
    