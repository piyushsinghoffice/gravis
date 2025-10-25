"""Template system for using HTML template files and inserting data into them."""

import json as _json
from importlib import resources


def load(resource_path):
    """Load a file in the same directory as the template system module."""
    # The package is the current module's package
    resource_package = __package__
    # Use importlib.resources to open the file as text
    with resources.files(resource_package).joinpath(resource_path).open('r', encoding='utf-8') as f:
        return f.read()


def insert(template, data):
    """Insert data into a template."""
    for key, val in data.items():
        tag = f'§{key}§'
        template = template.replace(tag, val)
    return template


def to_json(data):
    """Convert data to JSON."""
    return _json.dumps(data)