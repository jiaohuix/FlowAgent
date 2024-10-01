import re, yaml
from dataclasses import dataclass, asdict, field


class MyDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

    def represent_scalar(self, tag, value, style=None):
        if style is None:
            if '\n' in value:
                style = '|'
        return super(MyDumper, self).represent_scalar(tag, value, style)


@dataclass
class PDL:
    PDL_str: str = None
    
    name: str = ""
    desc: str = ""
    desc_detail: str = ""
    apis: list = field(default_factory=list)
    slots: list = field(default_factory=list)
    answers: list = field(default_factory=list)
    procedure: str = ""      # the core logic of the taskflow
    
    version: str = "v2"
    
    def __init__(self, PDL_str):
        self.PDL_str = PDL_str

    @classmethod
    def load_from_str(cls, PDL_str):
        instance = cls(PDL_str)
        instance.parse_PDL_str()
        return instance
    @classmethod
    def load_from_file(cls, file_path):
        with open(file_path, 'r') as f:
            PDL_str = f.read().strip()
        return cls.load_from_str(PDL_str)
    
    def parse_PDL_str(self):
        ob = yaml.load(self.PDL_str, Loader=yaml.FullLoader)
        self.name = ob["Name"]
        self.desc = ob["Desc"]
        self.desc_detail = ob.get("Detailed_desc", "")
        self.apis = ob.get("APIs", [])
        self.slots = ob["SLOTs"]
        self.answers = ob["ANSWERs"]
        self.procedure = ob["PDL"]

    def to_str(self):
        return self.PDL_str
    def to_str_wo_api(self):
        infos = asdict(self)
        selected_keys = ["name", "desc", "desc_detail", "slots", "answers", "procedure"]
        infos_selected = {k: infos[k] for k in selected_keys}
        return yaml.dump(infos_selected, sort_keys=False, Dumper=MyDumper, default_flow_style=False)
        
    def __repr__(self):
        return self.PDL_str