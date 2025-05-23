import typer
from flowagent import Config, DataManager, FlowagentController
from flowagent.data import WorkflowType, WorkflowTypeStr
from flowagent.roles import UserMode, BotMode, ApiMode

app = typer.Typer()

@app.command()
def run_cli(
    config: str = typer.Option("default.yaml", help="Configuration file"),
    workflow_dataset: str = typer.Option(None, help="Workflow dataset", case_sensitive=False),
    workflow_type: WorkflowTypeStr = typer.Option(None, help="Workflow type", case_sensitive=False),
    workflow_id: str = typer.Option(None, help="Workflow ID"),
    exp_version: str = typer.Option(None, help="Experiment version"),
    exp_mode: str = typer.Option(None, help="Experiment mode", case_sensitive=False),
    user_mode: UserMode = typer.Option(None, help="User mode", case_sensitive=False), # type: ignore
    user_llm_name: str = typer.Option(None, help="User LLM name"),
    user_template_fn: str = typer.Option(None, help="User template filename"),
    user_profile_id: int = typer.Option(None, help="User profile ID"),
    bot_mode: BotMode = typer.Option(None, help="Bot mode", case_sensitive=False), # type: ignore
    bot_template_fn: str = typer.Option(None, help="Bot template filename"),
    bot_llm_name: str = typer.Option(None, help="Bot LLM name"),
    api_mode: ApiMode = typer.Option(None, help="API mode", case_sensitive=False), # type: ignore
    api_llm_name: str = typer.Option(None, help="API LLM name"),
    conversation_turn_limit: int = typer.Option(None, help="Conversation turn limit"),
    log_utterence_time: bool = typer.Option(None, help="Log utterance time"),
    log_to_db: bool = typer.Option(None, help="Log to DB"),
):
    cfg = Config.from_yaml(DataManager.normalize_config_name(config))
    if workflow_dataset is not None: cfg.workflow_dataset = workflow_dataset
    if workflow_type is not None: cfg.workflow_type = workflow_type.value
    if workflow_id is not None: cfg.workflow_id = workflow_id
    if exp_version is not None: cfg.exp_version = exp_version
    if exp_mode is not None: cfg.exp_mode = exp_mode
    if user_mode is not None: cfg.user_mode = user_mode.value
    if user_llm_name is not None: cfg.user_llm_name = user_llm_name
    if user_template_fn is not None: cfg.user_template_fn = user_template_fn
    if user_profile_id is not None: cfg.user_profile_id = user_profile_id
    if bot_mode is not None: cfg.bot_mode = bot_mode.value
    if bot_template_fn is not None: cfg.bot_template_fn = bot_template_fn
    if bot_llm_name is not None: cfg.bot_llm_name = bot_llm_name
    if api_mode is not None: cfg.api_mode = api_mode.value
    if api_llm_name is not None: cfg.api_llm_name = api_llm_name
    if conversation_turn_limit is not None: cfg.conversation_turn_limit = conversation_turn_limit
    if log_utterence_time is not None: cfg.log_utterence_time = log_utterence_time
    if log_to_db is not None: cfg.log_to_db = log_to_db

    controller = FlowagentController(cfg)
    controller.start_conversation()

if __name__ == "__main__":
    app()
