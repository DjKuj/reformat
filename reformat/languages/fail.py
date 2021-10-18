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
    out = f'{hook.entry}\n\n'.encode()
    out += b'\n'.join(f.encode() for f in file_args) + b'\n'
    return 1, out
