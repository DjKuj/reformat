import os.path

from reformat import output
from reformat.store import Store
from reformat.util import rmtree


def clean(store: Store) -> int:
    legacy_path = os.path.expanduser('~/.reformat')
    for directory in (store.directory, legacy_path):
        if os.path.exists(directory):
            rmtree(directory)
            output.write_line(f'Cleaned {directory}.')
    return 0
