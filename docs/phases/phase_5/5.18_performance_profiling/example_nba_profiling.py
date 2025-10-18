#!/usr/bin/env python3
"""NBA Performance Profiling Example - MCP Recommendation #26"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
from scripts.ml.performance_profiling import PerformanceProfiler

profiler = PerformanceProfiler()
print("✅ Performance Profiling: Memory, speed, throughput analysis")
print("Optimization: Identify bottlenecks before production deployment")
