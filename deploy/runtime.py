"""Provision an isolated, reusable Python environment for a hosted release."""
import fcntl
import hashlib
import logging
import os
import shutil
import subprocess
import sys


def environment(base, release):
    requirements = release / 'requirements.txt'
    version = f'{sys.version_info.major}.{sys.version_info.minor}'
    digest = hashlib.sha256(requirements.read_bytes() + version.encode()).hexdigest()[:24]
    return base / 'venvs' / digest


def site_packages(venv):
    version = f'{sys.version_info.major}.{sys.version_info.minor}'
    return venv / 'lib' / f'python{version}' / 'site-packages'


def ensure_venv(base, release, *, interpreter=None, logger=None):
    logger = logger or logging.getLogger(__name__)
    venv = environment(base, release)
    python = venv / 'bin' / 'python'
    ready = venv / '.athena-ready'
    venv.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    env = os.environ.copy()
    for key in ('PYTHONHOME', 'PYTHONPATH', 'VIRTUAL_ENV', 'PIP_TARGET', 'PIP_PREFIX', 'PIP_USER'):
        env.pop(key, None)

    def run(*args):
        result = subprocess.run(args, cwd=release, env=env, check=False, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        if result.returncode:
            logger.error('Falha na preparação do venv: %s', result.stdout[-4000:].strip())
            result.check_returncode()

    with venv.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if ready.is_file() and python.is_file() and site_packages(venv).is_dir():
            logger.info('Reutilizando venv %s.', venv)
            return venv
        ready.unlink(missing_ok=True)
        if not python.is_file() or not (venv / 'pyvenv.cfg').is_file():
            version = f'{sys.version_info.major}.{sys.version_info.minor}'
            interpreter = interpreter or shutil.which(f'python{version}')
            if not interpreter:
                raise RuntimeError(f'Interpretador python{version} indisponível para criar o venv.')
            logger.info('Criando venv %s.', venv)
            run(str(interpreter), '-m', 'venv', str(venv))
        logger.info('Instalando dependências no venv %s.', venv)
        run(str(python), '-m', 'pip', 'install', '--disable-pip-version-check',
            '-r', str(release / 'requirements.txt'))
        run(str(python), '-m', 'pip', 'check')
        ready.touch()
    return venv
