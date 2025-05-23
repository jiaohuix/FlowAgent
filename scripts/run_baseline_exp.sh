PROJECT_PATH="$(git rev-parse --show-toplevel)"
cd "${PROJECT_PATH}"
source .venv/bin/activate
cd src
python run_flowagent_exp.py --config=default.yaml --exp-version=default \
    --workflow-type=code \
    --user-mode=llm_profile --user-llm-name=gpt-4o \
    --bot-mode=react_bot --bot-llm-name=gpt-4o \
    --api-mode=llm --api-llm-name=gpt-4o \
    --user-template-fn=flowagent/user_llm.jinja --bot-template-fn=baselines/flowbench.jinja \
    --conversation-turn-limit=20 --log-utterence-time --log-to-db
