# init_client, LLM_CFG
import os, datetime, traceback, functools
from typing import List, Dict, Optional, Union
from easonsi.llm.openai_client import OpenAIClient

_IP_01 = "9.91.12.44:8000"
_IP_02 = "9.91.0.28:13000"
LLM_CFG = {
    "custom": {
        "model_name": "Qwen2-72B-Instruct",
        "base_url": f"http://{_IP_01}/v1/",
        "api_key": "xxx",
    },
    "Qwen2-72B": {
        "model_name": "Qwen2-72B-Instruct",
        "base_url": f"http://{_IP_01}/v1/",
        "api_key": "xxx",
    },
    "v0729-Llama3_1-70B": {
        "model_name": "Infinity-Instruct-7M-0729-Llama3_1-70B",
        "base_url": f"http://{_IP_02}/v1/",
        "api_key": "xxx",
    },
    "v0729-Qwen2-7B": {
        "model_name": "Infinity-Instruct-7M-0729-Qwen2-7B-ianExp",
        "base_url": f"http://{_IP_02}/v1/",
        "api_key": "xxx",
    },
}
def add_openai_models():
    global LLM_CFG
    model_list = [
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4",
        "claude-3-haiku-20240307", "claude-3-5-sonnet-20240620", "claude-3-opus-20240229"
    ]
    for model in model_list:
        assert model not in LLM_CFG, f"{model} already in LLM_CFG"
        LLM_CFG[model] = {
            "model_name": model,
            "base_url": os.getenv("OPENAI_PROXY_BASE_URL"),
            "api_key": os.getenv("OPENAI_PROXY_API_KEY"),
        }

# set model alias!!
add_openai_models()


def init_client(llm_cfg:Dict):
    # global client
    base_url = os.getenv("OPENAI_PROXY_BASE_URL") if llm_cfg.get("base_url") is None else llm_cfg["base_url"]
    api_key = os.getenv("OPENAI_PROXY_API_KEY") if llm_cfg.get("api_key") is None else llm_cfg["api_key"]
    model_name = llm_cfg.get("model_name", "gpt-4o")
    client = OpenAIClient(
        model_name=model_name, base_url=base_url, api_key=api_key, is_sn=llm_cfg.get("is_sn", False)
    )
    return client

