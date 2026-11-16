"""Flask blueprint for login, logout, password recovery and CSRF protection."""
import hashlib
import hmac
import re
import secrets
import time
from datetime import timedelta

from flask import Blueprint, abort, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .language import translate

DUMMY_HASH = generate_password_hash(secrets.token_hex(16))


def password_hash(password):
    if not 12 <= len(password) <= 256:
        raise ValueError('Use uma senha entre 12 e 256 caracteres.')
    return generate_password_hash(password)


class Accounts:
    def __init__(self, app, store, send_reset, *, send_registration=None, public_endpoints=()):
        self.app = app
        self.store = store
        self.send_reset = send_reset
        self.send_registration = send_registration
        self.public_endpoints = {'static', 'accounts.static', *public_endpoints}
        if not app.secret_key or len(app.secret_key) < 32:
            raise ValueError('Configure uma chave de sessão de pelo menos 32 caracteres.')
        app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                          PERMANENT_SESSION_LIFETIME=timedelta(hours=12))
        app.context_processor(lambda: {'csrf_token': self.csrf_token, 'registration_enabled': send_registration is not None})
        app.before_request(self.protect)
        app.after_request(self.private_response)
        bp = Blueprint('accounts', __name__, template_folder='templates', static_folder='static', url_prefix='/conta')
        bp.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        bp.add_url_rule('/sair', 'logout', self.logout, methods=['POST'])
        bp.add_url_rule('/recuperar', 'forgot', self.forgot, methods=['GET', 'POST'])
        bp.add_url_rule('/redefinir', 'reset', self.reset, methods=['GET', 'POST'])
        if self.send_registration is not None:
            bp.add_url_rule('/cadastro', 'register', self.register, methods=['GET', 'POST'])
            bp.add_url_rule('/ativar', 'activate', self.activate, methods=['GET', 'POST'])
        app.register_blueprint(bp)

    @staticmethod
    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return session['csrf']

    def protect(self):
        g.identity = None
        if request.routing_exception is not None or request.endpoint in self.public_endpoints:
            return
        if 'uid' in session:
            with self.store.connect() as db:
                user = db.execute('SELECT id,email,epoch FROM users WHERE id=? AND enabled=1',
                                  (session['uid'],)).fetchone()
            if user and session.get('epoch') == user['epoch']:
                g.identity = user
            else:
                session.clear()
        if not g.identity and not (request.endpoint or '').startswith('accounts.'):
            if request.path.startswith('/api/'):
                return jsonify(error='Entre para continuar.'), 401
            return redirect(url_for('accounts.login'))
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
            if 'csrf' not in session or not hmac.compare_digest(token.encode(), session['csrf'].encode()):
                abort(403, translate('Sessão do formulário inválida. Recarregue a página.', self.language()))

    @staticmethod
    def private_response(response):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; connect-src 'self' data:; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        if request.endpoint != 'static':
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Referrer-Policy'] = 'no-referrer'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
        return response

    def allowed(self, action, email, *, limit, ip_limit):
        now = int(time.time())
        ip = request.remote_addr or 'unknown'
        with self.store.connect(write=True) as db:
            db.execute('DELETE FROM attempts WHERE expires<=?', (now,))
            for key, maximum in ((f'{action}:ip:{ip}', ip_limit), (f'{action}:email:{email}', limit)):
                row = db.execute('SELECT count FROM attempts WHERE bucket=?', (key,)).fetchone()
                if row and row['count'] >= maximum:
                    return False
                db.execute("""INSERT INTO attempts VALUES (?,?,1)
                              ON CONFLICT(bucket) DO UPDATE SET count=count+1""", (key, now + 900))
        return True

    @staticmethod
    def language():
        requested = request.args.get('lang')
        return requested if requested in ('pt', 'en') else ('en' if request.cookies.get('athena_lang') == 'en' else 'pt')

    def page(self, mode, **context):
        language = self.language()
        response = self.app.make_response(render_template(
            'athena_access/account.html', mode=mode, language=language,
            t=lambda message: translate(message, language), **context
        ))
        if request.args.get('lang') in ('pt', 'en'):
            response.set_cookie('athena_lang', language, max_age=31536000,
                                secure=self.app.config['SESSION_COOKIE_SECURE'], samesite='Lax')
        return response

    def login(self):
        if g.identity:
            return redirect(self.app.config.get('ACCOUNT_HOME', '/'))
        if request.method == 'GET':
            return self.page('login')
        email = request.form.get('email', '').strip().lower()[:254]
        password = request.form.get('password', '')
        if not self.allowed('login', email, limit=8, ip_limit=60):
            return self.page('login', error='Muitas tentativas. Aguarde e tente novamente.'), 429
        with self.store.connect() as db:
            user = db.execute('SELECT * FROM users WHERE email=? AND enabled=1', (email,)).fetchone()
        valid = len(password) <= 256 and check_password_hash(user['password'] if user else DUMMY_HASH, password)
        if not user or not valid:
            return self.page('login', error='E-mail ou senha inválidos.'), 401
        session.clear()
        session.update(uid=user['id'], epoch=user['epoch'], permanent=True)
        return redirect(self.app.config.get('ACCOUNT_HOME', '/'))

    def register(self):
        if g.identity:
            return redirect(self.app.config.get('ACCOUNT_HOME', '/'))
        if request.method == 'GET':
            return self.page('register')
        email = request.form.get('email', '').strip().lower()
        if len(email) > 254 or not re.fullmatch(r'[^@\s]{1,100}@[^@\s.]+(?:\.[^@\s.]+)+', email):
            return self.page('register', email=email, error='Informe um e-mail válido.'), 400
        if self.allowed('register', email, limit=3, ip_limit=20):
            token = secrets.token_urlsafe(32)
            digest = hashlib.sha256(token.encode()).hexdigest()
            now = int(time.time())
            with self.store.connect(write=True) as db:
                db.execute('DELETE FROM account_registrations WHERE expires<=?', (now,))
                available = not db.execute('SELECT 1 FROM users WHERE email=?', (email,)).fetchone()
                if available:
                    db.execute("""INSERT INTO account_registrations VALUES (?,?,?)
                                  ON CONFLICT(email) DO UPDATE SET digest=excluded.digest,expires=excluded.expires""",
                               (digest, email, now + 1800))
            if available:
                try:
                    self.send_registration(email, url_for('accounts.activate') + '#' + token)
                except Exception:
                    self.app.logger.error('Falha na entrega de e-mail de cadastro.')
        return self.page('register', message='Se o endereço puder ser cadastrado, você receberá um link para definir sua senha.')

    def activate(self):
        if g.identity:
            return redirect(self.app.config.get('ACCOUNT_HOME', '/'))
        if request.method == 'GET':
            return self.page('activate')
        token = request.form.get('token', '')
        if not 32 <= len(token) <= 128:
            return self.page('activate', error='Link inválido ou expirado. Solicite um novo cadastro.'), 400
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.store.connect() as db:
            pending = self.pending_registration(db, digest)
        if not pending:
            return self.page('activate', error='Link inválido ou expirado. Solicite um novo cadastro.'), 400
        password = request.form.get('password', '')
        if password != request.form.get('confirmation'):
            return self.page('activate', token=token, error='As senhas digitadas são diferentes.'), 400
        try:
            hashed = password_hash(password)
        except ValueError as exc:
            return self.page('activate', token=token, error=str(exc)), 400
        with self.store.connect(write=True) as db:
            pending = self.pending_registration(db, digest)
            if not pending:
                return self.page('activate', error='Link inválido ou expirado. Solicite um novo cadastro.'), 400
            inserted = db.execute('INSERT INTO users(email,password) VALUES (?,?) ON CONFLICT(email) DO NOTHING',
                                  (pending['email'], hashed))
            db.execute('DELETE FROM account_registrations WHERE digest=?', (digest,))
            if inserted.rowcount != 1:
                return self.page('activate', error='Link inválido ou expirado. Solicite um novo cadastro.'), 400
        session.clear()
        session.update(uid=inserted.lastrowid, epoch=0, permanent=True)
        return redirect(self.app.config.get('ACCOUNT_HOME', '/'), code=303)

    @staticmethod
    def pending_registration(db, digest):
        return db.execute('SELECT email FROM account_registrations WHERE digest=? AND expires>?',
                          (digest, int(time.time()))).fetchone()

    def logout(self):
        session.clear()
        return redirect(url_for('accounts.login'))

    def forgot(self):
        if request.method == 'GET':
            return self.page('forgot')
        email = request.form.get('email', '').strip().lower()[:254]
        if self.allowed('forgot', email, limit=3, ip_limit=30):
            token = secrets.token_urlsafe(32)
            digest = hashlib.sha256(token.encode()).hexdigest()
            with self.store.connect(write=True) as db:
                user = db.execute('SELECT id FROM users WHERE email=? AND enabled=1', (email,)).fetchone()
                if user:
                    db.execute('DELETE FROM password_resets WHERE user=? OR expires<=?',
                               (user['id'], int(time.time())))
                    db.execute('INSERT INTO password_resets VALUES (?,?,?)',
                               (digest, user['id'], int(time.time()) + 1800))
            if user:
                try:
                    self.send_reset(email, url_for('accounts.reset') + '#' + token)
                except Exception:
                    self.app.logger.error('Falha na entrega de e-mail de recuperação.')
        return self.page('forgot', message='Se o e-mail estiver cadastrado, você receberá um link de recuperação.')

    def reset(self):
        if request.method == 'GET':
            return self.page('reset')
        token = request.form.get('token', '')
        if not 32 <= len(token) <= 128:
            return self.page('reset', error='Link inválido ou expirado.'), 400
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.store.connect() as db:
            user = self.reset_user(db, digest)
        if not user:
            return self.page('reset', error='Link inválido ou expirado.'), 400
        password = request.form.get('password', '')
        if password != request.form.get('confirmation'):
            return self.page('reset', token=token, error='As senhas digitadas são diferentes.'), 400
        try:
            hashed = password_hash(password)
        except ValueError as exc:
            return self.page('reset', token=token, error=str(exc)), 400
        with self.store.connect(write=True) as db:
            user = self.reset_user(db, digest)
            if not user:
                return self.page('reset', error='Link inválido ou expirado.'), 400
            db.execute('UPDATE users SET password=?,epoch=epoch+1 WHERE id=?', (hashed, user['user']))
            db.execute('DELETE FROM password_resets WHERE user=?', (user['user'],))
        session.clear()
        return self.page('login', message='Senha atualizada. Entre com a nova senha.')

    @staticmethod
    def reset_user(db, digest):
        return db.execute("""SELECT r.user FROM password_resets r JOIN users u ON u.id=r.user
                             WHERE digest=? AND expires>? AND u.enabled=1""",
                          (digest, int(time.time()))).fetchone()
