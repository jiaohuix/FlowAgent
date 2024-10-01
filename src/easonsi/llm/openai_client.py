""" 
https://github.com/openai/openai-python
"""

import sys, os, json, re, time, requests, yaml, openai, traceback
from openai.types.chat import ChatCompletion
from tqdm import tqdm
# from diskcache import Cache
# from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple, Union

class Formater:
    """ 用于从字符串中提取信息, 比如规范GPT输出的结果 """
    @staticmethod
    def re_backtick(text):
        # 设置 ? 非贪婪模式
        # re.DOTALL 使得 . 可以匹配换行符
        pattern = re.compile(r"```(.*?)```", re.DOTALL)
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        else:
            return None

    @staticmethod
    def remove_code_prefix(text, type="json"):
        pattern_code = re.compile(r"```(.*?)```", re.DOTALL)
        match = pattern_code.search(text)
        if match:
            text = match.group(0).strip()
        else:
            return text

        pattern = re.compile(f"```{type}\n?", re.IGNORECASE)
        text = pattern.sub("", text)
        pattern = re.compile(f"```", re.DOTALL)
        text = pattern.sub("", text)
        return text.strip()

    @staticmethod
    def parse_codeblock(text:str, type="json") -> str:
        pattern = re.compile(f"```{type}\n?(.*?)```", re.DOTALL)
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        else:
            return text

    @staticmethod
    def parse_llm_output_json(text:str) -> Dict:
        try:
            json_str = Formater.parse_codeblock(text, type="json")
            parsed = json.loads(json_str)
            return parsed
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e), "text": text}

    @staticmethod
    def parse_llm_output_yaml(text:str) -> Dict:
        try:
            yaml_str = Formater.parse_codeblock(text, type="yaml")
            parsed = yaml.safe_load(yaml_str)
            return parsed
        except Exception as e:
            print(f"[ERROR] parse_llm_output_yaml: {e}\n  {text}")
            return {"error": str(e), "text": text}

def stream_generator(response, is_openai=True):
    if is_openai:
        for chunk in response:
            yield chunk.choices[0].delta.content or ""
    else:
        ret = ""
        for chunk in response.iter_lines():
            chunk_ret = json.loads(chunk)['response'].strip() 
            # yield json.loads(chunk)['response'].strip() or ""
            yield chunk_ret[len(ret):]
            ret = chunk_ret

class OpenAIClient:
    base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o"
    client: openai.OpenAI = None
    temperature: float = 0.5
    max_tokens: int = 4096

    use_cache: bool = False
    retries: int = 3
    backoff_factor: float = 0.5
    n_thread:int = 5
    
    def __init__(
        self, model_name:str=None, temperature:float=None, max_tokens:int=None,
        base_url=f"https://api.openai.com/v1", api_key=None, print_url=False, 
    ):
        if not api_key:
            print(f"[WARNING] api_key is None, please set it in the environment variable (OPENAI_API_KEY) or pass it as a parameter.")
        if print_url:
            print(f"[INFO] base_url: {base_url}")
        self.base_url = base_url
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        if model_name: self.model_name = model_name
        if temperature: self.temperature = temperature
        if max_tokens: self.max_tokens = max_tokens

    def query_one_raw(self, text, **args) -> ChatCompletion:
        model = self.model_name
        if "model" in args: 
            model = args.pop("model")
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": text}],
            model=model,
            **args
        )
        return chat_completion

    def query_one(self, query, return_model=False, return_usage=False, **args) -> Union[str, Tuple[str, ...]]:
        # _key = f"{self.model_name}-{text}"
        # if self.use_cache and _key in cache:
        #     return cache.get(_key)
        if "model" not in args: args["model"] = self.model_name
        if "max_tokens" not in args: args["max_tokens"] = self.max_tokens
        if "temperature" not in args: args["temperature"] = self.temperature
        for attempt in range(self.retries):
            try:
                chat_completion: ChatCompletion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": query}],
                    **args
                )
                # cache.set(_key, res)
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                time.sleep(self.backoff_factor * (2 ** attempt))
        else:
            raise Exception(f"Failed to get response after {self.retries} attempts.")
        if not return_model and not return_usage:
            return chat_completion.choices[0].message.content
        res = (chat_completion.choices[0].message.content, )
        if return_usage: return_model = True
        if return_model:
            res = res + (chat_completion.model, )
            if return_usage: res = res + (chat_completion.usage.to_dict(), )
        return res
    
    def query_one_stream_generator(self, text, stop=None) -> None:
        response = self.client.chat.completions.create(
            messages=[{ "role": "user", "content": text,}],
            model=self.model_name,
            temperature=self.temperature,
            stream=True,
            stop=stop
        )
        stream = stream_generator(response, is_openai=True)
        return stream
    
    def query_one_stream(self, text, stop=None, print_stream=True) -> None:
        res = ""
        stream = self.query_one_stream_generator(text, stop)
        for text in stream:
            res += text
            if print_stream:
                print(f"\033[90m{text}\033[0m", end="")
        if print_stream: print("\n")
        return res

