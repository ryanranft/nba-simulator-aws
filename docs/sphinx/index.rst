NBA Simulator Documentation
===========================

Welcome to the NBA Simulator technical documentation. This system creates a temporal panel data platform
for millisecond-precision NBA historical analysis with advanced machine learning and causal inference.

**Core Capability:** Query cumulative NBA statistics at any exact moment in time.

Quick Links
-----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/monitoring
   api/autonomous
   api/database
   api/utils

Overview
--------

The NBA Simulator is a temporal panel data system that enables snapshot queries of NBA history
at exact timestamps with millisecond precision, powering context-aware game simulations.

Example queries:

* "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"
* "What was the NBA's average pace at 11:23:45.678 PM on March 15, 2023?"
* "Show me the complete game state (score, possession, lineup) at 8:45:30 PM on May 1, 2024"

Architecture
------------

The system consists of six main phases:

**Phase 0: Data Collection & Infrastructure**
   Autonomous data collection from multiple sources (ESPN, NBA API, Basketball Reference, hoopR)
   with comprehensive monitoring and observability.

**Phase 1: Multi-Source Integration**
   S3-based deduplication, unified schemas, and data quality validation.

**Phase 2: PostgreSQL Database**
   Temporal panel data storage with millisecond-precision indexing.

**Phase 3: Temporal Query Engine**
   Advanced SQL queries for snapshot statistics at any point in time.

**Phase 4: Simulation Framework**
   Context-adaptive simulations using econometric and nonparametric models.

**Phase 5: Machine Learning Models**
   Advanced ML for predictions, causal inference, and performance analysis.

Key Features
------------

* **Autonomous Data Collection (ADCE)**: Self-healing data collection with 15-minute reconciliation
* **Real-time Monitoring**: CloudWatch integration with dashboards and alarms
* **Data Integrity**: DIMS (Data Inventory Management System) with drift detection
* **Performance Profiling**: Automated performance tracking and optimization
* **Cost Management**: Budget tracking and automated cost alerts

API Documentation
-----------------

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   api/monitoring
   api/autonomous
   api/database
   api/utils

Monitoring & Observability
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: scripts.monitoring.cloudwatch.publish_dims_metrics
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: scripts.monitoring.cloudwatch.publish_adce_metrics
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: scripts.monitoring.cloudwatch.profiler
   :members:
   :undoc-members:
   :show-inheritance:

Autonomous Data Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :doc:`api/autonomous` for ADCE documentation.

Database Operations
~~~~~~~~~~~~~~~~~~~

See :doc:`api/database` for database connection and query documentation.

Utilities
~~~~~~~~~

See :doc:`api/utils` for utility functions and helpers.

Getting Started
---------------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   # Clone repository
   git clone https://github.com/nba-simulator/nba-simulator-aws.git
   cd nba-simulator-aws

   # Create conda environment
   conda env create -f environment.yml
   conda activate nba-aws

   # Configure AWS credentials
   aws configure

Quick Start
~~~~~~~~~~~

.. code-block:: bash

   # Start autonomous data collection
   python scripts/autonomous/autonomous_cli.py start

   # Check system health
   python scripts/autonomous/autonomous_cli.py status

   # Verify data inventory
   python scripts/monitoring/dims_cli.py verify

Configuration
-------------

See ``config/`` directory for configuration files:

* ``config/autonomous_config.yaml`` - ADCE configuration
* ``config/cloudwatch_config.yaml`` - Monitoring configuration
* ``config/scraper_config.yaml`` - Scraper configuration

Documentation Standards
-----------------------

This project follows comprehensive documentation standards defined in:

* ``docs/DOCSTRING_STANDARDS.md`` - Python docstring guidelines
* ``docs/API_VERSIONING_POLICY.md`` - API versioning strategy
* ``docs/DEVELOPER_ONBOARDING.md`` - Developer onboarding guide

Contributing
------------

See ``docs/DEVELOPER_ONBOARDING.md`` for contribution guidelines.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
