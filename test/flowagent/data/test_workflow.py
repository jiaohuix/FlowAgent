# %%
from flowagent.data import DataManager, Workflow, WorkflowType, Config

cfg = Config.from_yaml(DataManager.normalize_config_name('default.yaml'))
cfg.workflow_dataset = "PDL"
cfg.user_profile_id = 0

workflow = Workflow(cfg)
print(workflow.to_str())
# print(workflow.pdl)

# %%
from flowagent.data.user_profile import OOWIntention
import yaml
yaml_file = "/work/huabu/dataset/meta/oow.yaml"
with open(yaml_file, 'r') as file:
    data = yaml.safe_load(file)
intention = OOWIntention.from_dict(data[0])
# %%
