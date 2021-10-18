# TODO: maybe `git ls-remote git://github.com/reformat/reformat-hooks` to
# determine the latest revision?  This adds ~200ms from my tests (and is
# significantly faster than https:// or http://).  For now, periodically
# manually updating the revision is fine.
SAMPLE_CONFIG = '''\
# See https://reformat.com for more information
# See https://reformat.com/hooks.html for more hooks
repos:
-   repo: https://github.com/reformat/reformat-hooks
    rev: v3.2.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
'''


def sample_config() -> int:
    print(SAMPLE_CONFIG, end='')
    return 0
