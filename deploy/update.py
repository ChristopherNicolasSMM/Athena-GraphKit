"""Fast-forward the source mirror, stage and validate a release, then reload WSGI."""
import argparse
import fcntl
import logging
import os
import subprocess
import sys
import tarfile
import tempfile
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from runtime import ensure_venv, site_packages

LOG = logging.getLogger('athena.deploy')
SMOKE = """
import shutil
from athena_cairo import load_cairosvg
from portal import app, studio

assert studio is not None, 'Hosted mode inactive'
assert shutil.which('dot'), 'dot binary unavailable'
assert load_cairosvg().svg2png(bytestring=b'<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"/>').startswith(b'\\x89PNG')
with app.test_client() as client:
    host = app.config.get('TRUSTED_HOSTS', ['localhost'])[0]
    assert client.get('/healthz', base_url='https://' + host).get_json() == {'status': 'ok'}
    assert client.get('/api/projects', base_url='https://' + host).status_code == 401
"""


def run(*args, cwd, env=None, timeout=120):
    result = subprocess.run(args, cwd=cwd, env=env, timeout=timeout, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        LOG.error('%s falhou (%s): %s', args[0], result.returncode, result.stdout[-6000:].strip())
        result.check_returncode()
    return result.stdout.strip()


def stage(base, repo, revision):
    destination = base / 'releases' / revision
    if destination.is_dir():
        return destination
    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        directory = Path(directory)
        archive = directory / 'source.tar'
        checkout = directory / 'release'
        run('git', 'archive', '--format=tar', '-o', str(archive), revision, cwd=repo)
        with tarfile.open(archive) as source:
            source.extractall(checkout, filter='data')
        checkout.rename(destination)
    return destination


def switch(base, release):
    with tempfile.TemporaryDirectory(dir=base) as directory:
        pointer = Path(directory) / 'current'
        pointer.symlink_to(release, target_is_directory=True)
        pointer.replace(base / 'current')


def update(base, repo, branch, wsgi):
    with (base / 'update.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            LOG.info('Verificação ignorada. Outra instância está em execução.')
            return
        if run('git', 'status', '--porcelain', cwd=repo):
            raise RuntimeError('Checkout de deploy possui alterações locais.')
        if run('git', 'symbolic-ref', '--short', 'HEAD', cwd=repo) != branch:
            raise RuntimeError(f'Checkout de deploy deve estar na branch {branch}.')
        run('git', 'fetch', '--no-tags', 'origin', branch, cwd=repo)
        revision = run('git', 'rev-parse', 'FETCH_HEAD', cwd=repo)
        run('git', 'merge-base', '--is-ancestor', 'HEAD', revision, cwd=repo)
        current = base / 'current'
        previous = current.resolve() if current.is_symlink() else None
        marker = base / 'reload-pending'
        if previous and previous.name == revision and not marker.is_file():
            LOG.info('Sem mudanças na revisão %s.', revision[:12])
            return
        LOG.info('Preparando revisão %s.', revision)
        release = stage(base, repo, revision)
        venv = ensure_venv(base, release, interpreter=sys.executable, logger=LOG)
        selected = release / '.venv'
        if not selected.is_symlink():
            selected.symlink_to(venv, target_is_directory=True)
        legacy = release / '.deps'
        if not legacy.is_symlink() and not legacy.exists():
            legacy.symlink_to(site_packages(venv), target_is_directory=True)
        env = os.environ | {'ATHENA_CONFIG': str(base / 'app.json')}
        env.pop('PYTHONPATH', None)
        env.pop('PYTHONHOME', None)
        run(str(venv / 'bin' / 'python'), '-c', SMOKE, cwd=release, env=env)
        run('git', 'merge', '--ff-only', revision, cwd=repo)
        marker.write_text(revision + '\n', encoding='ascii')
        switch(base, release)
        try:
            os.utime(wsgi, None)
        except OSError:
            if previous:
                switch(base, previous)
            else:
                current.unlink(missing_ok=True)
            raise
        marker.unlink()
        LOG.info('Revisão ativa %s. Recarga WSGI solicitada.', revision)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--wsgi', required=True, type=Path)
    parser.add_argument('--branch', default='main')
    parser.add_argument('--watch', action='store_true', help='Repete a verificação a cada dez minutos.')
    args = parser.parse_args()
    base, repo, wsgi = (path.resolve() for path in (args.base, args.repo, args.wsgi))
    os.umask(0o077)
    for folder in ('logs', 'venvs', 'releases'):
        (base / folder).mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(base / 'logs' / 'deploy.log', maxBytes=2_000_000,
                                  backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    LOG.addHandler(handler)
    LOG.setLevel(logging.INFO)
    while True:
        start = time.monotonic()
        try:
            update(base, repo, args.branch, wsgi)
        except Exception:
            LOG.exception('Atualização interrompida.')
            if not args.watch:
                return 1
        if not args.watch:
            return 0
        time.sleep(max(1, 600 - (time.monotonic() - start)))


if __name__ == '__main__':
    sys.exit(main())
