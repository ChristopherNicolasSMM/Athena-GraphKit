import base64
import io
import json
import unittest
import zipfile
from mcp_server import list_themes, render_diagram, prepare_documentation

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg==')

class McpTests(unittest.TestCase):
    def test_themes(self):
        self.assertEqual(list_themes()[0]['id'],'dark')
    def test_unsupported(self):
        with self.assertRaises(ValueError):render_diagram('sequenceDiagram\n A->>B: Hi')
    def test_render(self):
        r=render_diagram('flowchart LR\n A[Início] --> B[Fim]')
        self.assertTrue(base64.b64decode(r['base64']).lstrip().startswith(b'<?xml') or b'<svg' in base64.b64decode(r['base64']))
    def test_corporativo(self):
        r=prepare_documentation('# Doc\n{{diagram:fluxo}}',{'fluxo':base64.b64encode(PNG).decode()})
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(r['base64']))) as z:
            self.assertIn('imagens/fluxo.png',z.namelist())
            self.assertIn('![fluxo]',z.read('documento_athena.md').decode())
