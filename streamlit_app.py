"""Ponto de entrada da interface: poetry run streamlit run streamlit_app.py"""
import streamlit as st

from app.ui import ranking_page

st.set_page_config(page_title="Radar de Pautas Científicas", page_icon="📡", layout="wide")

st.title("📡 Radar de Pautas Científicas")
st.caption(
    "Pesquisas da UNILA com potencial de pauta. A IA sugere e justifica; "
    "a decisão é sempre do jornalista."
)

ranking_page.render()