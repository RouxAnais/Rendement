import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Analyse de rendement (comparaison)")

# Upload multiple fichiers (illimité)
uploaded_files = st.file_uploader(
    "Déposez vos fichiers CSV",
    type=["csv"],
    accept_multiple_files=True
)

# Fonction de lecture + nettoyage
def charger_fichier(uploaded_file):

    # Lecture brute pour trouver la ligne "Temps"
    df_brut = pd.read_csv(
        uploaded_file,
        sep=";",
        decimal=",",
        header=None,
        dtype=str
    )

    ligne_temps = df_brut[df_brut[0] == "Temps"].index

    if len(ligne_temps) == 0:
        return None

    uploaded_file.seek(0)

    # Lecture propre
    df = pd.read_csv(
        uploaded_file,
        sep=";",
        decimal=",",
        skiprows=ligne_temps[0]
    )

    # Renommage colonnes
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

    # Conversion numérique
    for col in ["Temps", "Montée", "Descente"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Nettoyage valeurs aberrantes
    df.loc[df["Montée"] > 1, "Montée"] = None
    df.loc[df["Descente"] > 1, "Descente"] = None

    return df


# ---------------- code principal ----------------

if uploaded_files:

    st.success(f"{len(uploaded_files)} fichier(s) chargé(s)")

    tabs = st.tabs([f"Fichier {i+1}" for i in range(len(uploaded_files))])

    for i, file in enumerate(uploaded_files):

        df = charger_fichier(file)

        if df is None:
            tabs[i].error("Impossible de lire le fichier.")
            continue

        # Graphique
        fig = px.line(
            df,
            x="Temps",
            y=["Montée", "Descente"],
            labels={"value": "Rendement", "variable": "Type"},
            title=file.name
        )

        tabs[i].plotly_chart(fig, use_container_width=True)

        # Statistiques montée
        q_low = df["Montée"].quantile(0.05)
        q_high = df["Montée"].quantile(0.95)
        df_monte_clean = df[(df["Montée"] >= q_low) & (df["Montée"] <= q_high)]

        # Statistiques descente
        q_low = df["Descente"].quantile(0.05)
        q_high = df["Descente"].quantile(0.95)
        df_desc_clean = df[(df["Descente"] >= q_low) & (df["Descente"] <= q_high)]

        moyenne_montee = df_monte_clean["Montée"].mean() * 100
        moyenne_descente = df_desc_clean["Descente"].mean() * 100

        tabs[i].subheader("Statistiques")

        tabs[i].write(f"Moyenne montée : {moyenne_montee:.2f} %")
        tabs[i].write(f"Moyenne descente : {moyenne_descente:.2f} %")

else:
    st.info("Importe un ou plusieurs fichiers CSV pour commencer l'analyse.")