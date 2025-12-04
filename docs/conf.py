# docs/conf.py

import os
import sys
sys.path.insert(0, os.path.abspath(".."))  # so Sphinx can find your package

project = "Iowa State Agronomy Farm Soil Mapping"
author = "Alex Cecil"
release = "0.1.0"

# General configuration
extensions = [
    "myst_parser",            # Enables Markdown
    "sphinx.ext.autodoc",     # Optional: auto-generate API docs
    "sphinx.ext.napoleon",    # Optional: parse Google/Numpy-style docstrings
]

templates_path = ["_templates"]
exclude_patterns = []

# Recognize both .md and .rst files
source_suffix = [".rst", ".md"]

# Use 'index.md' as the root document
master_doc = "index"

# HTML output options
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
