"""
Ferramentas triviais usadas pelo agente.
Todas síncronas e sem dependências externas.
"""

from langchain.tools import tool
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


@tool
def EchoTool(text: str) -> str:
    """Repete exatamente o texto fornecido (útil para debug)."""
    return text


@tool
def CalculatorTool(expression: str) -> str:
    """
    Avalia expressões aritméticas simples.
    Ex.: "2 + 2 * (3 - 1)"
    """
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as exc:  # noqa: BLE001
        return f"Erro na expressão: {exc}"


@tool
def DateTimeTool(question: str) -> str:  # ← 1 único argumento obrigatório
    """
    Responde sobre hora, data ou ambos conforme a pergunta:
      • Se contiver "hora"  ➜ HH:MM:SS
      • Se contiver "data"  ➜ DD/MM/AAAA
      • Caso contrário      ➜ DD/MM/AAAA HH:MM:SS
    Usa fuso America/Sao_Paulo; faz fallback manual UTC-3 se tzdata faltar.
    """
    try:
        tz = ZoneInfo("America/Sao_Paulo")
    except Exception:                       # ZoneInfoNotFoundError
        tz = timezone(timedelta(hours=-3))  # fallback UTC-3

    now = datetime.now(tz=tz)

    q = question.lower()
    show_date = "data" in q
    show_time = "hora" in q or "horas" in q or "time" in q

    if show_time and not show_date:
        return now.strftime("%H:%M:%S")
    if show_date and not show_time:
        return now.strftime("%d/%m/%Y")
    # default: ambos
    return now.strftime("%d/%m/%Y %H:%M:%S")
