"""Operator commands. Registration is controlled by the application operator."""
import json
import re
import sqlite3
from pathlib import Path

import click
from flask import g
from werkzeug.exceptions import HTTPException

from .accounts import password_hash


def install_commands(app, store, studio):
    @app.cli.group('access')
    def access():
        """Manage hosted accounts, teams and initial project imports."""

    def email_key(value):
        value = value.strip().lower()
        if not re.fullmatch(r'[^@\s]{1,100}@[^@\s.]+(?:\.[^@\s.]+)+', value) or len(value) > 254:
            raise click.ClickException('E-mail inválido.')
        return value

    def identify(db, email):
        user = db.execute('SELECT id FROM users WHERE email=?', (email_key(email),)).fetchone()
        if not user:
            raise click.ClickException('Usuário não cadastrado.')
        return user['id']

    @access.command('user')
    @click.argument('email')
    @click.password_option(confirmation_prompt=True)
    def user(email, password):
        """Create an account."""
        try:
            encoded = password_hash(password)
            with store.connect(write=True) as db:
                db.execute('INSERT INTO users(email,password) VALUES (?,?)', (email_key(email), encoded))
        except (ValueError, sqlite3.IntegrityError) as exc:
            raise click.ClickException('Conta já cadastrada ou senha fora do intervalo de 12 a 256 caracteres.') from exc
        click.echo('Conta criada.')

    @access.command('disable')
    @click.argument('email')
    @click.option('--enable', is_flag=True, help='Reativar a conta.')
    def disable(email, enable):
        with store.connect(write=True) as db:
            uid = identify(db, email)
            db.execute('UPDATE users SET enabled=?,epoch=epoch+1 WHERE id=?', (int(enable), uid))
            db.execute('DELETE FROM password_resets WHERE user=?', (uid,))
        click.echo('Conta atualizada.')

    @access.command('organization')
    @click.argument('identifier')
    @click.argument('name')
    def organization(identifier, name):
        create_team('organizations', identifier, name)

    @access.command('group')
    @click.argument('identifier')
    @click.argument('name')
    @click.argument('organization_id')
    def group(identifier, name, organization_id):
        create_team('groups', identifier, name, organization_id)

    def create_team(table, identifier, name, organization_id=None):
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', identifier) or not 1 <= len(name) <= 120:
            raise click.ClickException('Identificador ou nome inválido.')
        try:
            with store.connect(write=True) as db:
                if table == 'groups':
                    db.execute('INSERT INTO groups VALUES (?,?,?)', (identifier, organization_id, name))
                else:
                    db.execute('INSERT INTO organizations VALUES (?,?)', (identifier, name))
        except sqlite3.IntegrityError as exc:
            raise click.ClickException('Identificador em uso ou organização inexistente.') from exc
        click.echo('Cadastro criado.')

    @access.command('member')
    @click.argument('scope', type=click.Choice(['organization', 'group']))
    @click.argument('identifier')
    @click.argument('email')
    @click.option('--remove', is_flag=True)
    def member(scope, identifier, email, remove):
        with store.connect(write=True) as db:
            uid = identify(db, email)
            if scope == 'group':
                team = db.execute('SELECT organization FROM groups WHERE id=?', (identifier,)).fetchone()
                if not team:
                    raise click.ClickException('Grupo inexistente.')
                if not remove and not db.execute('SELECT 1 FROM organization_members WHERE organization=? AND user=?',
                                                 (team['organization'], uid)).fetchone():
                    raise click.ClickException('Adicione o usuário à organização do grupo primeiro.')
                table, column = 'group_members', 'team'
            else:
                if not db.execute('SELECT 1 FROM organizations WHERE id=?', (identifier,)).fetchone():
                    raise click.ClickException('Organização inexistente.')
                if remove:
                    db.execute('DELETE FROM group_members WHERE user=? AND team IN (SELECT id FROM groups WHERE organization=?)',
                               (uid, identifier))
                table, column = 'organization_members', 'organization'
            if remove:
                db.execute(f'DELETE FROM {table} WHERE {column}=? AND user=?', (identifier, uid))
            else:
                db.execute(f'INSERT OR IGNORE INTO {table} VALUES (?,?)', (identifier, uid))
        click.echo('Participação atualizada.')

    @access.command('import-project')
    @click.argument('email')
    @click.argument('file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
    def import_project(email, file):
        with store.connect() as db:
            g.identity = {'id': identify(db, email)}
        try:
            project = studio.validate(json.loads(file.read_text(encoding='utf-8-sig')))
            project.pop('_access', None)
            studio.create(project)
        except (ValueError, OSError, HTTPException) as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo('Projeto importado.')
