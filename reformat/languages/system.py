from typing import Sequence
from typing import Tuple

from reformat.hook import Hook
from reformat.languages import helpers


ENVIRONMENT_DIR = None
get_default_version = helpers.basic_get_default_version
healthy = helpers.basic_healthy
install_environment = helpers.no_install


def run_hook(
        hook: Hook,
        file_args: Sequence[str],
        color: bool,
) -> Tuple[int, bytes]:
    return helpers.run_xargs(hook, hook.cmd, file_args, color=color)
