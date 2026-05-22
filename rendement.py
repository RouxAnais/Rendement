import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Analyse de rendement - Montée / Descente")

uploaded_file = st.file_uploader("Dépose ton fichier CSV :", type=["csv"])

if uploaded_file is not None:

    # 1) Première lecture brute pour trouver la ligne "Temps"
    df_brut = pd.read_csv(
        uploaded_file,
        sep=";",
        decimal=",",
        header=None,
        dtype=str
    )

    ligne_temps = df_brut[df_brut[0] == "Temps"].index

    if len(ligne_temps) == 0:
        st.error("Impossible de trouver la colonne 'Temps' dans le fichier.")
        st.stop()

    # Remettre le curseur au début du fichier
    uploaded_file.seek(0)

    # 2) Deuxième lecture à partir de la bonne ligne
    df = pd.read_csv(
        uploaded_file,
        sep=";",
        decimal=",",
        skiprows=ligne_temps[0]
    )

    # Renommage des colonnes
    df.columns = [
        "Temps",
        "Couple_0_5",
        "Couple_0_50",
        "Effort",
        "Deplacement",
        "Rendement_montee_brut",
        "Rendement_descente_brut",
        "Montée",
        "Descente",
        "Rendement_montee_stats",
        "Rendement_descente_stats"
    ]

    df.columns = df.columns.str.strip()

    df["Montée"] = df["Montée"].astype(str).str.replace(",", ".", regex=False)
    df["Descente"] = df["Descente"].astype(str).str.replace(",", ".", regex=False)
    df["Temps"] = df["Temps"].astype(str).str.replace(",", ".", regex=False)

    df["Montée"] = pd.to_numeric(df["Montée"], errors="coerce")
    df["Descente"] = pd.to_numeric(df["Descente"], errors="coerce")
    df["Temps"] = pd.to_numeric(df["Temps"], errors="coerce")

    # Nettoyage
    df.loc[df["Montée"] > 1, "Montée"] = None
    df.loc[df["Descente"] > 1, "Descente"] = None

    tab1, tab2, tab3 = st.tabs(["Rendement", "Montée filtrée", "Descente filtrée"])

    fig1 = px.line(
        df,
        x="Temps",
        y=["Montée", "Descente"],
        labels={"value": "Rendement", "variable": "Type"},
        title="Rendement Montée + Descente"
    )
    tab1.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(
        df,
        x="Temps",
        y="Montée",
        labels={"Montée": "Rendement montée"},
        title="Rendement Montée filtrée"
    )
    tab2.plotly_chart(fig2, use_container_width=True)

    fig3 = px.line(
        df,
        x="Temps",
        y="Descente",
        labels={"Descente": "Rendement descente"},
        title="Rendement Descente filtrée"
    )
    tab3.plotly_chart(fig3, use_container_width=True)

    # Stats
    q_low = df["Montée"].quantile(0.05)
    q_high = df["Montée"].quantile(0.95)
    df_monte_clean = df[(df["Montée"] >= q_low) & (df["Montée"] <= q_high)]

    q_low = df["Descente"].quantile(0.05)
    q_high = df["Descente"].quantile(0.95)
    df_desc_clean = df[(df["Descente"] >= q_low) & (df["Descente"] <= q_high)]

    moyenne_montee = df_monte_clean["Montée"].mean() * 100
    moyenne_descente = df_desc_clean["Descente"].mean() * 100

    st.subheader("Statistiques")
    st.write("Moyenne montée :", moyenne_montee)
    st.write("Moyenne descente :", moyenne_descente)

else:
    st.info("Veuillez importer un fichier CSV pour lancer l'analyse.")
