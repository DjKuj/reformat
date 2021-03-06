import contextlib
import os
from typing import Generator
from typing import Sequence
from typing import Tuple

from reformat.envcontext import envcontext
from reformat.envcontext import PatchesT
from reformat.envcontext import SubstitutionT
from reformat.envcontext import UNSET
from reformat.envcontext import Var
from reformat.hook import Hook
from reformat.languages import helpers
from reformat.prefix import Prefix
from reformat.util import clean_path_on_failure
from reformat.util import cmd_output_b

ENVIRONMENT_DIR = 'conda'
get_default_version = helpers.basic_get_default_version
healthy = helpers.basic_healthy


def get_env_patch(env: str) -> PatchesT:
    # On non-windows systems executable live in $CONDA_PREFIX/bin, on Windows
    # they can be in $CONDA_PREFIX/bin, $CONDA_PREFIX/Library/bin,
    # $CONDA_PREFIX/Scripts and $CONDA_PREFIX. Whereas the latter only
    # seems to be used for python.exe.
    path: SubstitutionT = (os.path.join(env, 'bin'), os.pathsep, Var('PATH'))
    if os.name == 'nt':  # pragma: no cover (platform specific)
        path = (env, os.pathsep, *path)
        path = (os.path.join(env, 'Scripts'), os.pathsep, *path)
        path = (os.path.join(env, 'Library', 'bin'), os.pathsep, *path)

    return (
        ('PYTHONHOME', UNSET),
        ('VIRTUAL_ENV', UNSET),
        ('CONDA_PREFIX', env),
        ('PATH', path),
    )


@contextlib.contextmanager
def in_env(
        prefix: Prefix,
        language_version: str,
) -> Generator[None, None, None]:
    directory = helpers.environment_dir(ENVIRONMENT_DIR, language_version)
    envdir = prefix.path(directory)
    with envcontext(get_env_patch(envdir)):
        yield


def install_environment(
        prefix: Prefix,
        version: str,
        additional_dependencies: Sequence[str],
) -> None:
    helpers.assert_version_default('conda', version)
    directory = helpers.environment_dir(ENVIRONMENT_DIR, version)

    env_dir = prefix.path(directory)
    with clean_path_on_failure(env_dir):
        cmd_output_b(
            'conda', 'env', 'create', '-p', env_dir, '--file',
            'environment.yml', cwd=prefix.prefix_dir,
        )
        if additional_dependencies:
            cmd_output_b(
                'conda', 'install', '-p', env_dir, *additional_dependencies,
                cwd=prefix.prefix_dir,
            )


def run_hook(
        hook: Hook,
        file_args: Sequence[str],
        color: bool,
) -> Tuple[int, bytes]:
    # TODO: Some rare commands need to be run using `conda run` but mostly we
    #       can run them without which is much quicker and produces a better
    #       output.
    # cmd = ('conda', 'run', '-p', env_dir) + hook.cmd
    with in_env(hook.prefix, hook.language_version):
        return helpers.run_xargs(hook, hook.cmd, file_args, color=color)
