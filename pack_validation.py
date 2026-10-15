"""Check EF-12 template dependencies before spending time converting motions."""
from pathlib import Path


def validate_template(root):
    root = Path(root)
    # Stock Dummy.fmdl is an empty placeholder. Do not reject it for having no FMDL header.
    if not (root / 'mdl' / 'Dummy.fmdl').is_file():
        raise ValueError(
            'EF-12 template is missing mdl/Dummy.fmdl. Copy this standard placeholder '
            'from a stock character in your EF-12 installation into the prepared '
            'template; omitting it can prevent the game from loading.'
        )
