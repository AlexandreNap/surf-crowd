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
Les spots actuellement analysés sont ceux de Biarritz, Anglet, Capbreton,
et Lacanau.

Toutes les 5 minutes, un modèle d'intelligence artificielle scanne en direct les spots de surf afin d'obtenir régulièrement des informations sur ces derniers.
Le système détecte tous les surfeurs présents à l'eau et les compte.

#### Remarques : 
* Les baigneurs et plagistes sont généralement différentiés des surfeurs. De même pour les surfeurs débutants dans les mousses.
* Des surfeurs peuvent par moment être cachés derrière des séries de vagues et ne pas être comptés.
C'est pour cela que les données présentées sont lissées dans le temps.
* Les webcams des plages peuvent parfois tomber en panne, empéchant toute prise d'information  visuelle sur le spot, 
ou répétant en boucle un même passage.""")


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
    df_temp = df.groupby(["date", "spot_name"])["n_surfers"].std().reset_index()
    df_temp.columns = ["date", "spot_name", "freezing"]
    df = df.merge(df_temp, on=["date", "spot_name"])
    df["freezing"] = (df["freezing"] == 0) & (df["n_surfers"] > 0)
    df = df[~df["freezing"]]
    return df


def weighted_moving_average(df, w0=0.0009):
    df["date_time"] = pd.to_datetime(df["date_time"], format='%Y-%m-%d_%H-%M')
    df.sort_values(by=["date_time"], inplace=True)

    df["dt-1"] = df.groupby(["spot_name", "date"])["date_time"].shift(1)
    df["dt-1"] = pd.to_datetime(df["dt-1"], format='%Y-%m-%d_%H-%M')
    df["nsurfers-1"] = df.groupby(["spot_name", "date"])["n_surfers"].shift(1)
    df["delta-1"] = (df["date_time"] - df["dt-1"]) / np.timedelta64(1, 's')

    df["dt-2"] = df.groupby(["spot_name", "date"])["date_time"].shift(2)
    df["dt-2"] = pd.to_datetime(df["dt-2"], format='%Y-%m-%d_%H-%M')
    df["nsurfers-2"] = df.groupby(["spot_name", "date"])["n_surfers"].shift(2)
    df["delta-2"] = (df["date_time"] - df["dt-2"]) / np.timedelta64(1, 's')

    df.replace("NaT", np.NaN, inplace=True)
    df.fillna(0.0001, inplace=True)
    df["n_surfers_wma"] = df.apply(lambda x:\
                                       (x["n_surfers"] * w0 +
                                        x["nsurfers-1"] / x["delta-1"] +
                                        x["nsurfers-2"] / x["delta-2"]) / (w0 + 1/x["delta-1"] + 1/x["delta-2"]),
                                   axis=1)
    return df


def add_0_on_start_end_days(df, cols=["n_surfers"]):
    df_temp = df.groupby(["date", "spot_name"])["date_time"] \
        .aggregate(["min", "max"]).reset_index()
    df_temp["min"] = df_temp["min"] - datetime.timedelta(minutes=15)
    df_temp["max"] = df_temp["max"] + datetime.timedelta(minutes=15)
    df_temp = df_temp.melt(id_vars=["date", "spot_name"], value_vars=['min', 'max'], value_name="date_time")
    for col in cols:
        df_temp[col] = 0
    df_temp.drop(columns=["variable"], inplace=True)
    df = pd.concat((df, df_temp), axis=0)

    # remove 0 added on very last datetime by spot
    last_date_by_spot = df.groupby(["spot_name"])["date_time"].max().reset_index()
    df = pd.merge(df, last_date_by_spot, indicator=True, how='outer') \
        .query('_merge=="left_only"') \
        .drop('_merge', axis=1)

    df.sort_values(by=["date_time"], inplace=True)
    return df


def preprocess_data(df):
    df['date_time'] = pd.to_datetime(df.date_time, format='%Y-%m-%d_%H-%M')
    df["n_surfers"] = df["n_surfers_yolo5"]
    df = df[["date", "spot_name", "date_time", "n_surfers"]]
    df = remove_frozen_webcam_days(df)

    df = add_0_on_start_end_days(df)
    df.sort_values(by=["date_time"], inplace=True)

    df = weighted_moving_average(df)
    df = df[["date", "spot_name", "date_time", "n_surfers", "n_surfers_wma"]]
    df = add_0_on_start_end_days(df, ["n_surfers", "n_surfers_wma"])

    return df


date = st.sidebar.date_input('date', datetime.datetime.today())
df = pd.DataFrame(get_data((date - datetime.timedelta(28)).strftime('%Y-%m-%d'),
                           date.strftime('%Y-%m-%d')))
df = preprocess_data(df)

fig = px.line(df[df.date_time > (date - datetime.timedelta(7)).strftime('%Y-%m-%d')],
              x='date_time', y="n_surfers_wma", color="spot_name", template="seaborn",
              title="Report du nombre de surfeurs lissé", labels={'date_time': '', 'n_surfers_wma': ''})
st.plotly_chart(fig, use_container_width=True)


st.subheader("""Surf Report des 4 dernières semaines : 
On ne compte pas ici le nombre de surfeurs différents.\n
Si un surfeurs reste sur le spot pendant une heure et est détecté toutes les 10 minutes, il sera compté 6 fois.\n
Permet d'observer la fréquentation globale sur les 4 dernières semaines.""")

fig = px.bar(
        df.groupby(["date", "spot_name"])["n_surfers"].sum().reset_index(),
        x='date', y="n_surfers", color="spot_name", template="seaborn",
        title="Comptage quotidien", labels={'spot_name': '', 'n_surfers': ''},
        barmode="stack"
)
st.plotly_chart(fig, use_container_width=True)


col1, col2 = st.columns(2)
with col1:
    fig = px.bar(
        df.groupby(["spot_name"])["n_surfers"].sum().reset_index(),
        x='spot_name', y="n_surfers", template="seaborn",
        title="Nombre de surfeurs total sur la période", labels={'spot_name': '', 'n_surfers': ''}
    )
    st.plotly_chart(fig)

with col2:
    fig = px.bar(
        df.groupby(["spot_name"])["n_surfers"].mean().reset_index(),
        x='spot_name', y="n_surfers", template="seaborn",
        title="Nombre de surfeurs moyen sur la période", labels={'spot_name': '', 'n_surfers': ''}
    )
    st.plotly_chart(fig)
