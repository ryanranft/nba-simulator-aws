Database Operations
===================

Database connection and query utilities for PostgreSQL temporal panel data storage.

Connection Management
---------------------

.. automodule:: nba_simulator.database.connection
   :members:
   :undoc-members:
   :show-inheritance:

Query Utilities
---------------

Database query helpers and temporal query builders (Phase 3 implementation).

Configuration
-------------

Database configuration is managed via ``config/database_config.yaml``:

.. code-block:: yaml

   database:
     host: localhost
     port: 5432
     name: nba_simulator
     user: nba_user
     # password from environment variable
