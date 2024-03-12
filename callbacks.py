from langchain.callbacks.base import BaseCallbackHandler
import tiktoken
from typing import Any
from langchain.schema import LLMResult


class CustomTokensHandler(BaseCallbackHandler):

    def __init__(self) -> None:
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        encoding = tiktoken.get_encoding("cl100k_base")
        prompts_string = "".join(prompts)
        num_tokens = len(encoding.encode(prompts_string))
        self.prompt_tokens += num_tokens
        # print("Called LLM. Prompt tokens: ", num_tokens)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when chain ends running."""
        text_response = response.generations[0][0].text
        encoding = tiktoken.get_encoding("cl100k_base")
        response_string = len(encoding.encode(text_response))
        self.completion_tokens += response_string
        self.total_tokens = self.prompt_tokens + self.completion_tokens
