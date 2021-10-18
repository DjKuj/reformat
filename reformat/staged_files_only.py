import contextlib
import logging
import os.path
import time
from typing import Generator

from reformat import git
from reformat.util import CalledProcessError
from reformat.util import cmd_output
from reformat.util import cmd_output_b
from reformat.xargs import xargs


logger = logging.getLogger('reformat')

# without forcing submodule.recurse=0, changes in nested submodules will be
# discarded if `submodule.recurse=1` is configured
# we choose this instead of `--no-recurse-submodules` because it works on
# versions of git before that option was added to `git checkout`
_CHECKOUT_CMD = ('git', '-c', 'submodule.recurse=0', 'checkout', '--', '.')


def _git_apply(patch: str) -> None:
    args = ('apply', '--whitespace=nowarn', patch)
    try:
        cmd_output_b('git', *args)
    except CalledProcessError:
        # Retry with autocrlf=false -- see #570
        cmd_output_b('git', '-c', 'core.autocrlf=false', *args)


@contextlib.contextmanager
def _intent_to_add_cleared() -> Generator[None, None, None]:
    intent_to_add = git.intent_to_add_files()
    if intent_to_add:
        logger.warning('Unstaged intent-to-add files detected.')

        xargs(('git', 'rm', '--cached', '--'), intent_to_add)
        try:
            yield
        finally:
            xargs(('git', 'add', '--intent-to-add', '--'), intent_to_add)
    else:
        yield


@contextlib.contextmanager
def _unstaged_changes_cleared(patch_dir: str) -> Generator[None, None, None]:
    tree = cmd_output('git', 'write-tree')[1].strip()
    retcode, diff_stdout_binary, _ = cmd_output_b(
        'git', 'diff-index', '--ignore-submodules', '--binary',
        '--exit-code', '--no-color', '--no-ext-diff', tree, '--',
        retcode=None,
    )
    if retcode and diff_stdout_binary.strip():
        patch_filename = f'patch{int(time.time())}-{os.getpid()}'
        patch_filename = os.path.join(patch_dir, patch_filename)
        logger.warning('Unstaged files detected.')
        logger.info(f'Stashing unstaged files to {patch_filename}.')
        # Save the current unstaged changes as a patch
        os.makedirs(patch_dir, exist_ok=True)
        with open(patch_filename, 'wb') as patch_file:
            patch_file.write(diff_stdout_binary)

        # prevent recursive post-checkout hooks (#1418)
        no_checkout_env = dict(os.environ, _PRE_COMMIT_SKIP_POST_CHECKOUT='1')
        cmd_output_b(*_CHECKOUT_CMD, env=no_checkout_env)

        try:
            yield
        finally:
            # Try to apply the patch we saved
            try:
                _git_apply(patch_filename)
            except CalledProcessError:
                logger.warning(
                    'Stashed changes conflicted with hook auto-fixes... '
                    'Rolling back fixes...',
                )
                # We failed to apply the patch, presumably due to fixes made
                # by hooks.
                # Roll back the changes made by hooks.
                cmd_output_b(*_CHECKOUT_CMD, env=no_checkout_env)
                _git_apply(patch_filename)

            logger.info(f'Restored changes from {patch_filename}.')
    else:
        # There weren't any staged files so we don't need to do anything
        # special
        yield


@contextlib.contextmanager
def staged_files_only(patch_dir: str) -> Generator[None, None, None]:
    """Clear any unstaged changes from the git working directory inside this
    context.
    """
    with _intent_to_add_cleared(), _unstaged_changes_cleared(patch_dir):
        yield
