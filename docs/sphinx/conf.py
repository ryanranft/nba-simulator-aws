"""
Sphinx configuration for NBA Simulator documentation.

Phase 0.0021: Documentation & API Standards
"""

import os
import sys

# Add project root to path for autodoc
sys.path.insert(0, os.path.abspath("../.."))

# Project information
project = "NBA Simulator"
copyright = "2025, NBA Simulator Team"
author = "NBA Simulator Team"
version = "1.0"
release = "1.0.0"

# Extensions
extensions = [
    "sphinx.ext.autodoc",  # Auto-generate docs from docstrings
    "sphinx.ext.napoleon",  # Support for Google/NumPy style docstrings
    "sphinx.ext.viewcode",  # Add links to source code
    "sphinx.ext.todo",  # Support for TODO directives
    "sphinx.ext.coverage",  # Check documentation coverage
    "sphinx.ext.intersphinx",  # Link to other project docs
    "sphinx.ext.githubpages",  # Generate .nojekyll for GitHub Pages
]

# Napoleon settings (for Google/NumPy docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"
autodoc_mock_imports = ["boto3", "botocore", "pandas", "numpy", "scipy", "sklearn"]

# Templates
templates_path = ["_templates"]

# Source file patterns
source_suffix = ".rst"
master_doc = "index"

# Exclude patterns
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# HTML output options
html_theme = "alabaster"
html_static_path = ["_static"]
html_theme_options = {
    "description": "Temporal panel data system for NBA analysis",
    "github_user": "nba-simulator",
    "github_repo": "nba-simulator-aws",
    "fixed_sidebar": True,
    "page_width": "1200px",
}

# HTML page options
html_title = f"{project} v{version}"
html_short_title = project
html_show_sourcelink = True
html_show_sphinx = False
html_show_copyright = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

# TODO extension settings
todo_include_todos = True

# Coverage settings
coverage_show_missing_items = True
