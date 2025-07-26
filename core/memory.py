"""
Módulo de memória de conversação.
Mantém uma janela de N mensagens para dar contexto ao LLM.
"""

import os
from langchain.memory import ConversationBufferWindowMemory

WINDOW_K = int(os.getenv("MEMORY_WINDOW_SIZE", 10))

window_memory = ConversationBufferWindowMemory(
    k=WINDOW_K,
    return_messages=True,
)
