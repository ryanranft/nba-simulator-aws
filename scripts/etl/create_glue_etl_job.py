#!/usr/bin/env python3
"""
Create AWS Glue ETL Job for NBA Schedule Data

Creates:
1. Glue Connection to RDS PostgreSQL
2. Glue ETL Job to extract schedule data

Author: Ryan Ranft
Date: 2025-10-01
Phase: 2.2 - Glue ETL
"""

import boto3
import sys
import os

# Initialize AWS clients
glue = boto3.client('glue', region_name='us-east-1')
rds = boto3.client('rds', region_name='us-east-1')

# Get database password from environment
db_password = os.environ.get('DB_PASSWORD')
if not db_password:
    print("ERROR: DB_PASSWORD environment variable not set")
    print("Run: source /Users/ryanranft/nba-sim-credentials.env")
    sys.exit(1)

# Get RDS endpoint and subnet info
rds_response = rds.describe_db_instances(DBInstanceIdentifier='nba-sim-db')
db_instance = rds_response['DBInstances'][0]
rds_endpoint = db_instance['Endpoint']['Address']
subnet_group = db_instance['DBSubnetGroup']
subnets = [s['SubnetIdentifier'] for s in subnet_group['Subnets']]
vpc_id = subnet_group['VpcId']
security_groups = [sg['VpcSecurityGroupId'] for sg in db_instance['VpcSecurityGroups']]

print(f"RDS Endpoint: {rds_endpoint}")
print(f"VPC: {vpc_id}")
print(f"Subnets: {len(subnets)}")
print(f"Security Groups: {security_groups}")
print()

# Step 1: Create Glue Connection to RDS
connection_name = "nba-rds-connection"

try:
    print(f"Creating Glue connection: {connection_name}")
    glue.create_connection(
        ConnectionInput={
            'Name': connection_name,
            'Description': 'Connection to NBA Simulator RDS PostgreSQL',
            'ConnectionType': 'JDBC',
            'ConnectionProperties': {
                'JDBC_CONNECTION_URL': f'jdbc:postgresql://{rds_endpoint}:5432/nba_simulator',
                'USERNAME': 'postgres',
                'PASSWORD': db_password
            },
            'PhysicalConnectionRequirements': {
                'SubnetId': subnets[0],  # Use first subnet
                'SecurityGroupIdList': security_groups,
                'AvailabilityZone': subnet_group['Subnets'][0]['SubnetAvailabilityZone']['Name']
            }
        }
    )
    print(f"✅ Created connection: {connection_name}")
except glue.exceptions.AlreadyExistsException:
    print(f"ℹ️  Connection already exists: {connection_name}")
except Exception as e:
    print(f"Error creating connection: {e}")
    sys.exit(1)

print()

# Step 2: Create Glue ETL Job
job_name = "nba-schedule-etl-job"

try:
    print(f"Creating Glue ETL job: {job_name}")
    response = glue.create_job(
        Name=job_name,
        Description='Extract NBA schedule data from S3 JSON and load to RDS PostgreSQL',
        Role='AWSGlueServiceRole-NBASimulator',
        ExecutionProperty={
            'MaxConcurrentRuns': 1
        },
        Command={
            'Name': 'glueetl',
            'ScriptLocation': 's3://nba-sim-raw-data-lake/scripts/glue_etl_extract_schedule.py',
            'PythonVersion': '3'
        },
        DefaultArguments={
            '--TempDir': 's3://nba-sim-raw-data-lake/temp/',
            '--job-bookmark-option': 'job-bookmark-disable',
            '--enable-metrics': 'true',
            '--enable-continuous-cloudwatch-log': 'true',
            '--enable-spark-ui': 'true',
            '--spark-event-logs-path': 's3://nba-sim-raw-data-lake/spark-logs/',
            '--db_host': rds_endpoint,
            '--db_name': 'nba_simulator',
            '--db_user': 'postgres',
            '--db_password': db_password
        },
        Connections={
            'Connections': [connection_name]
        },
        MaxRetries=0,
        Timeout=2880,  # 48 hours max
        GlueVersion='4.0',
        NumberOfWorkers=2,
        WorkerType='G.1X'
    )
    print(f"✅ Created Glue ETL job: {job_name}")
    print(f"   Job ARN: {response.get('Name', 'N/A')}")
except glue.exceptions.AlreadyExistsException:
    print(f"ℹ️  Job already exists: {job_name}")
except Exception as e:
    print(f"❌ Error creating job: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("Glue ETL Setup Complete!")
print("=" * 80)
print()
print("Next steps:")
print("1. Test the job on year 1993:")
print(f"   aws glue start-job-run --job-name {job_name} --arguments '{{\"--year\":\"1993\"}}'")
print()
print("2. Monitor job run:")
print("   aws glue get-job-runs --job-name {job_name} --max-results 1")
print()
print("3. Check CloudWatch logs:")
print(f"   https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws-glue$252Fjobs$252Foutput")