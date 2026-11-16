import io
import re
import runpy
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from athena_access.accounts import password_hash


class HostedAccessTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.outbox = []
        self.registrations = []
        module = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'portal.py'))
        self.app = module['configure_hosted']({
            'ATHENA_SECRET_KEY': 'testing-key-only-' * 4,
            'ATHENA_DATABASE': Path(self.directory.name) / 'test.sqlite3',
        }, reset_sender=lambda *message: self.outbox.append(message),
           registration_sender=lambda *message: self.registrations.append(message))
        self.app.testing = True
        self.password = 'original password with spaces'
        from athena_access import AccessStore
        self.store = AccessStore(Path(self.directory.name) / 'test.sqlite3')
        hashed = password_hash(self.password)
        with self.store.connect(write=True) as db:
            db.executemany('INSERT INTO users(email,password) VALUES (?,?)',
                           ((email, hashed) for email in ('owner@example.test','member@example.test','other@example.test')))
            db.execute("INSERT INTO organizations VALUES ('org','Organização')")
            db.execute("INSERT INTO groups VALUES ('dev','org','Desenvolvimento')")
            db.execute("INSERT INTO organization_members VALUES ('org',2)")
            db.execute("INSERT INTO group_members VALUES ('dev',2)")
        self.owner, self.member, self.other = (self.app.test_client() for _ in range(3))

    @staticmethod
    def request(client, path, *, method='GET', **kwargs):
        return client.open(path, method=method, base_url='https://localhost', **kwargs)

    def csrf(self, client, path='/'):
        response = self.request(client, path)
        return re.search(rb'(?:name="csrf-token" content|name="csrf" value)="([^"]+)"', response.data)[1].decode()

    def login(self, client, email, password=None):
        return self.request(client, '/conta/login', method='POST', data={
            'email': email + '@example.test', 'password': password or self.password,
            'csrf': self.csrf(client, '/conta/login'),
        })

    def mutate(self, client, path, *, method='POST', **kwargs):
        return self.request(client, path, method=method,
                            headers={'X-CSRF-Token': self.csrf(client)}, **kwargs)

    def grant(self, principal, target, role, diagram=''):
        return self.mutate(self.owner, '/compartilhamento/projeto/permissoes',
                           data={'principal': principal, 'target': target, 'role': role, 'diagram': diagram})

    def test_language_selection_persists_across_account_pages(self):
        response = self.request(self.other, '/conta/login?lang=en')
        self.assertIn(b'<html lang="en">', response.data)
        self.assertIn(b'aria-label="English" aria-current="true"', response.data)
        self.assertIn(b'Create account', self.request(self.other, '/conta/login').data)
        self.assertIn(b'Recover your password', self.request(self.other, '/conta/recuperar').data)
        self.assertIn(b'Invalid email or password.', self.login(self.other, 'other', 'wrong password').data)
        response = self.request(self.other, '/conta/login?lang=pt')
        self.assertIn(b'<html lang="pt-BR">', response.data)
        self.assertIn(b'Criar conta', self.request(self.other, '/conta/login').data)

    def test_registration_confirms_email_and_creates_an_isolated_account(self):
        self.assertEqual(self.login(self.owner, 'owner').status_code, 302)
        self.assertEqual(self.mutate(self.owner, '/api/projects', json={'id':'privado'}).status_code, 201)
        path = '/conta/cadastro'
        client = self.other
        self.assertIn(b'/conta/cadastro', self.request(client, '/conta/login').data)
        self.assertEqual(self.request(client, path, method='POST', data={'email':'nova@example.test'}).status_code, 403)
        csrf = self.csrf(client, path)
        duplicate = self.request(client, path, method='POST', data={'csrf':csrf,'email':'owner@example.test'})
        requested = self.request(client, path, method='POST', data={'csrf':csrf,'email':'Nova@Example.Test'})
        self.assertEqual(duplicate.data, requested.data)
        self.assertEqual(len(self.registrations), 1)
        email, link = self.registrations[0]
        self.assertEqual(email, 'nova@example.test')
        endpoint, token = link.split('#', 1)
        with self.store.connect() as db:
            self.assertIsNone(db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone())
        form = {'csrf':self.csrf(client, endpoint),'token':token,
                'password':'uma senha para cadastro','confirmation':'uma senha para cadastro'}
        self.assertEqual(self.request(client, endpoint, method='POST', data=form).status_code, 303)
        self.assertEqual(self.request(client, '/api/projects').get_json(), {'projects':[]})
        self.assertEqual(self.request(client, '/api/projects/privado').status_code, 404)
        form['csrf'] = self.csrf(self.member, endpoint)
        self.assertEqual(self.request(self.member, endpoint, method='POST', data=form).status_code, 400)

    def test_untrusted_host_is_rejected_before_authentication(self):
        self.app.config['TRUSTED_HOSTS'] = ['athena.example.test']
        response = self.request(self.other, '/healthz')
        self.assertEqual(response.status_code, 400)
        self.assertIn('not trusted', response.get_json()['error'])
        response = self.other.get('/healthz', base_url='https://athena.example.test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_project_and_diagram_permissions_are_scoped(self):
        self.assertEqual(self.request(self.other, '/api/projects').status_code, 401)
        for client, user in ((self.owner,'owner'), (self.member,'member'), (self.other,'other')):
            self.assertEqual(self.login(client, user).status_code, 302)
        self.assertEqual(self.request(self.owner, '/api/projects', method='POST', json={}).status_code, 403)
        self.assertEqual(self.mutate(self.owner, '/api/projects', json={'id':'projeto'}).status_code, 201)
        self.assertEqual(self.grant('group','dev','editar','fluxo').status_code, 302)
        self.assertEqual(self.request(self.member, '/api/projects/projeto').status_code, 404)
        self.assertEqual(self.request(self.member, '/api/projects/projeto/download').status_code, 404)
        archived = self.request(self.member, '/api/projects/backup/all')
        with ZipFile(io.BytesIO(archived.data)) as archive:
            self.assertNotIn('projects/projeto.json', archive.namelist())
        diagram = '/compartilhamento/projeto/diagramas/fluxo'
        self.assertEqual(self.request(self.other, diagram).status_code, 404)
        self.assertNotIn(b'Este documento', self.request(self.member, diagram).data)
        form = {'title':'Somente diagrama','code':'flowchart LR\nA --> B','revision':'1'}
        self.assertEqual(self.mutate(self.member, diagram, data=form).status_code, 302)
        self.assertEqual(self.mutate(self.member, diagram, data=form).status_code, 409)
        self.assertEqual(self.grant('organization','org','visualizar').status_code, 302)
        project = self.request(self.member, '/api/projects/projeto').get_json()
        self.assertEqual(project['_access'], {'level':1,'revision':2})
        self.assertEqual(self.mutate(self.member, '/api/projects/projeto', method='PUT', json=project).status_code, 403)
        self.assertEqual(self.mutate(self.member, '/api/projects/projeto', method='DELETE').status_code, 403)
        self.assertEqual(self.grant('group','dev','remover','fluxo').status_code, 302)
        self.assertEqual(self.mutate(self.member, diagram, data=form).status_code, 403)
        self.assertEqual(self.request(self.other, '/api/projects/projeto').status_code, 404)

    def test_password_reset_is_single_use_and_revokes_sessions(self):
        self.assertEqual(self.login(self.owner, 'owner').status_code, 302)
        recovery = self.other
        path = '/conta/recuperar'
        csrf = self.csrf(recovery, path)
        self.request(recovery, path, method='POST', data={'csrf':csrf,'email':'missing@example.test'})
        self.assertEqual(self.outbox, [])
        self.request(recovery, path, method='POST', data={'csrf':csrf,'email':'owner@example.test'})
        self.assertEqual(len(self.outbox), 1)
        email, link = self.outbox[0]
        self.assertEqual(email, 'owner@example.test')
        path, token = link.split('#', 1)
        password = 'my new private password'
        form = {'csrf':self.csrf(recovery, path),'token':token,'password':password,'confirmation':password}
        self.assertEqual(self.request(recovery, path, method='POST', data=form).status_code, 200)
        self.assertEqual(self.request(self.owner, '/api/projects').status_code, 401)
        form['csrf'] = self.csrf(recovery, path)
        self.assertEqual(self.request(recovery, path, method='POST', data=form).status_code, 400)
        self.assertEqual(self.login(self.owner, 'owner', password).status_code, 302)
