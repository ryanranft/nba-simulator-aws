#!/usr/bin/env python3
"""
NBA Simulator - CloudWatch Setup Script

Configures CloudWatch monitoring:
1. Validates AWS permissions
2. Creates CloudWatch dashboard  
3. Sets up metric alarms
4. Publishes test metrics

Usage:
    python setup-cloudwatch.py --all
    python setup-cloudwatch.py --region us-west-2
"""

import sys
import json
import argparse
import asyncio

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    print("Warning: boto3 not installed. Run: pip install boto3")

class CloudWatchSetup:
    """CloudWatch setup and configuration"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.cw_client = None
        
        if BOTO3_AVAILABLE:
            try:
                self.cw_client = boto3.client('cloudwatch', region_name=region)
            except Exception as e:
                print(f"Error initializing CloudWatch client: {e}")
    
    def check_permissions(self) -> bool:
        """Check AWS permissions"""
        print("\n🔍 Checking AWS permissions...")
        
        if not BOTO3_AVAILABLE:
            print("❌ boto3 not installed")
            return False
        
        try:
            self.cw_client.list_metrics(Namespace='NBA-Simulator/DIMS', MaxRecords=1)
            print("✅ CloudWatch Metrics access: OK")
            return True
        except NoCredentialsError:
            print("❌ AWS credentials not found")
            print("Configure with: aws configure")
            return False
        except ClientError as e:
            print(f"❌ Permission error: {e}")
            return False
    
    def create_dashboard(self) -> bool:
        """Create CloudWatch dashboard"""
        print("\n📊 Creating CloudWatch Dashboard...")
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["NBA-Simulator/DIMS", "VerificationsPassed"],
                            [".", "VerificationsFailed"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": self.region,
                        "title": "DIMS Verification Results"
                    }
                }
            ]
        }
        
        try:
            self.cw_client.put_dashboard(
                DashboardName='NBA-Simulator-Monitoring',
                DashboardBody=json.dumps(dashboard_body)
            )
            print("✅ Dashboard created: NBA-Simulator-Monitoring")
            url = f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name=NBA-Simulator-Monitoring"
            print(f"   View at: {url}")
            return True
        except ClientError as e:
            print(f"❌ Failed to create dashboard: {e}")
            return False
    
    def create_alarms(self) -> bool:
        """Create CloudWatch alarms"""
        print("\n🚨 Creating CloudWatch Alarms...")
        
        alarms = [
            {
                'AlarmName': 'NBA-Simulator-DIMS-Failures',
                'MetricName': 'VerificationsFailed',
                'Namespace': 'NBA-Simulator/DIMS',
                'Statistic': 'Sum',
                'Period': 300,
                'EvaluationPeriods': 2,
                'Threshold': 5.0,
                'ComparisonOperator': 'GreaterThanThreshold',
                'AlarmDescription': 'Alert when DIMS verifications fail'
            }
        ]
        
        for alarm_config in alarms:
            try:
                self.cw_client.put_metric_alarm(**alarm_config)
                print(f"✅ Created alarm: {alarm_config['AlarmName']}")
            except ClientError as e:
                print(f"❌ Failed to create alarm: {e}")
                return False
        
        return True
    
    def print_guide(self):
        """Print configuration guide"""
        print("\n" + "=" * 70)
        print("📖 CloudWatch Configuration Complete!")
        print("=" * 70)
        print("""
Next Steps:

1. View Dashboard:
   AWS Console > CloudWatch > Dashboards > NBA-Simulator-Monitoring

2. Start Publishing Metrics:
   python start-dashboard.py

3. Cost: ~$1-2/month for metrics + alarms

For more info: https://docs.aws.amazon.com/cloudwatch/
        """)

async def main():
    parser = argparse.ArgumentParser(description='NBA Simulator - CloudWatch Setup')
    parser.add_argument('--region', '-r', default='us-east-1', help='AWS region')
    parser.add_argument('--create-dashboard', action='store_true', help='Create dashboard')
    parser.add_argument('--create-alarms', action='store_true', help='Create alarms')
    parser.add_argument('--all', action='store_true', help='Do everything')
    
    args = parser.parse_args()
    
    if not any([args.create_dashboard, args.create_alarms]):
        args.all = True
    
    print("=" * 70)
    print("🏀 NBA Simulator - CloudWatch Setup")
    print("=" * 70)
    print(f"Region: {args.region}")
    print("=" * 70)
    
    setup = CloudWatchSetup(region=args.region)
    
    if not setup.check_permissions():
        print("\n❌ Setup aborted due to permission issues")
        return 1
    
    if args.all or args.create_dashboard:
        setup.create_dashboard()
    
    if args.all or args.create_alarms:
        setup.create_alarms()
    
    setup.print_guide()
    return 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
