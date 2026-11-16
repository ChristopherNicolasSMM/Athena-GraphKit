import base64
import json
import tempfile
import unittest
from pathlib import Path
import portal

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg==')

class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.original=portal.WORKSPACE
        portal.WORKSPACE=Path(self.temp.name)
        self.client=portal.app.test_client()
    def tearDown(self):
        portal.WORKSPACE=self.original
        self.temp.cleanup()
    def test_project_crud(self):
        r=self.client.post('/api/projects',json={'id':'teste','title':'Teste'})
        self.assertEqual(r.status_code,201)
        project=r.get_json()
        self.assertEqual(len(project['diagrams']),1)
        self.assertEqual(self.client.get('/api/projects/teste').status_code,200)
        project['markdown']='# Documento\n\n{{diagram:fluxo}}'
        self.assertEqual(self.client.put('/api/projects/teste',json=project).status_code,200)
        self.assertEqual(self.client.delete('/api/projects/teste').status_code,200)
    def test_reject_invalid_id(self):
        self.assertEqual(self.client.post('/api/projects',json={'id':'../bad'}).status_code,400)
    def test_export(self):
        p=portal.default_project('teste')
        img='data:image/png;base64,'+base64.b64encode(PNG).decode()
        r=self.client.post('/api/export/documentation',json={'project':p,'images':{'fluxo':img}})
        self.assertEqual(r.status_code,200)
        import io,zipfile
        with zipfile.ZipFile(io.BytesIO(r.data)) as z:
            self.assertIn('imagens/fluxo.png',z.namelist())
            self.assertIn('![Integração SAP](imagens/fluxo.png)',z.read('documento_athena.md').decode())
    def test_import_rejects_project_without_id(self):
        project = portal.default_project('teste')
        del project['id']
        self.assertEqual(self.client.post('/api/projects/import', json=project).status_code, 400)

    def test_import_rejects_invalid_nodes_and_edges(self):
        project = portal.default_project('teste')
        diagram = project['diagrams'][0]
        diagram['nodes'].append(None)
        self.assertEqual(self.client.post('/api/projects/import', json=project).status_code, 400)
        diagram['nodes'].pop()
        diagram['edges'][0]['to'] = 'ausente'
        self.assertEqual(self.client.post('/api/projects/import', json=project).status_code, 400)

    def test_png_accepts_bounded_embedded_image_and_rejects_external_url(self):
        encoded = base64.b64encode(PNG).decode()
        self.assertTrue(portal.embedded_png('data:image/png;base64,' + encoded))
        self.assertFalse(portal.embedded_png('data:image/png;base64,invalid'))
        svg = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><image href="https://example.invalid/icon.png"/></svg>'
        response = self.client.post('/api/export/png', json={'svg': svg})
        self.assertEqual(response.status_code, 422)

    def test_missing_image(self):
        self.assertEqual(self.client.post('/api/export/documentation',json={'project':portal.default_project(),'images':{}}).status_code,400)

if __name__=='__main__': unittest.main()
