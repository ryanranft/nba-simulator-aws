#!/usr/bin/env python3
"""
Week 2 Database Baseline Validator

Validates all 40 database tables and creates baseline snapshot for comparison.
Part of Phase 1 validation before proceeding to Phase 2.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("WEEK 2: DATABASE BASELINE VALIDATION")
print("=" * 70)
print()

# Test new package imports
try:
    from nba_simulator.database import DatabaseConnection, execute_query
    from nba_simulator.config import config
    print("✅ Successfully imported nba_simulator package")
except ImportError as e:
    print(f"❌ Failed to import nba_simulator: {e}")
    print("   Falling back to direct database connection...")
    # TODO: Add fallback connection method
    sys.exit(1)

print()


def get_all_tables() -> List[str]:
    """Get list of all tables in the database"""
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    try:
        results = execute_query(query)
        tables = [row['table_name'] for row in results]
        print(f"✅ Found {len(tables)} tables in database")
        return tables
    except Exception as e:
        print(f"❌ Failed to get table list: {e}")
        return []


def get_table_metrics(table_name: str) -> Dict[str, Any]:
    """Get detailed metrics for a table"""
    metrics = {
        'table_name': table_name,
        'record_count': None,
        'size_bytes': None,
        'size_pretty': None,
        'last_vacuum': None,
        'last_analyze': None,
        'n_tup_ins': None,
        'n_tup_upd': None,
        'n_tup_del': None,
        'error': None
    }
    
    try:
        # Get record count
        count_query = f"SELECT COUNT(*) as count FROM {table_name};"
        count_result = execute_query(count_query)
        metrics['record_count'] = count_result[0]['count']
        
        # Get table size
        size_query = f"""
        SELECT 
            pg_total_relation_size('{table_name}') as size_bytes,
            pg_size_pretty(pg_total_relation_size('{table_name}')) as size_pretty;
        """
        size_result = execute_query(size_query)
        metrics['size_bytes'] = size_result[0]['size_bytes']
        metrics['size_pretty'] = size_result[0]['size_pretty']
        
        # Get statistics
        stats_query = f"""
        SELECT 
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze,
            n_tup_ins,
            n_tup_upd,
            n_tup_del
        FROM pg_stat_user_tables 
        WHERE relname = '{table_name}';
        """
        stats_result = execute_query(stats_query)
        if stats_result:
            stats = stats_result[0]
            metrics['last_vacuum'] = str(stats.get('last_vacuum') or stats.get('last_autovacuum'))
            metrics['last_analyze'] = str(stats.get('last_analyze') or stats.get('last_autoanalyze'))
            metrics['n_tup_ins'] = stats.get('n_tup_ins')
            metrics['n_tup_upd'] = stats.get('n_tup_upd')
            metrics['n_tup_del'] = stats.get('n_tup_del')
        
    except Exception as e:
        metrics['error'] = str(e)
    
    return metrics


def validate_critical_tables(baseline: Dict[str, Any]) -> List[str]:
    """Validate critical tables have expected record counts"""
    issues = []
    
    # Expected baselines from documentation
    expected = {
        'games': {'min': 44000, 'max': 50000, 'expected': 44828},
        'play_by_play': {'min': 19000000, 'max': 21000000, 'expected': 19855984},
        'box_score_players': {'min': 400000, 'max': 450000, 'expected': 408833},
        'box_score_snapshots': {'min': 0, 'max': 10000, 'expected': 1},
    }
    
    for table_name, exp in expected.items():
        if table_name in baseline:
            actual = baseline[table_name].get('record_count', 0)
            
            if actual < exp['min'] or actual > exp['max']:
                issues.append(
                    f"⚠️  {table_name}: {actual:,} records "
                    f"(expected ~{exp['expected']:,}, range: {exp['min']:,}-{exp['max']:,})"
                )
            else:
                print(f"✅ {table_name}: {actual:,} records (within expected range)")
    
    return issues


def investigate_temporal_events() -> Dict[str, Any]:
    """Special investigation of temporal_events table (Critical Question #1)"""
    print("\n" + "=" * 70)
    print("CRITICAL QUESTION #1: What is temporal_events table?")
    print("=" * 70)
    
    investigation = {
        'question': 'What is temporal_events table (5.8 GB)?',
        'findings': {}
    }
    
    try:
        # Get table structure
        schema_query = """
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'temporal_events'
        ORDER BY ordinal_position;
        """
        schema = execute_query(schema_query)
        investigation['findings']['schema'] = schema
        
        print(f"\nTable Structure ({len(schema)} columns):")
        for col in schema[:10]:  # Show first 10 columns
            print(f"  - {col['column_name']}: {col['data_type']}")
        if len(schema) > 10:
            print(f"  ... and {len(schema) - 10} more columns")
        
        # Get sample records
        sample_query = "SELECT * FROM temporal_events LIMIT 5;"
        samples = execute_query(sample_query)
        investigation['findings']['sample_count'] = len(samples)
        
        print(f"\n✅ Sample records available: {len(samples)}")
        
        # Get total count and size
        count_query = "SELECT COUNT(*) as count FROM temporal_events;"
        size_query = """
        SELECT 
            pg_size_pretty(pg_total_relation_size('temporal_events')) as size
        FROM pg_tables WHERE tablename = 'temporal_events';
        """
        
        count_result = execute_query(count_query)
        size_result = execute_query(size_query)
        
        investigation['findings']['record_count'] = count_result[0]['count']
        investigation['findings']['size'] = size_result[0]['size'] if size_result else 'Unknown'
        
        print(f"✅ Total records: {count_result[0]['count']:,}")
        print(f"✅ Table size: {investigation['findings']['size']}")
        
        # Check for recent activity
        stats_query = """
        SELECT n_tup_ins, n_tup_upd, n_tup_del, last_autoanalyze
        FROM pg_stat_user_tables 
        WHERE relname = 'temporal_events';
        """
        stats = execute_query(stats_query)
        if stats:
            investigation['findings']['statistics'] = stats[0]
            print(f"✅ Recent inserts: {stats[0]['n_tup_ins']:,}")
            print(f"✅ Recent updates: {stats[0]['n_tup_upd']:,}")
            print(f"✅ Last analyzed: {stats[0]['last_autoanalyze']}")
        
        investigation['conclusion'] = "Investigation complete - see findings for details"
        
    except Exception as e:
        investigation['error'] = str(e)
        print(f"❌ Error investigating temporal_events: {e}")
    
    return investigation


def main():
    """Main validation workflow"""
    
    # Initialize results
    results = {
        'timestamp': datetime.now().isoformat(),
        'week': 2,
        'phase': '1_validation',
        'baseline': {},
        'validation': {
            'issues': [],
            'warnings': [],
            'passed': False
        },
        'critical_questions': {},
        'summary': {}
    }
    
    print("Step 1: Getting list of all tables...")
    print("-" * 70)
    tables = get_all_tables()
    
    if not tables:
        print("❌ No tables found. Cannot continue validation.")
        sys.exit(1)
    
    print()
    print("Step 2: Collecting metrics for each table...")
    print("-" * 70)
    
    for i, table_name in enumerate(tables, 1):
        print(f"[{i}/{len(tables)}] Analyzing {table_name}...", end=" ")
        
        metrics = get_table_metrics(table_name)
        results['baseline'][table_name] = metrics
        
        if metrics['error']:
            print(f"❌ Error: {metrics['error']}")
            results['validation']['issues'].append(f"{table_name}: {metrics['error']}")
        else:
            count = metrics['record_count']
            size = metrics['size_pretty']
            print(f"✅ {count:,} records, {size}")
    
    print()
    print("Step 3: Validating critical tables...")
    print("-" * 70)
    
    critical_issues = validate_critical_tables(results['baseline'])
    results['validation']['issues'].extend(critical_issues)
    
    if not critical_issues:
        print("\n✅ All critical tables validated successfully!")
    else:
        print(f"\n⚠️  Found {len(critical_issues)} issue(s) with critical tables:")
        for issue in critical_issues:
            print(f"  {issue}")
    
    # Investigate temporal_events (Critical Question #1)
    results['critical_questions']['temporal_events'] = investigate_temporal_events()
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    total_tables = len(tables)
    tables_with_data = sum(1 for m in results['baseline'].values() 
                          if m['record_count'] and m['record_count'] > 0)
    tables_with_errors = sum(1 for m in results['baseline'].values() if m['error'])
    
    total_records = sum(m['record_count'] for m in results['baseline'].values() 
                       if m['record_count'])
    total_size_bytes = sum(m['size_bytes'] for m in results['baseline'].values() 
                          if m['size_bytes'])
    total_size_gb = total_size_bytes / (1024**3)
    
    results['summary'] = {
        'total_tables': total_tables,
        'tables_with_data': tables_with_data,
        'tables_with_errors': tables_with_errors,
        'total_records': total_records,
        'total_size_gb': round(total_size_gb, 2),
        'validation_passed': len(results['validation']['issues']) == 0
    }
    
    print(f"\nTotal tables: {total_tables}")
    print(f"Tables with data: {tables_with_data}")
    print(f"Tables with errors: {tables_with_errors}")
    print(f"Total records: {total_records:,}")
    print(f"Total database size: {total_size_gb:.2f} GB")
    print()
    
    if results['validation']['issues']:
        print(f"❌ VALIDATION FAILED: {len(results['validation']['issues'])} issue(s) found")
        results['validation']['passed'] = False
    else:
        print("✅ VALIDATION PASSED: All checks successful!")
        results['validation']['passed'] = True
    
    # Save baseline snapshot
    output_dir = project_root / "backups"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"week2_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print()
    print(f"📁 Baseline saved to: {output_file}")
    print()
    
    # Exit code
    sys.exit(0 if results['validation']['passed'] else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

