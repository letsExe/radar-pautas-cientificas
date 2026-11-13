"""Ponto de entrada da interface: poetry run streamlit run streamlit_app.py"""
import streamlit as st

from app.ui import overview_page, ranking_page

st.set_page_config(page_title="Radar de Pautas Científicas", page_icon="📡", layout="wide")

st.title("📡 Radar de Pautas Científicas")
st.caption(
    "Pesquisas da UNILA com potencial de pauta. A IA sugere e justifica; "
    "a decisão é sempre do jornalista."
)

pages = [
    st.Page(ranking_page.render, title="Ranking", icon="📰", url_path="ranking", default=True),
    st.Page(overview_page.render, title="Visão geral", icon="📊", url_path="visao-geral"),
]
st.navigation(pages).run()