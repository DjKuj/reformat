import contextlib
import os.path
from typing import Generator
from typing import Sequence
from typing import Tuple

import reformat.constants as C
from reformat.envcontext import envcontext
from reformat.envcontext import PatchesT
from reformat.envcontext import Var
from reformat.hook import Hook
from reformat.languages import helpers
from reformat.prefix import Prefix
from reformat.util import clean_path_on_failure

ENVIRONMENT_DIR = 'dotnetenv'
BIN_DIR = 'bin'

get_default_version = helpers.basic_get_default_version
healthy = helpers.basic_healthy


def get_env_patch(venv: str) -> PatchesT:
    return (
        ('PATH', (os.path.join(venv, BIN_DIR), os.pathsep, Var('PATH'))),
    )


@contextlib.contextmanager
def in_env(prefix: Prefix) -> Generator[None, None, None]:
    directory = helpers.environment_dir(ENVIRONMENT_DIR, C.DEFAULT)
    envdir = prefix.path(directory)
    with envcontext(get_env_patch(envdir)):
        yield


def install_environment(
        prefix: Prefix,
        version: str,
        additional_dependencies: Sequence[str],
) -> None:
    helpers.assert_version_default('dotnet', version)
    helpers.assert_no_additional_deps('dotnet', additional_dependencies)

    envdir = prefix.path(helpers.environment_dir(ENVIRONMENT_DIR, version))
    with clean_path_on_failure(envdir):
        build_dir = 'reformat-build'

        # Build & pack nupkg file
        helpers.run_setup_cmd(
            prefix,
            (
                'dotnet', 'pack',
                '--configuration', 'Release',
                '--output', build_dir,
            ),
        )

        # Determine tool from the packaged file <tool_name>.<version>.nupkg
        build_outputs = os.listdir(os.path.join(prefix.prefix_dir, build_dir))
        if len(build_outputs) != 1:
            raise NotImplementedError(
                f"Can't handle multiple build outputs. Got {build_outputs}",
            )
        tool_name = build_outputs[0].split('.')[0]

        # Install to bin dir
        helpers.run_setup_cmd(
            prefix,
            (
                'dotnet', 'tool', 'install',
                '--tool-path', os.path.join(envdir, BIN_DIR),
                '--add-source', build_dir,
                tool_name,
            ),
        )

        # Clean the git dir, ignoring the environment dir
        clean_cmd = ('git', 'clean', '-ffxd', '-e', f'{ENVIRONMENT_DIR}-*')
        helpers.run_setup_cmd(prefix, clean_cmd)


def run_hook(
        hook: Hook,
        file_args: Sequence[str],
        color: bool,
) -> Tuple[int, bytes]:
    with in_env(hook.prefix):
        return helpers.run_xargs(hook, hook.cmd, file_args, color=color)
