"""
Exemplo de ferramenta que chama um endpoint externo – separada para
facilitar testes, dependências e futuras extensões.
"""

import os
import requests
from langchain.tools import BaseTool, ToolException


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Busca rápida na Web via DuckDuckGo. "
        "Use quando precisar de dados públicos atualizados."
    )

    def _run(self, query: str) -> str:  # noqa: D401
        try:
            resp = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": query},
                timeout=10,
            )
            resp.raise_for_status()
        except Exception as exc:
            raise ToolException(f"Falha na busca web: {exc}") from exc

        # parse HTML simples (placeholder)
        return f"Resultados brutos: {resp.text[:500]}..."

    async def _arun(self, query: str) -> str:
        """Versão assíncrona opcional"""
        raise NotImplementedError("Versão async não implementada.")
