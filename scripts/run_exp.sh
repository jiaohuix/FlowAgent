PROJECT_PATH="$(git rev-parse --show-toplevel)"
cd "${PROJECT_PATH}"
source .venv/bin/activate
cd src
python run_flowagent_exp.py --config=default.yaml --exp-version=default \
    --workflow-type=pdl \
    --user-mode=llm_profile --user-llm-name=gpt-4o \
    --bot-mode=pdl_bot --bot-llm-name=gpt-4o \
    --api-mode=llm --api-llm-name=gpt-4o \
    --user-template-fn=flowagent/user_llm.jinja --bot-template-fn=flowagent/bot_pdl.jinja \
    --conversation-turn-limit=20 --log-utterence-time --log-to-db
