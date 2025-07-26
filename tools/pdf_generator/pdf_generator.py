# tools/pdf_generator/pdf_generator.py
"""
Geração de PDF (exemplo simplificado). Modular para manter dependências (reportlab) isoladas.
"""
from langchain.tools import BaseTool
from reportlab.pdfgen import canvas


class PDFGeneratorTool(BaseTool):
    name = "pdf_generator"
    description = "Gera um PDF simples com texto passado pelo usuário."

    def _run(self, text: str) -> str:
        file_name = "output.pdf"
        c = canvas.Canvas(file_name)
        c.drawString(72, 720, text)
        c.save()
        return f"PDF salvo em {file_name}"

    async def _arun(self, text: str) -> str:
        raise NotImplementedError("Versão async não implementada.")
