"""Athena integration for the reusable authorization store."""
import json
import sqlite3

from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from .store import SUBJECTS

PROJECTS = """
CREATE TABLE IF NOT EXISTS studio_projects (
    id TEXT PRIMARY KEY, owner INTEGER NOT NULL REFERENCES users(id),
    body TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1
)
"""
PRINCIPALS = {'user': 'users', 'group': 'groups', 'organization': 'organizations'}
ROLES = {'visualizar': 1, 'editar': 2}


class StudioProjects:
    def __init__(self, app, store, validate, slug):
        self.store = store
        self.validate = validate
        self.slug = slug
        with store.connect() as db:
            db.execute(PROJECTS)
        bp = Blueprint('sharing', __name__, url_prefix='/compartilhamento')
        bp.add_url_rule('/', 'dashboard', self.dashboard)
        bp.add_url_rule('/<pid>/permissoes', 'permissions', self.permissions, methods=['GET', 'POST'])
        bp.add_url_rule('/<pid>/diagramas/<did>', 'diagram', self.diagram, methods=['GET', 'POST'])
        app.register_blueprint(bp)

    @property
    def uid(self):
        return g.identity['id']

    @staticmethod
    def serialized(project):
        try:
            return json.dumps(project, ensure_ascii=False, allow_nan=False)
        except ValueError:
            abort(400, 'Projeto contém números inválidos.')

    def create(self, project):
        try:
            with self.store.connect(write=True) as db:
                db.execute('INSERT INTO studio_projects(id,owner,body) VALUES (?,?,?)',
                           (project['id'], self.uid, self.serialized(project)))
        except sqlite3.IntegrityError:
            abort(409, 'Identificador de projeto indisponível.')
        return project

    def list(self):
        with self.store.connect() as db:
            rows = db.execute(f"""
                SELECT id,body FROM studio_projects WHERE owner=:uid OR id IN (
                  SELECT resource FROM grants JOIN ({SUBJECTS}) USING(principal,target)
                  WHERE scope='project'
                )""", {'uid': self.uid}).fetchall()
        return [json.loads(row['body']) for row in rows]

    def project_row(self, db, pid):
        row = db.execute('SELECT * FROM studio_projects WHERE id=?', (pid,)).fetchone()
        if not row:
            abort(404, 'Projeto não encontrado.')
        level = 3 if row['owner'] == self.uid else self.store.level(db, self.uid, 'project', pid)
        return row, level

    @staticmethod
    def require(actual, minimum):
        if actual < minimum:
            abort(404 if not actual else 403, 'Recurso indisponível para esta conta.')

    def get(self, pid):
        with self.store.connect() as db:
            row, level = self.project_row(db, pid)
            self.require(level, 1)
        project = json.loads(row['body'])
        project['_access'] = {'level': level, 'revision': row['revision']}
        return project

    def save(self, pid, project):
        revision = self.revision(project.pop('_access', None))
        with self.store.connect(write=True) as db:
            row, level = self.project_row(db, pid)
            self.require(level, 2)
            previous = json.loads(row['body'])
            removed = {item['id'] for item in previous.get('diagrams', [])} - {
                item['id'] for item in project.get('diagrams', [])
            }
            self.replace(db, row, revision, project)
            db.executemany("DELETE FROM grants WHERE scope='diagram' AND resource=?",
                           ((f'{pid}/{did}',) for did in removed))

    @staticmethod
    def revision(access):
        return access.get('revision') if isinstance(access, dict) else None

    def replace(self, db, row, revision, project):
        if type(revision) is not int or revision != row['revision']:
            abort(409, 'O projeto mudou desde que foi aberto. Recarregue antes de salvar.')
        db.execute('UPDATE studio_projects SET body=?,revision=revision+1 WHERE id=?',
                   (self.serialized(project), row['id']))

    def delete(self, pid):
        with self.store.connect(write=True) as db:
            _, level = self.project_row(db, pid)
            self.require(level, 3)
            db.execute("""DELETE FROM grants WHERE (scope='project' AND resource=?)
                          OR (scope='diagram' AND substr(resource,1,?)=?)""",
                       (pid, len(pid) + 1, pid + '/'))
            db.execute('DELETE FROM studio_projects WHERE id=?', (pid,))

    def dashboard(self):
        with self.store.connect() as db:
            rows = db.execute(f"""SELECT DISTINCT resource FROM grants
                                  JOIN ({SUBJECTS}) USING(principal,target)
                                  WHERE scope='diagram'""", {'uid': self.uid}).fetchall()
            diagrams = []
            for row in rows:
                pid, did = row['resource'].split('/')
                project = db.execute('SELECT body FROM studio_projects WHERE id=?', (pid,)).fetchone()
                if project:
                    item = next((d for d in json.loads(project['body']).get('diagrams', []) if d['id'] == did), None)
                    if item:
                        diagrams.append((pid, did, item['title']))
            owned = {row[0] for row in db.execute("SELECT id FROM studio_projects WHERE owner=?", (self.uid,))}
        return render_template('sharing.html', projects=self.list(), diagrams=diagrams, owned=owned)

    def diagram(self, pid, did):
        pid, did = self.slug(pid), self.slug(did)
        with self.store.connect(write=request.method == 'POST') as db:
            row, project_level = self.project_row(db, pid)
            level = max(project_level, self.store.level(db, self.uid, 'diagram', f'{pid}/{did}'))
            self.require(level, 1)
            project = json.loads(row['body'])
            item = next((d for d in project.get('diagrams', []) if d['id'] == did), None)
            if not item:
                abort(404, 'Diagrama não encontrado.')
            if request.method == 'POST':
                self.require(level, 2)
                try:
                    revision = int(request.form.get('revision',''))
                except ValueError:
                    abort(400, 'Revisão inválida.')
                item.update(title=request.form.get('title', ''), code=request.form.get('code', ''), visualStale=True)
                self.validate(project)
                self.replace(db, row, revision, project)
                return redirect(url_for('sharing.diagram', pid=pid, did=did))
        return render_template('shared_diagram.html', item=item, level=level, revision=row['revision'])

    @staticmethod
    def identity(db, principal, value):
        if principal == 'user':
            row = db.execute('SELECT id FROM users WHERE email=? AND enabled=1 AND email_verified=1',
                             (value.lower(),)).fetchone()
        else:
            row = db.execute(f'SELECT id FROM {PRINCIPALS[principal]} WHERE id=?', (value,)).fetchone()
        if not row:
            message = 'Informe o e-mail confirmado de uma conta ativa.' if principal == 'user' else 'Destinatário não encontrado.'
            abort(400, message)
        return str(row['id'])

    def permissions(self, pid):
        pid = self.slug(pid)
        with self.store.connect(write=request.method == 'POST') as db:
            row, level = self.project_row(db, pid)
            self.require(level, 3)
            project = json.loads(row['body'])
            diagrams = project.get('diagrams', [])
            if request.method == 'POST':
                did = request.form.get('diagram', '')
                principal = request.form.get('principal')
                action = request.form.get('role')
                value = request.form.get('target', '').strip()
                if principal not in PRINCIPALS or action not in (*ROLES, 'remover'):
                    abort(400, 'Tipo de destinatário ou permissão inválida.')
                if did and did not in {item['id'] for item in diagrams}:
                    abort(404, 'Diagrama não encontrado.')
                target = value if action == 'remover' else self.identity(db, principal, value)
                scope, resource = ('diagram', f'{pid}/{did}') if did else ('project', pid)
                if action == 'remover':
                    db.execute('DELETE FROM grants WHERE scope=? AND resource=? AND principal=? AND target=?',
                               (scope, resource, principal, target))
                else:
                    db.execute("""INSERT INTO grants VALUES (?,?,?,?,?)
                                  ON CONFLICT(scope,resource,principal,target) DO UPDATE SET level=excluded.level""",
                               (scope, resource, principal, target, ROLES[action]))
                return redirect(url_for('sharing.permissions', pid=pid))
            grants = db.execute("""
                SELECT grants.*, COALESCE(users.email,grants.target) AS label
                FROM grants LEFT JOIN users ON principal='user' AND CAST(users.id AS TEXT)=target
                WHERE (scope='project' AND resource=?)
                   OR (scope='diagram' AND substr(resource,1,?)=?)
                ORDER BY scope, resource, principal, target""", (pid, len(pid) + 1, pid + '/')).fetchall()
        return render_template('permissions.html', project=project, diagrams=diagrams, grants=grants)
