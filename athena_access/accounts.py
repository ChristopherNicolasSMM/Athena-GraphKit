"""Flask blueprint for login, logout, password recovery and CSRF protection."""
import hashlib
import hmac
import secrets
import time
from datetime import timedelta

from flask import Blueprint, abort, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

DUMMY_HASH = generate_password_hash(secrets.token_hex(16))


def password_hash(password):
    if not 12 <= len(password) <= 256:
        raise ValueError('Use uma senha entre 12 e 256 caracteres.')
    return generate_password_hash(password)


class Accounts:
    def __init__(self, app, store, send_reset, *, public_endpoints=()):
        self.app = app
        self.store = store
        self.send_reset = send_reset
        self.public_endpoints = {'static', 'accounts.static', *public_endpoints}
        if not app.secret_key or len(app.secret_key) < 32:
            raise ValueError('Configure uma chave de sessão de pelo menos 32 caracteres.')
        app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                          PERMANENT_SESSION_LIFETIME=timedelta(hours=12))
        app.context_processor(lambda: {'csrf_token': self.csrf_token})
        app.before_request(self.protect)
        app.after_request(self.private_response)
        bp = Blueprint('accounts', __name__, template_folder='templates', static_folder='static', url_prefix='/conta')
        bp.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        bp.add_url_rule('/sair', 'logout', self.logout, methods=['POST'])
        bp.add_url_rule('/recuperar', 'forgot', self.forgot, methods=['GET', 'POST'])
        bp.add_url_rule('/redefinir', 'reset', self.reset, methods=['GET', 'POST'])
        app.register_blueprint(bp)

    @staticmethod
    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return session['csrf']

    def protect(self):
        g.identity = None
        if request.endpoint in self.public_endpoints:
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
                abort(403, 'Sessão do formulário inválida. Recarregue a página.')

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
    def page(mode, **context):
        return render_template('athena_access/account.html', mode=mode, **context)

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
