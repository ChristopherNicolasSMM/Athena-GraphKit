import tempfile
import unittest
from pathlib import Path
from athena import AthenaGraphKit
from core.parser import interpretar

class TestAthena(unittest.TestCase):
    def test_texto_svg(self):
        with tempfile.TemporaryDirectory() as pasta:
            resultado = AthenaGraphKit().gerar_texto("flowchart LR\n A[Portal] --> B[SAP]", Path(pasta)/"teste")
            self.assertTrue(resultado.caminho.exists())
            self.assertIn("<svg", resultado.caminho.read_text(encoding="utf-8"))

    def test_markdown_multiplos(self):
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta)
            entrada = base / "entrada.md"
            entrada.write_text("# Exemplo\n```mermaid\nflowchart LR\n A --> B\n```\n```mermaid\nflowchart TB\n X --> Y\n```", encoding="utf-8")
            resultados = AthenaGraphKit().gerar_arquivo(entrada, base / "out")
            self.assertEqual(len(resultados), 2)
            self.assertTrue(all(r.caminho.exists() for r in resultados))

    def test_temas(self):
        for nome in ("corporativo", "sap_fiori", "dark"):
            self.assertEqual(AthenaGraphKit(nome).nome_tema, nome)

    def test_formas_e_direcao_do_editor_visual(self):
        code = 'flowchart TB\n A("Tarefa") <--> D[/"Documento"/]\n D --> C[("Dados")]'
        parsed = interpretar(code)
        self.assertEqual(parsed.direcao, "TB")
        self.assertEqual([node["tipo"] for node in parsed.nos.values()],
                         ["ellipse", "parallelogram", "cylinder"])
        self.assertEqual(parsed.arestas[0][2], "<-->")
        with tempfile.TemporaryDirectory() as pasta:
            result = AthenaGraphKit().gerar_texto(code, Path(pasta) / "figura")
            svg = result.caminho.read_text(encoding="utf-8")
            self.assertIn("Tarefa", svg)
            self.assertIn("Dados", svg)

    def test_invalido(self):
        with self.assertRaises(ValueError):
            AthenaGraphKit().gerar_texto("sequenceDiagram\n A->>B: oi", Path("nao_gera"))

if __name__ == "__main__":
    unittest.main()
