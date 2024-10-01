import streamlit as st
st.set_page_config(
    page_title="Exp Analysis",
    page_icon=":bar_chart:",  # 💬📊 https://streamlit-emoji-shortcodes-streamlit-app-gwckff.streamlit.app
)
import pandas as pd
from ..data import DBManager, Config, DataManager
from .show_conversation import show_conversation_page
from .show_data import show_data_page



def main(cfg_name: str):
    if 'cfg' not in st.session_state:
        st.session_state.cfg = Config.from_yaml(DataManager.normalize_config_name(cfg_name))
        st.session_state.data_manager = DataManager(st.session_state.cfg)
    
    page = st.sidebar.selectbox("Select Page", ["📊 Data", "🔍 Conversation", ])
    
    # add splitter
    st.sidebar.markdown("---")

    if page == "🔍 Conversation":
        show_conversation_page()
    elif page == "📊 Data":
        show_data_page()

