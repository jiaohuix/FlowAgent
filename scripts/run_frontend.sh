PROJECT_PATH="$(git rev-parse --show-toplevel)"
cd "${PROJECT_PATH}"
source .venv/bin/activate
cd src
streamlit run run_flowagent_ui.py --server.address 0.0.0.0 --server.port=8502 -- --config=default.yaml
