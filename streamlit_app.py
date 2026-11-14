"""Ponto de entrada da interface: poetry run streamlit run streamlit_app.py"""
import os

import streamlit as st

from app.core.secrets_env import export_to_environ

# No Streamlit Community Cloud as configurações ficam em "Secrets". Copiamos para o ambiente
# ANTES de importar o resto, porque o config.py lê as variáveis ao ser importado.
# Localmente não há secrets: vale o .env.
try:
    export_to_environ(st.secrets, os.environ)
except Exception:
    pass

from app.ui import overview_page, ranking_page  # noqa: E402

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