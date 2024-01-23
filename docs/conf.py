#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Robusta documentation build configuration file, created by
# sphinx-quickstart on Wed Apr 28 13:48:20 2021.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# add the root robusta directory to the path so that playbooks/ becomes importable
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / Path("_ext")))
sys.path.insert(0, str(Path(__file__).parent.parent))  # so we can import the playbooks

# -- Custom Sidebar -------------------------------------------------------


# -- General configuration ------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.graphviz",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.autosummary",
    "sphinxcontrib.mermaid",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",
    "sphinx_design",
    "sphinxcontrib.images",
    "autorobusta",
    "sphinx_immaterial",
    "sphinxcontrib.details.directive",
    "sphinx_jinja",
    "sphinx_reredirects",
]

suppress_warnings = ["autosectionlabel.*"]

# sphinx redirects from old docs

redirects = {
    # General pattern for all 'catalog' subdirectories
    "catalog/*/index.html": "/exp-redirects/playbook-reference/{1}/index.html",
    # General pattern for user-guide sections
    "user-guide/*.html": "/exp-redirects/configuration/{1}.html",
    # Specific redirects for unique pages
    "installation.html": "/exp-redirects/setup-robusta/installation/index.html",
    "architecture.html": "/exp-redirects/how-it-works/architecture.html",
    "upgrade.html": "/exp-redirects/setup-robusta/upgrade.html",
    "oss-vs-saas.html": "/exp-redirects/how-it-works/oss-vs-saas.html",
    "getting-started/installation.html": "/exp-redirects/setup-robusta/installation/all-in-one-installation.html",
    "community.html": "/exp-redirects/help.html",
    "quick-start.html": "/exp-redirects/setup-robusta/installation/index.html",
    # Developer guide with a deeper path
    "developer-guide/actions/*.html": "/exp-redirects/playbook-reference/actions/develop-actions/{1}.html",
    # Tutorials with specific new paths
    "tutorials/*.html": "/exp-redirects/tutorials/{1}.html",
    # Docs with a specific redirection
    "docs/configuration/*.html": "/exp-redirects/configuration/{1}.html",
}

# for sphinx_jinja - see https://github.com/tardyp/sphinx-jinja
jinja_contexts = {}

jinja_filters = {"to_snake_case": lambda s: "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")}

# for sphinx.ext.inheritance_diagram
# inheritance_graph_attrs = dict(rankdir="TB", size='""')

images_config = {
    "override_image_directive": True,
}

smartquotes = False

autodoc_mock_imports = ["prometheus_api_client"]
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    # 'special-members': '__init__',
    "undoc-members": True,
    # 'exclude-members': '__weakref__'
}
autoclass_content = "both"
add_module_names = False


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = [".rst", ".md"]

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "Robusta"
copyright = "2024, Robusta"
author = "Natan Yellin and Pavan Gudiwada"

# The short X.Y version.
# version = "DOCS_VERSION_PLACEHOLDER"
# The full version, including alpha/beta/rc tags.
# release = "DOCS_RELEASE_PLACEHOLDER"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**/*.inc.rst", "**/*.jinja"]

# The name of the Pygments (syntax highlighting) style to use.
# pygments_style = "manni"
# pygments_dark_style = "monokai"
pygments_style = "witchhazel.WitchHazelStyle"
pygments_dark_style = "witchhazel.WitchHazelStyle"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

html_theme = "sphinx_immaterial"

html_logo = "_static/logo_default.svg"

html_theme_options = {
    "icon": {
        "repo": "fontawesome/brands/github",
    },
    "repo_url": "https://github.com/robusta-dev/robusta",
    "repo_name": "Robusta",
    "repo_type": "github",
    "edit_uri": "tree/exp-redirects/docs",
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "robusta",
            "accent": "robusta",
            "toggle": {
                "icon": "material/weather-night",
                "name": "Switch to dark mode",
            },
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "robusta-dark",
            "accent": "robusta-dark",
            "toggle": {
                "icon": "material/weather-sunny",
                "name": "Switch to light mode",
            },
        },
    ],
    "features": [
        "navigation.instant",
        "navigation.top",
        "navigation.tabs",
        "navigation.tabs.sticky",
        "search.share",
        "toc.follow",
        "toc.sticky",
    ],
    "globaltoc_collapse": False,
    "social": [
        {
            "icon": "fontawesome/brands/github",
            "link": "https://github.com/robusta-dev/robusta",
        },
        {
            "icon": "fontawesome/brands/slack",
            "link": "https://bit.ly/robusta-slack",
        },
        {
            "icon": "fontawesome/brands/twitter",
            "link": "https://twitter.com/RobustaDev",
        },
        {
            "icon": "fontawesome/brands/linkedin",
            "link": "https://www.linkedin.com/company/robusta-dev/",
        },
    ],
}

html_sidebars = {"**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]}

copybutton_prompt_text = r"$ "
# html_title = ""

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_css_files = [
    "custom.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css",
]

html_js_files = ["analytics.js"]

html_favicon = "_static/favicon.png"

html_favicon = "_static/faviconNew.svg"

html_extra_path = ["robots.txt"]


def setup(app):
    app.add_css_file("custom.css")
