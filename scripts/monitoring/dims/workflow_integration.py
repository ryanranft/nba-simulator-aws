"""
DIMS Workflow Integration Module

Integrates existing data inventory workflows with DIMS:
- Workflow #13: File Inventory
- Workflow #45: Local Data Inventory
- Workflow #46: Data Gap Analysis
- Workflow #47: AWS Data Inventory
- Workflow #49: Automated Data Audit
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkflowIntegration:
    """Helper class for running existing workflows and extracting results."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.workflows_dir = self.project_root / 'docs' / 'claude_workflows' / 'workflow_descriptions'

    def run_file_inventory(self, update: bool = True) -> Dict:
        """
        Run Workflow #13: File Inventory

        Generates docs/FILE_INVENTORY.md with metadata for all project files.

        Args:
            update: Whether to regenerate the inventory file

        Returns:
            Dict with:
                - total_files: Number of files documented
                - last_updated: Timestamp of inventory file
                - categories: Dict of file counts by category
        """
        inventory_file = self.project_root / 'docs' / 'FILE_INVENTORY.md'

        if update:
            logger.info("Generating file inventory...")
            # Command from workflow #13
            cmd = f"""
                cd {self.project_root} && python3 - <<'PYEOF'
import os
from pathlib import Path
from datetime import datetime

project_root = Path.cwd()
output_file = project_root / 'docs' / 'FILE_INVENTORY.md'

# Scan for important files
file_types = {{
    'Python Scripts': '**/*.py',
    'Shell Scripts': '**/*.sh',
    'SQL Files': '**/*.sql',
    'Markdown Docs': '**/*.md'
}}

with open(output_file, 'w') as f:
    f.write(f'# File Inventory\\n\\n')
    f.write(f'**Generated:** {{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}\\n\\n')

    for category, pattern in file_types.items():
        files = sorted(project_root.glob(pattern))
        f.write(f'## {{category}} ({{len(files)}})\\n\\n')

        for file_path in files:
            if '.git' not in str(file_path):
                rel_path = file_path.relative_to(project_root)
                f.write(f'### {{rel_path}}\\n\\n')

                # Try to extract docstring/description
                if file_path.suffix == '.py':
                    try:
                        with open(file_path) as src:
                            lines = src.readlines()[:10]
                            for line in lines:
                                if ('\"\"\"' in line) or (\"'''\" in line):
                                    f.write(f'{{line.strip()}}\\n')
                                    break
                    except:
                        pass

                f.write('\\n')

print(f'✓ File inventory generated: {{output_file}}')
PYEOF
            """

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode != 0:
                    logger.error(f"File inventory failed: {result.stderr}")
            except Exception as e:
                logger.error(f"Error running file inventory: {e}")

        # Parse results
        if not inventory_file.exists():
            return {
                'total_files': 0,
                'last_updated': None,
                'categories': {}
            }

        total_files = 0
        categories = {}

        with open(inventory_file) as f:
            content = f.read()
            total_files = content.count('###')

            # Parse categories
            for line in content.split('\n'):
                if line.startswith('## ') and '(' in line:
                    category = line.split('(')[0].replace('## ', '').strip()
                    count = int(line.split('(')[1].split(')')[0])
                    categories[category] = count

        last_updated = datetime.fromtimestamp(inventory_file.stat().st_mtime)

        return {
            'total_files': total_files,
            'last_updated': last_updated.isoformat(),
            'categories': categories
        }

    def run_local_data_inventory(self, mode: str = 'quick') -> Dict:
        """
        Run Workflow #45: Local Data Inventory

        Inventories local disk data (archives, project data, temp files).

        Args:
            mode: 'quick' (<30s) or 'full' (2-5 min)

        Returns:
            Dict with:
                - archives_size_gb: Size of archives directory
                - temp_size_gb: Size of temp directory
                - project_size_gb: Size of project directory
                - total_files: Total file count
        """
        logger.info(f"Running local data inventory ({mode} mode)...")

        result = {
            'archives_size_gb': 0,
            'temp_size_gb': 0,
            'project_size_gb': 0,
            'total_files': 0
        }

        # Check archives
        archives_dir = Path.home() / 'sports-simulator-archives' / 'nba'
        if archives_dir.exists():
            cmd = f"du -sg {archives_dir} 2>/dev/null | awk '{{print $1}}'"
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result['archives_size_gb'] = int(output.stdout.strip() or 0)
            except:
                pass

            if mode == 'full':
                cmd = f"find {archives_dir} -type f 2>/dev/null | wc -l"
                try:
                    output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                    result['total_files'] += int(output.stdout.strip() or 0)
                except:
                    pass

        # Check temp directory
        temp_dir = Path.home() / 'nba-sim-temp'
        if temp_dir.exists():
            cmd = f"du -sg {temp_dir} 2>/dev/null | awk '{{print $1}}'"
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result['temp_size_gb'] = int(output.stdout.strip() or 0)
            except:
                pass

        # Check project directory
        cmd = f"du -sg {self.project_root} 2>/dev/null | awk '{{print $1}}'"
        try:
            output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            result['project_size_gb'] = int(output.stdout.strip() or 0)
        except:
            pass

        logger.info(f"Local inventory complete: {result}")
        return result

    def run_aws_data_inventory(self) -> Dict:
        """
        Run Workflow #47: AWS Data Inventory

        Comprehensive AWS resource inventory with cost analysis.

        Returns:
            Dict with:
                - s3_objects: Total S3 objects
                - s3_size_gb: Total S3 size
                - rds_size_gb: RDS database size
                - rds_allocated_gb: RDS allocated storage
                - estimated_cost_usd: Monthly cost estimate
        """
        logger.info("Running AWS data inventory...")

        result = {
            's3_objects': 0,
            's3_size_gb': 0.0,
            'rds_size_gb': 0.0,
            'rds_allocated_gb': 0,
            'estimated_cost_usd': 0.0
        }

        # S3 metrics
        try:
            cmd = "aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize 2>/dev/null | grep 'Total Objects' | awk '{print $3}'"
            output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            result['s3_objects'] = int(output.stdout.strip() or 0)

            cmd = "aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize 2>/dev/null | grep 'Total Size' | awk '{print $3/1024/1024/1024}'"
            output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            result['s3_size_gb'] = float(output.stdout.strip() or 0)
        except Exception as e:
            logger.error(f"Error fetching S3 metrics: {e}")

        # RDS metrics (if credentials available)
        try:
            import os
            if os.environ.get('DB_HOST'):
                cmd = "psql -h $DB_HOST -U $DB_USER -d nba_simulator -t -c \"SELECT ROUND(pg_database_size('nba_simulator')::numeric / 1024 / 1024 / 1024, 2)\" 2>/dev/null | tr -d ' '"
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result['rds_size_gb'] = float(output.stdout.strip() or 0)

                cmd = "aws rds describe-db-instances --db-instance-identifier nba-simulator --query 'DBInstances[0].AllocatedStorage' --output text 2>/dev/null"
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result['rds_allocated_gb'] = int(output.stdout.strip() or 0)
        except Exception as e:
            logger.error(f"Error fetching RDS metrics: {e}")

        # Estimate costs
        s3_cost = result['s3_size_gb'] * 0.023  # $0.023/GB/month
        rds_cost = 20.0  # Base RDS cost
        result['estimated_cost_usd'] = round(s3_cost + rds_cost, 2)

        logger.info(f"AWS inventory complete: {result}")
        return result

    def run_data_gap_analysis(self) -> Dict:
        """
        Run Workflow #46: Data Gap Analysis

        Identifies missing data (games, play-by-play, player stats).

        Returns:
            Dict with:
                - missing_games: Number of games without box scores
                - games_without_pbp: Number of games without play-by-play
                - total_games: Total games in database
        """
        logger.info("Running data gap analysis...")

        result = {
            'missing_games': 0,
            'games_without_pbp': 0,
            'total_games': 0
        }

        try:
            import os
            if os.environ.get('DB_HOST'):
                # Games missing box scores
                cmd = "psql -h $DB_HOST -U $DB_USER -d nba_simulator -t -c \"SELECT COUNT(*) FROM (SELECT DISTINCT game_id FROM games EXCEPT SELECT DISTINCT game_id FROM box_scores) AS gaps\" 2>/dev/null | tr -d ' '"
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result['missing_games'] = int(output.stdout.strip() or 0)

                # Games without play-by-play
                cmd = "psql -h $DB_HOST -U $DB_USER -d nba_simulator -t -c \"SELECT COUNT(*) FROM (SELECT DISTINCT game_id FROM games EXCEPT SELECT DISTINCT game_id FROM play_by_play) AS gaps\" 2>/dev/null | tr -d ' '"
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result['games_without_pbp'] = int(output.stdout.strip() or 0)

                # Total games
                cmd = "psql -h $DB_HOST -U $DB_USER -d nba_simulator -t -c \"SELECT COUNT(*) FROM games\" 2>/dev/null | tr -d ' '"
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result['total_games'] = int(output.stdout.strip() or 0)
        except Exception as e:
            logger.error(f"Error running gap analysis: {e}")

        logger.info(f"Gap analysis complete: {result}")
        return result

    def run_sync_status_check(self) -> Dict:
        """
        Run Workflow #49: Sync Status Check

        Compares local vs S3 file counts and identifies drift.

        Returns:
            Dict with:
                - status: 'synced', 'minor_drift', 'moderate_drift', 'major_drift'
                - s3_files: File count in S3
                - local_files: File count locally
                - drift_pct: Drift percentage
        """
        logger.info("Running sync status check...")

        script_path = self.project_root / 'scripts' / 'monitoring' / 'check_sync_status.sh'

        try:
            # Run full mode to get details
            cmd = f"bash {script_path}"
            output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

            # Parse output
            lines = output.stdout.split('\n')
            result = {
                'status': 'unknown',
                's3_files': 0,
                'local_files': 0,
                'drift_pct': 0.0
            }

            for line in lines:
                if line.startswith('S3 Files:'):
                    result['s3_files'] = int(line.split(':')[1].strip())
                elif line.startswith('Local Files:'):
                    result['local_files'] = int(line.split(':')[1].strip())
                elif line.startswith('Drift:'):
                    result['drift_pct'] = float(line.split(':')[1].strip().replace('%', ''))
                elif line.startswith('Status:'):
                    result['status'] = line.split(':')[1].strip()

            logger.info(f"Sync status check complete: {result}")
            return result

        except Exception as e:
            logger.error(f"Error running sync status check: {e}")
            return {
                'status': 'error',
                's3_files': 0,
                'local_files': 0,
                'drift_pct': 0.0
            }

    def run_all_workflows(self, file_inventory: bool = True,
                         local_inventory: bool = True,
                         aws_inventory: bool = True,
                         gap_analysis: bool = True,
                         sync_status: bool = True) -> Dict:
        """
        Run all workflow integrations.

        Args:
            file_inventory: Run Workflow #13
            local_inventory: Run Workflow #45
            aws_inventory: Run Workflow #47
            gap_analysis: Run Workflow #46
            sync_status: Run Workflow #49

        Returns:
            Dict with results from all workflows
        """
        logger.info("Running all workflow integrations...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'workflows': {}
        }

        if file_inventory:
            results['workflows']['file_inventory'] = self.run_file_inventory()

        if local_inventory:
            results['workflows']['local_data'] = self.run_local_data_inventory()

        if aws_inventory:
            results['workflows']['aws_inventory'] = self.run_aws_data_inventory()

        if gap_analysis:
            results['workflows']['data_gaps'] = self.run_data_gap_analysis()

        if sync_status:
            results['workflows']['sync_status'] = self.run_sync_status_check()

        logger.info("All workflows complete")
        return results


def main():
    """CLI entry point for testing."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    project_root = Path(__file__).parent.parent.parent
    integration = WorkflowIntegration(str(project_root))

    if len(sys.argv) > 1:
        workflow = sys.argv[1]

        if workflow == 'file-inventory':
            result = integration.run_file_inventory()
        elif workflow == 'local-inventory':
            result = integration.run_local_data_inventory()
        elif workflow == 'aws-inventory':
            result = integration.run_aws_data_inventory()
        elif workflow == 'gap-analysis':
            result = integration.run_data_gap_analysis()
        elif workflow == 'sync-status':
            result = integration.run_sync_status_check()
        elif workflow == 'all':
            result = integration.run_all_workflows()
        else:
            print(f"Unknown workflow: {workflow}")
            sys.exit(1)

        print(json.dumps(result, indent=2))
    else:
        print("Usage: python workflow_integration.py <workflow>")
        print("Workflows: file-inventory, local-inventory, aws-inventory, gap-analysis, sync-status, all")
        sys.exit(1)


if __name__ == '__main__':
    main()
