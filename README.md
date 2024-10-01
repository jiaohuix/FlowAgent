

## run

```bash
PROJECT_PATH=<path to project>
cd ${PROJECT_PATH}/src
python run_flowagent_cli.py --config=default.yaml --exp-version=default --exp-mode=turn \
    --workflow-type=text --workflow-id=000 \
    --user-mode=llm_profile --user-llm-name=gpt-4o --user-profile-id=0 \
    --bot-mode=react_bot --bot-llm-name=gpt-4o \
    --api-mode=llm --api-llm-name=gpt-4o \
    --user-template-fn=baselines/user_llm.jinja --bot-template-fn=baselines/flowbench.jinja \
    --conversation-turn-limit=20 --log-utterence-time --log-to-db
```

## templates

see `src/utils/templates/flowagent`
