#!/usr/bin/env python3
"""
AWS Glue ETL Job: Extract NBA Schedule Data

Extracts 10% of relevant fields from ESPN JSON schedule files.
Processes year-partitioned S3 data and writes to RDS PostgreSQL.

Input: s3://nba-sim-raw-data-lake/schedule/year=YYYY/*.json
Output: RDS PostgreSQL table: games

Fields Extracted (10% strategy):
- game_id, game_date, season_year
- home_team_id, home_team_name, home_score
- away_team_id, away_team_name, away_score
- venue_name, venue_city, venue_state
- status, completed

Author: Ryan Ranft
Date: 2025-10-01
Phase: 2.2 - Glue ETL
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Initialize Glue context
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'year',  # Process one year at a time
    'db_host',
    'db_name',
    'db_user',
    'db_password'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

year = args['year']
print(f"Processing schedule data for year {year}")

# Read from Glue Catalog (created by crawler)
table_name = f"year_{year}"
database_name = "nba_raw_data"

print(f"Reading table: {database_name}.{table_name}")

# Read the Glue table
dynamic_frame = glueContext.create_dynamic_frame.from_catalog(
    database=database_name,
    table_name=table_name
)

# Convert to Spark DataFrame for easier manipulation
df = dynamic_frame.toDF()

print(f"Schema of source table:")
df.printSchema()

# Define UDF to extract game data from the nested JSON structure
def extract_games(row):
    """Extract game records from ESPN JSON structure"""
    games = []

    try:
        # Navigate to page.content.events
        if not row.page or not row.page.content or not row.page.content.events:
            return games

        events_by_date = row.page.content.events

        # Events are organized by date (e.g., "19931105")
        for date_key in events_by_date:
            date_games = events_by_date[date_key]

            if not isinstance(date_games, list):
                continue

            for game in date_games:
                # Extract basic game info
                game_id = game.get('id')
                game_date = game.get('date')
                completed = game.get('completed', False)

                # Extract status
                status = game.get('status', {})
                status_detail = status.get('detail', 'Unknown')

                # Extract teams (competitors or teams array)
                teams_data = game.get('competitors') or game.get('teams', [])

                if len(teams_data) < 2:
                    continue

                # Find home and away teams
                home_team = None
                away_team = None

                for team in teams_data:
                    if team.get('isHome'):
                        home_team = team
                    else:
                        away_team = team

                # If not clearly marked, first is home, second is away
                if not home_team:
                    home_team = teams_data[0] if teams_data[0].get('isHome', True) else teams_data[1]
                    away_team = teams_data[1] if teams_data[0].get('isHome', True) else teams_data[0]

                # Extract venue
                venue = game.get('venue', {})
                venue_name = venue.get('fullName')
                venue_address = venue.get('address', {})
                venue_city = venue_address.get('city')
                venue_state = venue_address.get('state')

                # Create game record
                game_record = {
                    'game_id': str(game_id),
                    'game_date': game_date,
                    'season_year': int(year),
                    'home_team_id': str(home_team.get('id')) if home_team else None,
                    'home_team_name': home_team.get('displayName') if home_team else None,
                    'home_team_abbrev': home_team.get('abbrev') if home_team else None,
                    'home_score': int(home_team.get('score', 0)) if home_team and home_team.get('score') else None,
                    'away_team_id': str(away_team.get('id')) if away_team else None,
                    'away_team_name': away_team.get('displayName') if away_team else None,
                    'away_team_abbrev': away_team.get('abbrev') if away_team else None,
                    'away_score': int(away_team.get('score', 0)) if away_team and away_team.get('score') else None,
                    'venue_name': venue_name,
                    'venue_city': venue_city,
                    'venue_state': venue_state,
                    'status': status_detail,
                    'completed': completed,
                    'home_winner': home_team.get('winner', False) if home_team else False
                }

                games.append(game_record)

    except Exception as e:
        print(f"Error extracting games: {e}")

    return games

# Register UDF
extract_games_udf = udf(extract_games, ArrayType(StructType([
    StructField("game_id", StringType(), True),
    StructField("game_date", StringType(), True),
    StructField("season_year", IntegerType(), True),
    StructField("home_team_id", StringType(), True),
    StructField("home_team_name", StringType(), True),
    StructField("home_team_abbrev", StringType(), True),
    StructField("home_score", IntegerType(), True),
    StructField("away_team_id", StringType(), True),
    StructField("away_team_name", StringType(), True),
    StructField("away_team_abbrev", StringType(), True),
    StructField("away_score", IntegerType(), True),
    StructField("venue_name", StringType(), True),
    StructField("venue_city", StringType(), True),
    StructField("venue_state", StringType(), True),
    StructField("status", StringType(), True),
    StructField("completed", BooleanType(), True),
    StructField("home_winner", BooleanType(), True)
])))

# Apply UDF to extract games
games_df = df.withColumn("games", extract_games_udf(struct([df[x] for x in df.columns])))

# Explode the games array to individual rows
games_exploded = games_df.select(explode("games").alias("game"))

# Flatten the struct into columns
final_df = games_exploded.select("game.*")

print(f"Extracted {final_df.count()} game records for year {year}")
print("Sample data:")
final_df.show(5, truncate=False)

# Write to RDS PostgreSQL
jdbc_url = f"jdbc:postgresql://{args['db_host']}:5432/{args['db_name']}"

final_df.write \
    .format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "games") \
    .option("user", args['db_user']) \
    .option("password", args['db_password']) \
    .option("driver", "org.postgresql.Driver") \
    .mode("append") \
    .save()

print(f"✅ Successfully loaded {final_df.count()} games from year {year} to RDS")

job.commit()