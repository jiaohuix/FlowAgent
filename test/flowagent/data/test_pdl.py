# %%
from flowagent.data import PDL
pdl = PDL.load_from_file("/work/huabu/dataset/PDL/pdl/000.yaml")
# %%
print(pdl.to_str_wo_api())
# %%
