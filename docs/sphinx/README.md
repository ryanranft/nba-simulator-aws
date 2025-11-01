# NBA Simulator - Sphinx Documentation

Auto-generated API reference documentation for the NBA Simulator project.

**Phase 0.0021: Documentation & API Standards**

## Quick Start

### Prerequisites

```bash
pip install sphinx sphinx-rtd-theme
```

### Build Documentation

```bash
# From this directory (docs/sphinx/)
make html

# View in browser
make serve
# Open: http://localhost:8000
```

### Clean Build

```bash
make clean
make html
```

## What's Included

### Autodoc Modules

- **Monitoring & Observability** (`scripts/monitoring/cloudwatch/`)
  - DIMS metrics publisher
  - ADCE metrics publisher
  - S3 metrics publisher
  - Cost metrics publisher
  - Performance profiler

- **Autonomous Data Collection** (ADCE)
  - Health monitoring
  - Task queue management
  - Reconciliation daemon

- **Database Operations**
  - Connection management
  - Query utilities

- **Utilities**
  - Logging
  - Constants

### Configuration

**conf.py** includes:
- autodoc - Auto-generate from docstrings
- napoleon - Google/NumPy docstring support
- viewcode - Links to source code
- intersphinx - Links to external docs (Python, pandas, numpy)

## Output

Built documentation is generated in:
```
_build/html/index.html
```

## Deployment

### GitHub Pages

```bash
# Build docs
make html

# Deploy to gh-pages branch
cp -r _build/html/* /path/to/gh-pages-branch/
cd /path/to/gh-pages-branch
git add .
git commit -m "Update documentation"
git push origin gh-pages
```

### Read the Docs

1. Create `.readthedocs.yaml` in project root
2. Connect repository to Read the Docs
3. Auto-builds on git push

## Updating Documentation

### Add New Module

1. Create new .rst file in `api/`
2. Add to `index.rst` toctree
3. Use automodule directive:

```rst
My Module
=========

.. automodule:: scripts.my_module
   :members:
   :undoc-members:
   :show-inheritance:
```

### Rebuild

```bash
make clean
make html
```

## Documentation Standards

Follow the docstring standards defined in:
- `docs/DOCSTRING_STANDARDS.md`

## Troubleshooting

### Module Import Errors

If autodoc can't find modules:
1. Check `sys.path` in `conf.py`
2. Add to `autodoc_mock_imports` if needed

### Build Warnings

```bash
# Build with warnings as errors
make SPHINXOPTS="-W" html
```

---

**Created:** November 1, 2025
**Phase:** 0.0021 (Documentation & API Standards)
