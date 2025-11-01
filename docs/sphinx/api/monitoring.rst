Monitoring & Observability API
==============================

This module provides comprehensive monitoring and observability for the NBA Simulator.

CloudWatch Metrics Publishers
------------------------------

DIMS Metrics Publisher
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: scripts.monitoring.cloudwatch.publish_dims_metrics
   :members:
   :undoc-members:
   :show-inheritance:

ADCE Metrics Publisher
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: scripts.monitoring.cloudwatch.publish_adce_metrics
   :members:
   :undoc-members:
   :show-inheritance:

S3 Metrics Publisher
~~~~~~~~~~~~~~~~~~~~

.. automodule:: scripts.monitoring.cloudwatch.publish_s3_metrics
   :members:
   :undoc-members:
   :show-inheritance:

Cost Metrics Publisher
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: scripts.monitoring.cloudwatch.publish_cost_metrics
   :members:
   :undoc-members:
   :show-inheritance:

Performance Profiler
--------------------

.. automodule:: scripts.monitoring.cloudwatch.profiler
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
~~~~~~~~~~~~~

.. code-block:: python

   from scripts.monitoring.cloudwatch.profiler import profile_performance

   @profile_performance('DatabaseQuery')
   def query_database(sql):
       # Your database query code
       pass

DIMS (Data Inventory Management System)
----------------------------------------

.. automodule:: scripts.monitoring.dims.core
   :members:
   :undoc-members:
   :show-inheritance:
