PROJECT_PATH="$(git rev-parse --show-toplevel)"
cd "${PROJECT_PATH}"
source .venv/bin/activate

# MODEL_NAME="gpt-4o"
MODEL_NAME="Qwen/Qwen3-8B"


cd src
python run_flowagent_cli.py --config=default.yaml --exp-version=defaultss --exp-mode=session \
    --workflow-type=pdl --workflow-id=000 \
    --user-mode=manual --user-llm-name=$MODEL_NAME --user-profile-id=0 \
    --bot-mode=pdl_bot --bot-llm-name=$MODEL_NAME \
    --api-mode=llm --api-llm-name=$MODEL_NAME \
    --bot-template-fn=flowagent/bot_pdl.jinja \
    --conversation-turn-limit=20 --log-utterence-time  --no-log-to-db

#no-log-to-db 关闭mongodb
