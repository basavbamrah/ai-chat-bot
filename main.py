from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain.tools.retriever import create_retriever_tool
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import (
    ConversationBufferWindowMemory,
    ChatMessageHistory,
)
from callbacks import CustomTokensHandler
from prompts import prefix, format_instructions, suffix
from langchain.schema import HumanMessage, AIMessage
import os
from typing import Optional

_ = load_dotenv()


def create_memory_buffer(
    msg_lst: list = [], input: str = "input", output: Optional[str] = None, k: int = 10
) -> ConversationBufferWindowMemory:

    print("=========== length ===========")
    print(len(msg_lst))
    if len(msg_lst) == 0:
        return ConversationBufferWindowMemory(
            k=k,
            memory_key="chat_history",
            input_key=input,
            output_key=output,
            return_messages=True,
        )

    else:
        message = []
        if len(msg_lst) % 2 != 0:
            raise Exception("Length of list should be even")
        for i in range(len(msg_lst)):
            if i == 0 or i % 2 == 0:
                message.append(HumanMessage(content=msg_lst[i]))
            else:
                message.append(AIMessage(content=msg_lst[i]))

        return ConversationBufferWindowMemory(
            k=k,
            memory_key="chat_history",
            input_key=input,
            output_key=output,
            chat_memory=ChatMessageHistory(messages=message[-k:]),
            return_messages=True,
        )


def load_create_embeddings()->FAISS:
    if os.path.exists("embeddings"):
        index = FAISS.load_local("embeddings", OpenAIEmbeddings())
        return index
    else:
        loader = PyPDFLoader("Documents/Get Catalyzed Knowledge Base (updated).pdf")
        pages = loader.load_and_split()
        index = FAISS.from_documents(pages, OpenAIEmbeddings())
        index.save_local("embeddings")
        return index

def _create_agent(llm, memory, input_variables, **kwargs)-> AgentExecutor:
    prompt = PromptTemplate(
        template=prefix + format_instructions + suffix,
        input_variables=input_variables,
    )
    tools = _create_tools()
    agent = create_react_agent(
        llm,
        tools=[tools],
        prompt=prompt,
        **kwargs,
    )
    return AgentExecutor(
        agent=agent,
        tools=[tools],
        verbose=True,
        memory=memory,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )


def _create_tools()->create_retriever_tool:
    index = load_create_embeddings()
    return create_retriever_tool(
        retriever=index.as_retriever(), name="retriever", description="retriever tool"
    )


class GetCatalyzedAgent:
    def __init__(self, memory_lst: list = []) -> None:
        self.memory = create_memory_buffer(
            memory_lst, input="input", output="output", k=10
        )
        self.handler = CustomTokensHandler()
        self.llm = ChatOpenAI(
            model_name="gpt-4-1106-preview", temperature=0, callbacks=[self.handler]
        )
        input_variables = [
            "agent_scratchpad",
            "input",
            "tool_names",
            "tools",
            "chat_history",
        ]
        self.agent = _create_agent(
            llm=self.llm,
            memory=self.memory,
            input_variables=input_variables,
        )

    def ask_question(self, query: str) -> dict:
        answer = self.agent.invoke({"input": query})
        answer["token"] = {
            "prompt": self.handler.prompt_tokens,
            "completion": self.handler.completion_tokens,
            "total": self.handler.total_tokens,
        }

        if answer["output"].lower().startswith("agent stopped"):
            answer["output"] = "No answer found, please again"

        return answer
