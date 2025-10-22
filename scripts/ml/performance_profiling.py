"""
Performance Profiling Framework

Implements comprehensive performance analysis and optimization:
- Memory profiling (peak usage, allocations)
- Execution time analysis
- Throughput measurement (predictions/second)
- Resource utilization tracking
- Bottleneck identification
- Optimization recommendations
- Scalability analysis
- Hardware utilization metrics

Author: NBA Simulator Project
Created: 2025-10-18
"""

import logging
import time
import psutil
import gc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
import json
import numpy as np
import pandas as pd
from pathlib import Path
import warnings
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class MemoryProfile:
    """Store memory profiling results."""
    peak_memory_mb: float
    baseline_memory_mb: float
    memory_increase_mb: float
    gc_collections: Dict[str, int]
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'peak_memory_mb': float(self.peak_memory_mb),
            'baseline_memory_mb': float(self.baseline_memory_mb),
            'memory_increase_mb': float(self.memory_increase_mb),
            'gc_collections': {k: int(v) for k, v in self.gc_collections.items()},
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


@dataclass
class TimeProfile:
    """Store timing profiling results."""
    total_time: float
    avg_time_per_sample: float
    throughput_samples_per_sec: float
    breakdown: Dict[str, float]
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_time': float(self.total_time),
            'avg_time_per_sample': float(self.avg_time_per_sample),
            'throughput_samples_per_sec': float(self.throughput_samples_per_sec),
            'breakdown': {k: float(v) for k, v in self.breakdown.items()},
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


@dataclass
class PerformanceReport:
    """Store comprehensive performance report."""
    memory_profile: MemoryProfile
    time_profile: TimeProfile
    system_stats: Dict[str, float]
    bottlenecks: List[str]
    recommendations: List[str]
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'memory_profile': self.memory_profile.to_dict(),
            'time_profile': self.time_profile.to_dict(),
            'system_stats': {k: float(v) for k, v in self.system_stats.items()},
            'bottlenecks': self.bottlenecks,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class PerformanceProfiler:
    """
    Comprehensive performance profiling framework.

    Provides methods for:
    - Memory profiling
    - Execution time analysis
    - Throughput measurement
    - Resource utilization
    - Bottleneck identification
    - Optimization recommendations
    """

    def __init__(self):
        """Initialize performance profiler."""
        self.logger = logging.getLogger(__name__)
        self.process = psutil.Process()
        self.logger.info("Initialized PerformanceProfiler")

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def profile_memory(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, MemoryProfile]:
        """
        Profile memory usage of a function.

        Parameters
        ----------
        func : Callable
            Function to profile
        *args : Any
            Function arguments
        **kwargs : Any
            Function keyword arguments

        Returns
        -------
        Tuple[Any, MemoryProfile]
            Function result and memory profile
        """
        self.logger.info(f"Profiling memory for {func.__name__}")

        # Force garbage collection before measurement
        gc.collect()

        # Get baseline
        baseline_memory = self.get_memory_usage()
        baseline_gc = gc.get_count()

        # Run function
        result = func(*args, **kwargs)

        # Force GC again
        gc.collect()

        # Get peak memory
        peak_memory = self.get_memory_usage()
        final_gc = gc.get_count()

        # Calculate GC collections
        gc_collections = {
            'gen0': final_gc[0] - baseline_gc[0],
            'gen1': final_gc[1] - baseline_gc[1],
            'gen2': final_gc[2] - baseline_gc[2]
        }

        profile = MemoryProfile(
            peak_memory_mb=peak_memory,
            baseline_memory_mb=baseline_memory,
            memory_increase_mb=peak_memory - baseline_memory,
            gc_collections=gc_collections,
            timestamp=datetime.now().isoformat(),
            metadata={'function': func.__name__}
        )

        return result, profile

    def profile_time(
        self,
        func: Callable,
        n_samples: int,
        *args,
        **kwargs
    ) -> Tuple[Any, TimeProfile]:
        """
        Profile execution time of a function.

        Parameters
        ----------
        func : Callable
            Function to profile
        n_samples : int
            Number of samples being processed
        *args : Any
            Function arguments
        **kwargs : Any
            Function keyword arguments

        Returns
        -------
        Tuple[Any, TimeProfile]
            Function result and time profile
        """
        self.logger.info(f"Profiling time for {func.__name__}")

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        total_time = end_time - start_time
        avg_time_per_sample = total_time / n_samples if n_samples > 0 else 0
        throughput = n_samples / total_time if total_time > 0 else 0

        profile = TimeProfile(
            total_time=total_time,
            avg_time_per_sample=avg_time_per_sample,
            throughput_samples_per_sec=throughput,
            breakdown={'function': total_time},
            timestamp=datetime.now().isoformat(),
            metadata={'function': func.__name__, 'n_samples': n_samples}
        )

        return result, profile

    def profile_comprehensive(
        self,
        func: Callable,
        n_samples: int,
        *args,
        **kwargs
    ) -> Tuple[Any, MemoryProfile, TimeProfile]:
        """
        Profile both memory and time.

        Parameters
        ----------
        func : Callable
            Function to profile
        n_samples : int
            Number of samples
        *args : Any
            Function arguments
        **kwargs : Any
            Function keyword arguments

        Returns
        -------
        Tuple[Any, MemoryProfile, TimeProfile]
            Function result, memory profile, time profile
        """
        self.logger.info(f"Comprehensive profiling for {func.__name__}")

        # Force GC
        gc.collect()

        # Baseline
        baseline_memory = self.get_memory_usage()
        baseline_gc = gc.get_count()

        # Time and run
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        # Memory after
        gc.collect()
        peak_memory = self.get_memory_usage()
        final_gc = gc.get_count()

        # Memory profile
        memory_profile = MemoryProfile(
            peak_memory_mb=peak_memory,
            baseline_memory_mb=baseline_memory,
            memory_increase_mb=peak_memory - baseline_memory,
            gc_collections={
                'gen0': final_gc[0] - baseline_gc[0],
                'gen1': final_gc[1] - baseline_gc[1],
                'gen2': final_gc[2] - baseline_gc[2]
            },
            timestamp=datetime.now().isoformat(),
            metadata={'function': func.__name__}
        )

        # Time profile
        total_time = end_time - start_time
        time_profile = TimeProfile(
            total_time=total_time,
            avg_time_per_sample=total_time / n_samples if n_samples > 0 else 0,
            throughput_samples_per_sec=n_samples / total_time if total_time > 0 else 0,
            breakdown={'function': total_time},
            timestamp=datetime.now().isoformat(),
            metadata={'function': func.__name__, 'n_samples': n_samples}
        )

        return result, memory_profile, time_profile

    def get_system_stats(self) -> Dict[str, float]:
        """
        Get current system resource statistics.

        Returns
        -------
        Dict[str, float]
            System statistics
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cpu_percent': cpu_percent,
            'memory_total_gb': memory.total / 1024 ** 3,
            'memory_available_gb': memory.available / 1024 ** 3,
            'memory_percent': memory.percent,
            'disk_total_gb': disk.total / 1024 ** 3,
            'disk_used_gb': disk.used / 1024 ** 3,
            'disk_percent': disk.percent
        }

    def identify_bottlenecks(
        self,
        memory_profile: MemoryProfile,
        time_profile: TimeProfile,
        system_stats: Dict[str, float]
    ) -> List[str]:
        """
        Identify performance bottlenecks.

        Parameters
        ----------
        memory_profile : MemoryProfile
            Memory profiling results
        time_profile : TimeProfile
            Time profiling results
        system_stats : Dict[str, float]
            System statistics

        Returns
        -------
        List[str]
            Identified bottlenecks
        """
        bottlenecks = []

        # Memory bottlenecks
        if memory_profile.memory_increase_mb > 1000:  # >1GB increase
            bottlenecks.append(
                f"High memory allocation: {memory_profile.memory_increase_mb:.1f}MB increase"
            )

        if memory_profile.gc_collections['gen2'] > 5:
            bottlenecks.append(
                f"Excessive garbage collection: {memory_profile.gc_collections['gen2']} gen2 collections"
            )

        # Time bottlenecks
        if time_profile.throughput_samples_per_sec < 100:  # <100 samples/sec
            bottlenecks.append(
                f"Low throughput: {time_profile.throughput_samples_per_sec:.1f} samples/sec"
            )

        if time_profile.avg_time_per_sample > 0.01:  # >10ms per sample
            bottlenecks.append(
                f"Slow per-sample processing: {time_profile.avg_time_per_sample*1000:.2f}ms/sample"
            )

        # System bottlenecks
        if system_stats['cpu_percent'] > 90:
            bottlenecks.append(f"High CPU utilization: {system_stats['cpu_percent']:.1f}%")

        if system_stats['memory_percent'] > 85:
            bottlenecks.append(f"High memory utilization: {system_stats['memory_percent']:.1f}%")

        return bottlenecks

    def generate_recommendations(
        self,
        memory_profile: MemoryProfile,
        time_profile: TimeProfile,
        bottlenecks: List[str]
    ) -> List[str]:
        """
        Generate optimization recommendations.

        Parameters
        ----------
        memory_profile : MemoryProfile
            Memory profiling results
        time_profile : TimeProfile
            Time profiling results
        bottlenecks : List[str]
            Identified bottlenecks

        Returns
        -------
        List[str]
            Optimization recommendations
        """
        recommendations = []

        # Memory recommendations
        if memory_profile.memory_increase_mb > 1000:
            recommendations.append(
                "💾 High memory usage detected. Consider: "
                "(1) Batch processing, (2) Memory-efficient data types, "
                "(3) Streaming instead of loading all data"
            )

        if memory_profile.gc_collections['gen2'] > 5:
            recommendations.append(
                "♻️ Excessive GC detected. Consider: "
                "(1) Object pooling, (2) Reduce temporary object creation, "
                "(3) Use generators instead of lists"
            )

        # Time recommendations
        if time_profile.throughput_samples_per_sec < 100:
            recommendations.append(
                "⚡ Low throughput detected. Consider: "
                "(1) Vectorization, (2) Parallel processing, "
                "(3) Model optimization (pruning, quantization)"
            )

        if time_profile.avg_time_per_sample > 0.01:
            recommendations.append(
                "🚀 Slow processing detected. Consider: "
                "(1) Caching predictions, (2) Feature precomputation, "
                "(3) Model simplification"
            )

        # General recommendations
        if not bottlenecks:
            recommendations.append(
                "✅ Performance looks good! No major bottlenecks detected."
            )

        return recommendations

    def create_report(
        self,
        memory_profile: MemoryProfile,
        time_profile: TimeProfile
    ) -> PerformanceReport:
        """
        Create comprehensive performance report.

        Parameters
        ----------
        memory_profile : MemoryProfile
            Memory profiling results
        time_profile : TimeProfile
            Time profiling results

        Returns
        -------
        PerformanceReport
            Complete performance report
        """
        system_stats = self.get_system_stats()
        bottlenecks = self.identify_bottlenecks(memory_profile, time_profile, system_stats)
        recommendations = self.generate_recommendations(memory_profile, time_profile, bottlenecks)

        return PerformanceReport(
            memory_profile=memory_profile,
            time_profile=time_profile,
            system_stats=system_stats,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )

    def export_report(self, output_path: str, report: PerformanceReport) -> None:
        """
        Export performance report to JSON file.

        Parameters
        ----------
        output_path : str
            Path to output file
        report : PerformanceReport
            Report to export
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

        self.logger.info(f"Report exported to {output_path}")


def demo_performance_profiling():
    """Demonstrate performance profiling framework."""
    logger.info("=== Performance Profiling Framework Demo ===\n")

    # Create output directory
    output_dir = Path("/tmp/performance_profiling")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize profiler
    profiler = PerformanceProfiler()

    # Demo workload: Train a model
    logger.info("--- Demo Workload: Training Random Forest ---")

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification

    # Create synthetic dataset
    def create_and_train_model():
        X, y = make_classification(
            n_samples=10000,
            n_features=50,
            n_informative=20,
            n_redundant=10,
            random_state=42
        )

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        model.fit(X, y)
        return model

    # Profile comprehensive
    result, memory_profile, time_profile = profiler.profile_comprehensive(
        create_and_train_model,
        10000  # n_samples for profiling metrics
    )

    # Display results
    logger.info("\n📊 Memory Profile:")
    logger.info(f"  Baseline: {memory_profile.baseline_memory_mb:.1f} MB")
    logger.info(f"  Peak: {memory_profile.peak_memory_mb:.1f} MB")
    logger.info(f"  Increase: {memory_profile.memory_increase_mb:.1f} MB")
    logger.info(f"  GC collections: {memory_profile.gc_collections}")

    logger.info("\n⏱️  Time Profile:")
    logger.info(f"  Total time: {time_profile.total_time:.4f} seconds")
    logger.info(f"  Avg time per sample: {time_profile.avg_time_per_sample*1000:.4f} ms")
    logger.info(f"  Throughput: {time_profile.throughput_samples_per_sec:.1f} samples/sec")

    # Create full report
    logger.info("\n--- Creating Performance Report ---")
    report = profiler.create_report(memory_profile, time_profile)

    logger.info("\n💻 System Stats:")
    for key, value in report.system_stats.items():
        logger.info(f"  {key}: {value:.2f}")

    if report.bottlenecks:
        logger.info("\n⚠️  Bottlenecks Detected:")
        for i, bottleneck in enumerate(report.bottlenecks, 1):
            logger.info(f"  {i}. {bottleneck}")
    else:
        logger.info("\n✅ No bottlenecks detected")

    logger.info("\n💡 Recommendations:")
    for i, rec in enumerate(report.recommendations, 1):
        logger.info(f"  {i}. {rec}")

    # Export report
    profiler.export_report(str(output_dir / "performance_report.json"), report)

    logger.info(f"\n✅ Performance profiling demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return report


if __name__ == '__main__':
    demo_performance_profiling()
