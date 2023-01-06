import sys
import subprocess
import streamlit as st
import streamlit.components.v1 as components

subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "../requirements.txt"])

import numpy as np
import pandas as pd
import plotly.express as px
import pymongo
import certifi
import datetime

@st.cache
def get_data(date1, date2):
    client = pymongo.MongoClient(st.secrets["MONGO_ADRESS"], tlsCAFile=certifi.where())
    db = client["surf"]
    col = db["sviews"]
    my_list = []
    # add use of optional date_range
    query = {"date": {"$gte": date1, "$lt": date2}, "n_surfers_yolo5": {"$gt": -1}}
    for x in col.find(query):
        my_list.append(x)
    return my_list


date1 = st.sidebar.date_input('start date', datetime.date(2022,5,1))

df = pd.DataFrame(get_data(date1.strftime('%Y-%m-%d'),
                           (date1 + datetime.timedelta(7)).strftime('%Y-%m-%d')))
print(df.columns)
print(df.date.min())
print(df.date.max())

df2 = df.copy().spot_name.value_counts().reset_index()
df2.columns = ["spot", "n"]
print(df2)
fig = px.bar(df2, x='spot', y="n", color="n")
st.plotly_chart(fig, width=120)



df['date_time'] = pd.to_datetime(df.date_time, format='%Y-%m-%d_%H-%M')
df.sort_values(by="date_time", inplace=True)

fig = px.line(df, x='date_time', y="n_surfers_yolo5", color="spot_name",
             width=1500, height=800)
st.plotly_chart(fig, width=1600)

fig = px.bar(
    df[["spot_name", "n_surfers_yolo5"]].groupby(["spot_name"]).median().reset_index(),
    x='spot_name', y="n_surfers_yolo5", color="n_surfers_yolo5")
st.plotly_chart(fig, width=120)

fig = px.bar(
    df[["spot_name", "n_surfers_yolo5"]].groupby(["spot_name"]).mean().reset_index(),
    x='spot_name', y="n_surfers_yolo5", color="n_surfers_yolo5")
st.plotly_chart(fig, width=120)


components.html('<iframe src="https://magicseaweed.com/Le-Prevent-Surf-Report/1527/Embed/" width="800" height="1600" frameborder="0"></iframe>',
                width=1200, height=1600)
