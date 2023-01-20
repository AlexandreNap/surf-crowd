import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
import plotly.express as px
import pymongo
import certifi
import datetime


st.set_page_config(layout="wide",
                   page_title="Surf-Crowd")

st.header("""Surf Crowd
Cette page permet de visualiser des reports de spots de surfs français. 
Les spots actuellement analysés sont de Biarritz, Anglet, Capbreton,
et Lacanau.

Une IA scanne les sports de surf en direct pour obtenir de manière régulière des
informations sur les spots de surf.
Elle détecte l'ensemble des surfeurs à l'eau et les comptes.

#### Remarques : 
* Les baigneurs et plagistes ne sont généralement pas détectés.
* Des surfeurs peuvent par moment être cachés derrière des séries de vagues et ne pas être comptés.
* Les webcams des plages peuvent tomber en panne, empéchant toute prise d'information  visuelle sur le spot""")


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
    query = {"date": {"$gte": date1, "$lte": date2}, "n_surfers_yolo5": {"$gt": -1}}
    for x in col.find(query):
        my_list.append(x)
    return my_list


def remove_frozen_webcam_days(df):
    df_temp = df.groupby(["date", "spot_name"])["n_surfers_yolo5"].std().reset_index()
    df_temp.columns = ["date", "spot_name", "freezing"]
    df = df.merge(df_temp, on=["date", "spot_name"])
    df["freezing"] = (df["freezing"] == 0) & (df["n_surfers_yolo5"] > 0)
    df = df[~df["freezing"]]
    return df


def weighted_moving_average(df):
    df["dt-1"] = df.groupby(["spot_name"])["date_time"].shift(1)
    df["dt-1"] = pd.to_datetime(df["dt-1"], format='%Y-%m-%d_%H-%M')
    df["date_time"] = pd.to_datetime(df["date_time"], format='%Y-%m-%d_%H-%M')
    df["dt-1"] = (df["date_time"] - df["dt-1"]) / np.timedelta64(1, 's')
    return df


def preprocess_data(df):
    df['date_time'] = pd.to_datetime(df.date_time, format='%Y-%m-%d_%H-%M')
    df = df[["date", "spot_name", "date_time", "n_surfers_yolo5"]]
    df = remove_frozen_webcam_days(df)

    df_temp = df.groupby(["date", "spot_name"])["date_time"] \
        .aggregate(["min", "max"]).reset_index()
    df_temp["min"] = df_temp["min"] - datetime.timedelta(minutes=45)
    df_temp["max"] = df_temp["max"] + datetime.timedelta(minutes=45)
    df_temp = df_temp.melt(id_vars=["date", "spot_name"], value_vars=['min', 'max'], value_name="date_time")
    df_temp["n_surfers_yolo5"] = 0
    df_temp.drop(columns=["variable"], inplace=True)
    df = pd.concat((df, df_temp), axis=0)
    df.sort_values(by=["date_time"], inplace=True)
    df = weighted_moving_average(df)
    return df


date = st.sidebar.date_input('date', datetime.datetime.today())
df = pd.DataFrame(get_data((date - datetime.timedelta(28)).strftime('%Y-%m-%d'),
                           date.strftime('%Y-%m-%d')))
df = preprocess_data(df)

df_last7 = df[df.date_time > (date - datetime.timedelta(7)).strftime('%Y-%m-%d')]

fig = px.line(df_last7, x='date_time', y="n_surfers_yolo5", color="spot_name", template="seaborn",
              title="Report du nombre de surfeurs", labels={'date_time': '', 'n_surfers_yolo5': ''})
st.plotly_chart(fig, use_container_width=True)


st.subheader("""Surf Report des 4 dernières semaines : 
On ne compte pas ici le nombre de surfeurs différents.\n
Si un surfeurs reste sur le spot pendant une heure et est détecté toutes les 10 minutes, il sera compté 6 fois""")

fig = px.bar(
        df.groupby(["date", "spot_name"])["n_surfers_yolo5"].sum().reset_index(),
        x='date', y="n_surfers_yolo5", color="spot_name", template="seaborn",
        title="Comptage quotidien", labels={'spot_name': '', 'n_surfers_yolo5': ''},
        barmode="stack"
)
st.plotly_chart(fig)


col1, col2 = st.columns(2)
with col1:
    fig = px.bar(
        df.groupby(["spot_name"])["n_surfers_yolo5"].sum().reset_index(),
        x='spot_name', y="n_surfers_yolo5", template="seaborn",
        title="Nombre de surfeurs total sur la période", labels={'spot_name': '', 'n_surfers_yolo5': ''}
    )
    st.plotly_chart(fig)

with col2:
    fig = px.bar(
        df.groupby(["spot_name"])["n_surfers_yolo5"].mean().reset_index(),
        x='spot_name', y="n_surfers_yolo5", template="seaborn",
        title="Nombre de surfeurs moyen sur la période", labels={'spot_name': '', 'n_surfers_yolo5': ''}
    )
    st.plotly_chart(fig)

components.html('<iframe src="https://magicseaweed.com/Le-Prevent-Surf-Report/1527/Embed/" width="1800" height="1600" frameborder="0"></iframe>',
                width=1200, height=600)
