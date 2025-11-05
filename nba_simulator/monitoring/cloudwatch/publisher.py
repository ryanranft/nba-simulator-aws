#!/usr/bin/env python3
"""
NBA Simulator - CloudWatch Metrics Publisher

Publishes monitoring metrics to AWS CloudWatch for native AWS monitoring.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None

logger = logging.getLogger(__name__)

class MetricNamespace(Enum):
    """CloudWatch metric namespaces"""
    DIMS = "NBA-Simulator/DIMS"
    SCRAPERS = "NBA-Simulator/Scrapers"
    DATABASE = "NBA-Simulator/Database"
    HEALTH = "NBA-Simulator/Health"
    COST = "NBA-Simulator/Cost"

class MetricUnit(Enum):
    """CloudWatch metric units"""
    COUNT = "Count"
    PERCENT = "Percent"
    BYTES = "Bytes"
    SECONDS = "Seconds"
    NONE = "None"

@dataclass
class CloudWatchMetric:
    """Represents a CloudWatch metric"""
    namespace: str
    name: str
    value: float
    unit: str
    dimensions: Dict[str, str]
    timestamp: Optional[datetime] = None
    
    def to_boto3_format(self) -> Dict[str, Any]:
        """Convert to boto3 format"""
        metric = {
            'MetricName': self.name,
            'Value': self.value,
            'Unit': self.unit,
            'Dimensions': [{'Name': k, 'Value': v} for k, v in self.dimensions.items()]
        }
        if self.timestamp:
            metric['Timestamp'] = self.timestamp
        return metric

class CloudWatchPublisher:
    """Publishes metrics to AWS CloudWatch with batching and cost optimization"""
    
    def __init__(self, region: str = 'us-east-1', cost_optimized: bool = True):
        self.region = region
        self.cost_optimized = cost_optimized
        self.client = None
        self._metric_buffer: List[CloudWatchMetric] = []
        self._buffer_size = 20
        
        if boto3:
            try:
                self.client = boto3.client('cloudwatch', region_name=region)
                logger.info(f"CloudWatch client initialized for {region}")
            except Exception as e:
                logger.error(f"Failed to initialize CloudWatch: {e}")
    
    async def publish_metric(
        self,
        namespace: MetricNamespace,
        name: str,
        value: float,
        unit: MetricUnit = MetricUnit.COUNT,
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Publish a single metric"""
        if not self.client:
            return False
        
        if self.cost_optimized and not self._is_critical_metric(name):
            return False
        
        metric = CloudWatchMetric(
            namespace=namespace.value,
            name=name,
            value=value,
            unit=unit.value,
            dimensions=dimensions or {},
            timestamp=timestamp or datetime.now()
        )
        
        self._metric_buffer.append(metric)
        
        if len(self._metric_buffer) >= self._buffer_size:
            return await self.flush()
        
        return True
    
    async def flush(self) -> bool:
        """Flush buffered metrics"""
        if not self._metric_buffer or not self.client:
            self._metric_buffer.clear()
            return False
        
        try:
            namespaces: Dict[str, List[CloudWatchMetric]] = {}
            for metric in self._metric_buffer:
                if metric.namespace not in namespaces:
                    namespaces[metric.namespace] = []
                namespaces[metric.namespace].append(metric)
            
            for namespace, metrics in namespaces.items():
                for i in range(0, len(metrics), self._buffer_size):
                    batch = metrics[i:i + self._buffer_size]
                    self.client.put_metric_data(
                        Namespace=namespace,
                        MetricData=[m.to_boto3_format() for m in batch]
                    )
                    logger.info(f"Published {len(batch)} metrics to {namespace}")
            
            self._metric_buffer.clear()
            return True
        except Exception as e:
            logger.error(f"Error publishing to CloudWatch: {e}")
            self._metric_buffer.clear()
            return False
    
    def _is_critical_metric(self, metric_name: str) -> bool:
        """Check if metric is critical"""
        critical_keywords = ['error', 'failure', 'critical', 'cost', 'verification', 'health', 'alert']
        return any(kw in metric_name.lower() for kw in critical_keywords)

class DIMSCloudWatchPublisher:
    """Publishes DIMS metrics to CloudWatch"""
    
    def __init__(self, publisher: CloudWatchPublisher):
        self.publisher = publisher
    
    async def publish_verification_results(self, run_id: str, results: List[Dict[str, Any]]) -> bool:
        """Publish DIMS verification results"""
        total = len(results)
        passed = sum(1 for r in results if r.get('passed', False))
        
        await self.publisher.publish_metric(
            namespace=MetricNamespace.DIMS,
            name='VerificationsPassed',
            value=passed,
            dimensions={'RunID': run_id}
        )
        await self.publisher.publish_metric(
            namespace=MetricNamespace.DIMS,
            name='VerificationsFailed',
            value=total - passed,
            dimensions={'RunID': run_id}
        )
        return True

__all__ = ['CloudWatchPublisher', 'DIMSCloudWatchPublisher', 'MetricNamespace', 'MetricUnit']
