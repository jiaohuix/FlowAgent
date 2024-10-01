import json, yaml
import streamlit as st
import pandas as pd
from ..data import DBManager, Config, DataManager


def refresh_conversation_id():
    _db: DBManager = st.session_state.db
    selected_exp_version = st.session_state.get("exp_version", None)
    query = {}
    if selected_exp_version is not None:
        query["exp_version"] = selected_exp_version
    st.session_state.run_exps = _db.query_run_experiments(query=query)

def show_conversation_page():
    """
    Streamlit UI for checking a finished experiment.
    """
    # ------------------ session_state --------------------
    if "db" not in st.session_state:
        assert 'cfg' in st.session_state
        cfg: Config = st.session_state.cfg
        st.session_state.db = DBManager(cfg.db_uri, cfg.db_name, cfg.db_message_collection_name)
        st.session_state.data_manager = DataManager(cfg)
    if "run_exps" not in st.session_state:
        refresh_conversation_id()
    
    db:DBManager = st.session_state.db
    data_manager:DataManager = st.session_state.data_manager
    
    # ------------------ sidebar --------------------
    with st.sidebar:
        # 1. select interested `exp_version`
        _ava_exp_versions = [None] + db.get_all_run_exp_versions()
        st.selectbox(
            "1️⃣ Select exp_version", 
            options=_ava_exp_versions,
            key="exp_version",
            on_change=refresh_conversation_id
        )
        st.info(f"run exps: {len(st.session_state.run_exps)}")
        
        # 2. select speicific `conversation_id`
        col1, col2 = st.columns([3, 1])
        _options = [f"({exp['workflow_id']}-{exp['user_profile_id']})_{exp['conversation_id']}" for exp in st.session_state.run_exps]
        _options.sort()
        with col1:
            conversation_id = st.selectbox(
                "2️⃣ Select conversation_id", 
                options=_options,
                
            )
            conversation_id = conversation_id.split("_", 1)[1]
        with col2:
            if st.button("Refresh"):
                refresh_conversation_id()
        customized_conversation_id = st.text_input(
            "Customized conversation_id"
        )
        if customized_conversation_id: conversation_id = customized_conversation_id
        st.info(f"selected conversation_id: {conversation_id}")
        display_option = st.selectbox(
            "Choose display option",
            options=["Table", "Dataframe"],
        )

    # ------------------ main --------------------
    if conversation_id:
        # 1. query conversation from db ; show the conversation
        conv = db.query_messages_by_conversation_id(conversation_id)
        if len(conv.msgs) == 0:
            st.warning(f"Conversation `{conversation_id}` is empty.")
            return
        df = conv.to_dataframe()
        selected_columns = ['role', 'content', 'utterance_id']
        df_selected = df[selected_columns].set_index('utterance_id')
        st.markdown(f"### Conversation `{conversation_id}`")
        if display_option == "Dataframe":
            st.dataframe(df_selected)
        else:
            st.table(df_selected, ) # table is better for reading then st.dataframe!
        
        # 2. query config from db; show the config
        conversation_metas = db.query_config_by_conversation_id(conversation_id)
        st.markdown(f"### Configuration")
        with st.expander("Details"):
            st.write(conversation_metas)
        
        # 3. show the user profile
        conv_cfg = Config.from_dict(conversation_metas)
        data_manager.refresh_config(conv_cfg)               # update the data_manager first~
        with open(data_manager.DIR_data_workflow / f"user_profile/{conv_cfg.workflow_id}.json", 'r') as f:
            user_profiles = json.load(f)
            selected_up = user_profiles[conv_cfg.user_profile_id]
        st.markdown(f"### User Profile")
        with st.expander("Details"):
            st.write(selected_up)
        
        # 4. show the judge results
        st.markdown(f"### Judge Results")
        judge_res = db.query_evaluations({"conversation_id": conversation_id})
        if len(judge_res) == 0:
            st.write("No evaluation results found!")
        else:
            with st.expander("Details"):
                st.write(judge_res[0])
        
        # 5. show the utterance infors
        utterance_ids = df['utterance_id'].unique()
        with st.sidebar: 
            selected_utterance_id = st.selectbox(
                "3️⃣ Select utterance_id", options=utterance_ids)
    
        st.markdown(f"### Details of `utterance_id={selected_utterance_id}`")
        with st.expander("Details"):
            if selected_utterance_id is not None:
                selected_row = df[df['utterance_id'] == selected_utterance_id].iloc[0]
                st.write(selected_row.to_dict())


