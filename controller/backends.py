"""Fixed inference targets with machine-specific paths supplied by configuration."""
import os
import sys

from controller.wsl_bridge import WSLBridge

BACKENDS = ('local', 'cloud')
_TARGETS = {
    'local': {'backend': 'local', 'base_url': 'http://127.0.0.1:8000/v1',
              'model_id': 'gamescaling', 'model_root': 'THUSI-Lab/GameScaling-0.8B-S3'},
    'cloud': {'backend': 'cloud', 'base_url': 'http://127.0.0.1:18080/v1',
              'model_id': 'gamescaling', 'model_root': 'THUSI-Lab/GameScaling-9B-S3'},
}


def _required_path(variable):
    value = os.environ.get(variable)
    if not value or not value.strip():
        raise ValueError(f'Missing controller configuration: set {variable}')
    return value


def backend_target(backend='local'):
    if type(backend) is not str or backend not in BACKENDS:
        raise ValueError('backend must be local or cloud')
    return _TARGETS[backend].copy()


def create_bridge(backend='local', *, timeout=15):
    target = backend_target(backend)
    if backend == 'local':
        return WSLBridge(timeout=timeout)
    repo = _required_path('GAMESCALING_WINDOWS_CLIENT_REPO')
    return WSLBridge(command=[sys.executable, '-u',
        __import__('pathlib').Path(__file__).with_name('policy_worker.py').as_posix(),
        '--repo', repo, '--base-url', target['base_url']], timeout=timeout)


def validate_health(health, backend='local'):
    target = backend_target(backend)
    try:
        models = health['models']['data']
        valid = isinstance(models, list) and any(isinstance(row, dict) and
            row.get('id') == target['model_id'] and row.get('root') == target['model_root']
            for row in models)
    except (KeyError, TypeError):
        valid = False
    if not valid:
        raise RuntimeError(f"Expected {target['backend']} model id={target['model_id']} "
                           f"root={target['model_root']} at {target['base_url']}")
    return health
