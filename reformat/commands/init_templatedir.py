import logging
import os.path
from typing import Sequence

from reformat.commands.install_uninstall import install
from reformat.store import Store
from reformat.util import CalledProcessError
from reformat.util import cmd_output

logger = logging.getLogger('reformat')


def init_templatedir(
        config_file: str,
        store: Store,
        directory: str,
        hook_types: Sequence[str],
        skip_on_missing_config: bool = True,
) -> int:
    install(
        config_file,
        store,
        hook_types=hook_types,
        overwrite=True,
        skip_on_missing_config=skip_on_missing_config,
        git_dir=directory,
    )
    try:
        _, out, _ = cmd_output('git', 'config', 'init.templateDir')
    except CalledProcessError:
        configured_path = None
    else:
        configured_path = os.path.realpath(os.path.expanduser(out.strip()))
    dest = os.path.realpath(directory)
    if configured_path != dest:
        logger.warning('`init.templateDir` not set to the target directory')
        logger.warning(f'maybe `git config --global init.templateDir {dest}`?')
    return 0
