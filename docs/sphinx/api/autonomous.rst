Autonomous Data Collection Engine (ADCE)
=========================================

The Autonomous Data Collection Engine (ADCE) manages automated data scraping,
reconciliation, and storage operations.

Overview
--------

ADCE provides:

* **Autonomous Operation**: Self-healing data collection with minimal intervention
* **Multi-Source Support**: ESPN, NBA API, Basketball Reference, hoopR
* **15-Minute Reconciliation**: Automatic gap detection and task generation
* **Priority Queue**: Weighted scoring system for task prioritization
* **Parallel Execution**: ThreadPoolExecutor with rate limiting
* **Real-time Monitoring**: Health monitoring via HTTP endpoints

Health Monitor
--------------

The health monitor provides real-time status via HTTP endpoints:

* ``GET /status`` - Comprehensive system status
* ``GET /health`` - Simple health check
* ``GET /tasks`` - Task queue status

Command Line Interface
----------------------

.. code-block:: bash

   # Start ADCE
   python scripts/autonomous/autonomous_cli.py start

   # Check status
   python scripts/autonomous/autonomous_cli.py status

   # Stop ADCE
   python scripts/autonomous/autonomous_cli.py stop

Configuration
-------------

ADCE is configured via ``config/autonomous_config.yaml``:

.. code-block:: yaml

   reconciliation_interval_minutes: 15
   task_queue_check_interval_seconds: 10
   max_concurrent_scrapers: 5
   priority_weighting:
     enabled: true
     base_scores:
       CRITICAL: 1000
       HIGH: 100
       MEDIUM: 10
       LOW: 1
