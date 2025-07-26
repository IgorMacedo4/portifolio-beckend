"""
Main de demonstração (linha de comando).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis .env
load_dotenv()

# Ajusta PYTHONPATH para importar core
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import ConversationalAgent  # noqa: E402

def main() -> None:
    print("Agente mínimo LangGraph 0.3")
    agent = ConversationalAgent()
    print(f"Modelo: {agent.get_status()['llm_model']}")
    print()

    while True:
        user_input = input("Você: ").strip()
        if user_input.lower() in {"sair", "exit", "quit", "q"}:
            break
        resposta = agent.conversar(user_input)
        print(f"Alam: {resposta}\n")

if __name__ == "__main__":
    main()
