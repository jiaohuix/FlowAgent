""" updated 240906
usage:
    python run_flowagent_exp.py --config=default.yaml --exp-version=default \
        --workflow-type=text \
        --user-mode=llm_profile --user-llm-name=gpt-4o \
        --bot-mode=react_bot --bot-llm-name=gpt-4o \
        --api-mode=llm --api-llm-name=gpt-4o \
        --user-template-fn=baselines/user_llm.jinja --bot-template-fn=baselines/flowbench.jinja \
        --conversation-turn-limit=20 --log-utterence-time --log-to-db
"""
import typer
from flowagent import Config, DataManager, Evaluator
from flowagent.data import WorkflowType, WorkflowTypeStr
from flowagent.roles import UserMode, BotMode, ApiMode

app = typer.Typer()

@app.command()
def run_exp(
    config: str = typer.Option("default.yaml", help="Configuration file"),
    workflow_dataset: str = typer.Option(None, help="Workflow dataset", case_sensitive=False),
    workflow_type: WorkflowTypeStr = typer.Option(None, help="Workflow type", case_sensitive=False),
    exp_version: str = typer.Option(None, help="Experiment version"),
    exp_mode: str = typer.Option(None, help="Experiment mode", case_sensitive=False),
    user_mode: UserMode = typer.Option(None, help="User mode", case_sensitive=False), # type: ignore
    user_llm_name: str = typer.Option(None, help="User LLM name"),
    user_template_fn: str = typer.Option(None, help="User template filename"),
    bot_mode: BotMode = typer.Option(None, help="Bot mode", case_sensitive=False), # type: ignore
    bot_template_fn: str = typer.Option(None, help="Bot template filename"),
    bot_llm_name: str = typer.Option(None, help="Bot LLM name"),
    api_mode: ApiMode = typer.Option(None, help="API mode", case_sensitive=False), # type: ignore
    api_llm_name: str = typer.Option(None, help="API LLM name"),
    conversation_turn_limit: int = typer.Option(None, help="Conversation turn limit"),
    log_utterence_time: bool = typer.Option(None, help="Log utterance time"),
    log_to_db: bool = typer.Option(None, help="Log to DB"),
    simulate_num_persona: int = typer.Option(None, help="Simulate num persona"),
    simulate_max_workers: int = typer.Option(None, help="Simulate max workers"),
):
    cfg = Config.from_yaml(DataManager.normalize_config_name(config))
    if workflow_dataset is not None: cfg.workflow_dataset = workflow_dataset
    if workflow_type is not None: cfg.workflow_type = workflow_type.value
    if exp_version is not None: cfg.exp_version = exp_version
    if exp_mode is not None: cfg.exp_mode = exp_mode
    if user_mode is not None: cfg.user_mode = user_mode.value
    if user_llm_name is not None: cfg.user_llm_name = user_llm_name
    if user_template_fn is not None: cfg.user_template_fn = user_template_fn
    if bot_mode is not None: cfg.bot_mode = bot_mode.value
    if bot_template_fn is not None: cfg.bot_template_fn = bot_template_fn
    if bot_llm_name is not None: cfg.bot_llm_name = bot_llm_name
    if api_mode is not None: cfg.api_mode = api_mode.value
    if api_llm_name is not None: cfg.api_llm_name = api_llm_name
    if conversation_turn_limit is not None: cfg.conversation_turn_limit = conversation_turn_limit
    if log_utterence_time is not None: cfg.log_utterence_time = log_utterence_time
    if log_to_db is not None: cfg.log_to_db = log_to_db
    if simulate_num_persona is not None: cfg.simulate_num_persona = simulate_num_persona
    if simulate_max_workers is not None: cfg.simulate_max_workers = simulate_max_workers

    controller = Evaluator(cfg)
    controller.main()

if __name__ == "__main__":
    app()
