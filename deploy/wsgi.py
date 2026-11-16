"""Copy this file to the PythonAnywhere WSGI entry point."""
import logging
import os
import runpy
import site
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE = Path(os.environ.get('ATHENA_DEPLOY_HOME', str(Path.home() / 'athena-deploy')))
LOGS = BASE / 'logs'
LOGS.mkdir(parents=True, exist_ok=True, mode=0o700)


def file_handler(name, level):
    handler = RotatingFileHandler(LOGS / name, maxBytes=2_000_000, backupCount=3, encoding='utf-8')
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    return handler


startup = logging.getLogger('athena.startup')
startup.setLevel(logging.INFO)
startup.addHandler(file_handler('startup.log', logging.INFO))
try:
    current = BASE / 'current'
    if current.is_symlink():
        release = current.resolve(strict=True)
    else:
        release = Path(os.environ.get('ATHENA_REPO', str(Path.home() / 'Athena-GraphKit'))).resolve(strict=True)
    runtime = runpy.run_path(str(release / 'deploy' / 'runtime.py'))
    venv = runtime['ensure_venv'](BASE, release, logger=startup)
    packages = str(runtime['site_packages'](venv))
    before = set(sys.path)
    site.addsitedir(packages)
    additions = [path for path in sys.path if path not in before and path != packages]
    sys.path[:] = [str(release), packages, *additions,
                   *(path for path in sys.path if path in before and path != packages)]
    os.environ['ATHENA_CONFIG'] = str(BASE / 'app.json')
    from portal import app as application

    application.logger.addHandler(file_handler('errors.log', logging.ERROR))
    startup.info('Aplicação iniciada. Revisão %s', release.name)
except Exception:
    startup.exception('Falha ao inicializar a aplicação.')
    raise
