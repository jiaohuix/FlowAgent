import yaml, json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from ..data import DBManager, Config, DataManager, WorkflowType


def build_workflow_infos(workflow_infos) -> pd.DataFrame:
    data = []
    for k,v in workflow_infos.items():
        v['workflow_id'] = k
        data.append(v)
    st.session_state.df_workflow_infos = pd.DataFrame(data).set_index('workflow_id')

def refresh_dataset():
    # 1. update config
    _cfg:Config = st.session_state.cfg
    _cfg.workflow_dataset = st.session_state.selected_workflow_dataset
    # 2. update data_manager
    _dm:DataManager = st.session_state.data_manager
    _dm.refresh_config(_cfg)
    # 3. 
    build_workflow_infos(_dm.workflow_infos)


def show_data_page():
    # ------------------ session_state --------------------
    data_manager:DataManager = st.session_state.data_manager
    build_workflow_infos(data_manager.workflow_infos)

    if "db" not in st.session_state:
        assert 'cfg' in st.session_state
        _cfg: Config = st.session_state.cfg
        st.session_state.db = DBManager(_cfg.db_uri, _cfg.db_name, _cfg.db_message_collection_name)
    db:DBManager = st.session_state.db

    # ------------------ sidebar --------------------
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.selectbox(
            "1️⃣ Select data", 
            options=data_manager.get_workflow_dataset_names(),
            key="selected_workflow_dataset",
            on_change=refresh_dataset,
            
        )
    with col2: 
        st.selectbox(
            "Workflow ID",
            st.session_state.df_workflow_infos.index, index=1,
            key="selected_workflow_id"
        )
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        show_toolbox = st.checkbox("Show Toolbox")
        show_text = st.checkbox("Show Text")
    with col2:
        show_code = st.checkbox("Show Code")
        show_flowchart = st.checkbox("Show Flowchart")

    with open(data_manager.DIR_data_workflow / f"user_profile/{st.session_state.selected_workflow_id}.json", 'r') as f:
        user_profiles = json.load(f)
    st.sidebar.selectbox(
        "2️⃣ Secect User Profile ID",
        list(range(len(user_profiles))),
        key="selected_user_profile_id"
    )
    
    ava_workflow_types = ["ALL"] + [wt.workflow_type for wt in WorkflowType]
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        selected_workflow_type = st.selectbox(
            "3️⃣ Select Workflow Type",
            ava_workflow_types
        )
    with col2:
        refresh = st.button("Refresh") # utilize the feature of streamlit to refresh
    col21, col22 = st.sidebar.columns(2)
    with col21:
        use_current_workflow = st.checkbox("Use Correct Workflow")
    with col22:
        use_current_user_profile = st.checkbox("Use Current User Profile")
    customized_query = st.sidebar.text_input(
        "Customized Mongo Query :warning:",
    )

    # ------------------ main --------------------
    # 1. show workflow_infos
    st.markdown("### Workflow Infos")
    with st.expander("Show Workflow Infos", expanded=True):
        st.dataframe(st.session_state.df_workflow_infos)

    # 2. show workflow details
    st.markdown(f"### Details of `{st.session_state.selected_workflow_id}`")
    if show_toolbox:
        with open(data_manager.DIR_data_workflow / f"tools/{st.session_state.selected_workflow_id}.yaml", 'r') as f:
            toolbox = yaml.safe_load(f)
            st.markdown("#### Toolbox")
            st.write(toolbox)
    if show_text:
        _type = WorkflowType.TEXT
        with open(data_manager.DIR_data_workflow / f"{_type.subdir}/{st.session_state.selected_workflow_id}{_type.suffix}", 'r') as f:
            workflow = f.read().strip()
            st.markdown("#### Text")
            st.write(workflow)
    if show_code:
        _type = WorkflowType.CODE
        with open(data_manager.DIR_data_workflow / f"{_type.subdir}/{st.session_state.selected_workflow_id}{_type.suffix}", 'r') as f:
            workflow = f.read().strip()
            st.markdown("#### Code")
            st.code(workflow, language='python')
    if show_flowchart:
        _type = WorkflowType.FLOWCHART
        with open(data_manager.DIR_data_workflow / f"{_type.subdir}/{st.session_state.selected_workflow_id}{_type.suffix}", 'r') as f:
            workflow = f.read().strip()
            st.markdown("#### Flowchart")
            # workflow = f"```mermaid\n{workflow}\n```"
            # st.markdown(workflow, unsafe_allow_html=True)
            html_code = get_html_code(workflow)
            components.html(html_code, height=500, scrolling=True)
    
    # 3. show user profiles
    st.markdown("### User Profiles")
    with st.expander("Show User Profiles", expanded=False):
        st.write(user_profiles[st.session_state.selected_user_profile_id])

    # 4. show run experiemnts
    st.markdown("### Run Experiments")
    query = {
        'workflow_dataset': st.session_state.selected_workflow_dataset,
    }
    if use_current_workflow: query['workflow_id'] = st.session_state.selected_workflow_id
    if use_current_user_profile: query['user_profile_id'] = st.session_state.selected_user_profile_id
    if selected_workflow_type!="ALL": query["workflow_type"] = selected_workflow_type
    if customized_query:
        try:
            query.update(json.loads(customized_query))
        except Exception as e:
            st.sidebar.error(e)
    st.sidebar.info(f"current query: {query}")
    run_experiments = db.query_run_experiments(query)
    if len(run_experiments) == 0:
        st.warning("No experiment found")
    else:
        df = pd.DataFrame(run_experiments).drop(columns=['_id']).set_index('conversation_id')
        st.dataframe(df)


def get_html_code(mermaid_code: str):
    return \
"""
<!DOCTYPE html>
<html>
<head>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true }});
  </script>
</head>
<body>
  <div class="mermaid">
    {mermaid_code}
  </div>
</body>
</html>
""".format(mermaid_code=mermaid_code)