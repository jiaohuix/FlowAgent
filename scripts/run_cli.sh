PROJECT_PATH="$(git rev-parse --show-toplevel)"
cd "${PROJECT_PATH}"
source .venv/bin/activate
cd src
python run_flowagent_cli.py --config=default.yaml --exp-version=defaultss --exp-mode=session \
    --workflow-type=pdl --workflow-id=000 \
    --user-mode=manual --user-llm-name=gpt-4o --user-profile-id=0 \
    --bot-mode=pdl_bot --bot-llm-name=gpt-4o \
    --api-mode=llm --api-llm-name=gpt-4o \
    --bot-template-fn=flowagent/bot_pdl.jinja \
    --conversation-turn-limit=20 --log-utterence-time --log-to-db
