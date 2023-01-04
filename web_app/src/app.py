import sys
import subprocess
import streamlit as st
import streamlit.components.v1 as components

subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "/app/surf-crowd/web_app/requirements.txt"])

import pandas as pd
import plotly.express as px
import pymongo
import certifi
import datetime


st.set_page_config(layout="wide")


@st.experimental_singleton
def init_connection():
    return pymongo.MongoClient(st.secrets["MONGO_ADRESS"], tlsCAFile=certifi.where())


client = init_connection()


@st.experimental_memo(ttl=300)
def get_data(date1, date2):
    db = client["surf"]
    col = db["sviews"]
    my_list = []
    # add use of optional date_range
    query = {"date": {"$gte": date1, "$lt": date2}, "n_surfers_yolo5": {"$gt": -1}}
    for x in col.find(query):
        my_list.append(x)
    return my_list


date1 = st.sidebar.date_input('start date', datetime.datetime.today() - datetime.timedelta(7))
df = pd.DataFrame(get_data(date1.strftime('%Y-%m-%d'),
                           (date1 + datetime.timedelta(7)).strftime('%Y-%m-%d')))

df2 = df.copy().spot_name.value_counts().reset_index()
df2.columns = ["spot", "n"]

df['date_time'] = pd.to_datetime(df.date_time, format='%Y-%m-%d_%H-%M')
df.sort_values(by="date_time", inplace=True)

fig = px.line(df, x='date_time', y="n_surfers_yolo5", color="spot_name", template="seaborn",
              title="Report du nombre de surfeurs", labels={'date_time': '', 'n_surfers_yolo5': ''})
st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(df2, x='spot', y="n", template="seaborn",
                 title="Nombre total compté sur la période", labels={'spot': '', 'n': ''})
    st.plotly_chart(fig)

with col2:
    fig = px.bar(
        df[["spot_name", "n_surfers_yolo5"]].groupby(["spot_name"]).mean().reset_index(),
        x='spot_name', y="n_surfers_yolo5", template="seaborn",
        title="Nombre moyen de surfeurs sur la période", labels={'spot_name': '', 'n_surfers_yolo5': ''})
    st.plotly_chart(fig)

components.html('<iframe src="https://magicseaweed.com/Le-Prevent-Surf-Report/1527/Embed/" width="1800" height="1600" frameborder="0"></iframe>',
                width=1200, height=600)
