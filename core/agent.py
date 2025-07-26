from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Annotated, List
from typing_extensions import TypedDict

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents import initialize_agent, AgentType
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langmem.short_term import SummarizationNode

from tools import EchoTool, CalculatorTool, DateTimeTool          # ← NEW
from core.rag import rag_service

# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("agent")

# ---------- Esquema de estado ----------
class State(TypedDict):
    messages: Annotated[List, add_messages]
    input: str
    rag_ctx: str
    context: dict

# ---------- Persona ----------
PERSONA = Path("agent/prompt.md").read_text(encoding="utf-8").strip()

# ---------- LLM principal ----------
llm = init_chat_model(
    os.getenv("GROQ_MODEL_NAME", "groq:llama-3.3-70b-versatile"),
    temperature=float(os.getenv("GROQ_TEMPERATURE", 0.7)),
    max_tokens=int(os.getenv("GROQ_MAX_TOKENS", 1024)),
    groq_api_key=os.environ["GROQ_API_KEY"],
)

# ---------- Ferramentas básicas ----------
TOOLS = [EchoTool, CalculatorTool, DateTimeTool]

agent_executor = initialize_agent(
    tools=TOOLS,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=False,
    max_iterations=3,             # ← NOVO
    early_stopping_method="force" # ← NOVO
)

# ---------- Nós ----------
def node_rag(state: State) -> State:
    query = state["input"]
    state["rag_ctx"] = rag_service.get_context(query) if rag_service else ""
    return state


def node_format(state: State) -> State:
    """Adiciona persona + pergunta com contexto RAG ao histórico."""
    if not state["messages"]:
        state["messages"].append(SystemMessage(content=PERSONA))

    user_msg = f'{state["input"]}\n\n### CONTEXTO\n{state["rag_ctx"]}'
    state["messages"].append(HumanMessage(content=user_msg))
    return state


def safe_agent_call(prompt: str) -> str:
    """
    Executa o agente LangChain (LLM + tools) capturando exceções.
    Se o modelo ou a tool falharem, devolve aviso ao usuário.
    """
    try:
        return agent_executor.run(prompt).strip()
    except Exception as exc:  # noqa: BLE001
        log.error("Falha no agente/tools: %s", exc, exc_info=True)
        return "⚠️ Desculpe, ocorreu um erro ao usar as ferramentas. Tente novamente."


def node_llm_or_tool(state: State) -> State:
    """
    Decide automaticamente: LLM puro ou chamada de tool.
    Zero-shot ReAct do LangChain cuida da escolha.
    """
    prompt = state["messages"][-1].content  # última mensagem do usuário com contexto
    response_text = safe_agent_call(prompt)
    state["messages"].append(AIMessage(content=response_text))
    return state


# ---------- Memória – LangMem ----------
summarization_model = llm.bind(max_tokens=128)
summarize_node = SummarizationNode(
    model=summarization_model,
    max_tokens=int(os.getenv("GROQ_MAX_TOKENS", 1024)),
    max_summary_tokens=128,
    input_messages_key="messages",
    output_messages_key="messages",
)

# ---------- Grafo ----------
builder = StateGraph(State)
builder.add_node("rag", node_rag)
builder.add_node("format", node_format)
builder.add_node("llm_or_tool", node_llm_or_tool)     # ← NEW
builder.add_node("summarize", summarize_node)

builder.add_edge(START, "rag")
builder.add_edge("rag", "format")
builder.add_edge("format", "llm_or_tool")
builder.add_edge("llm_or_tool", "summarize")
builder.add_edge("summarize", END)

graph = builder.compile()

# ---------- Wrapper ----------
class ConversationalAgent:
    """Agente com LangGraph + LangChain + LangMem + Tools."""

    def __init__(self) -> None:
        self._running_summary = None
        self._history: List = []

        summarize_node.model = llm  # garante que memória use o mesmo modelo

    def conversar(self, text: str) -> str:
        init_state: State = {
            "messages": self._history,
            "input": text,
            "rag_ctx": "",
            "context": {"running_summary": self._running_summary} if self._running_summary else {},
        }

        final = graph.invoke(init_state)

        self._history = final["messages"]
        self._running_summary = final["context"].get("running_summary") if "context" in final else None

        return self._history[-1].content

    def get_status(self) -> dict:
        return {
            "llm_model": llm.model_name,
            "rag_available": rag_service.is_available() if rag_service else False,
            "has_memory": self._running_summary is not None,
            "tools": [t.name for t in TOOLS],
        }
