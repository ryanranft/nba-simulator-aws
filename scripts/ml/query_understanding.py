"""
Query Understanding Module for RAG+LLM System

Analyzes user queries to extract intent, entities, and temporal context.
Enables intelligent context retrieval and response generation.

Part of Phase 0.0012: RAG + LLM Integration (rec_188)
"""

import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor


class QueryUnderstanding:
    """Parse and understand user queries about NBA data"""

    def __init__(self, db_connection: Optional[psycopg2.extensions.connection] = None):
        """
        Initialize query understanding module.

        Args:
            db_connection: PostgreSQL connection for entity matching
        """
        self.conn = db_connection

        # Query intent patterns
        self.intent_patterns = {
            "comparison": [
                r"\bcompare\b",
                r"\bvs\.?\b",
                r"\bversus\b",
                r"\bbetter\b",
                r"\bwho\'s\b",
                r"\bwhich\b.*\bbetter\b",
            ],
            "narrative": [
                r"\bwhat happened\b",
                r"\bdescribe\b",
                r"\btell me about\b",
                r"\bstory\b",
                r"\bhow did\b",
                r"\brecap\b",
            ],
            "statistics": [
                r"\bstats?\b",
                r"\bstatistics\b",
                r"\baverages?\b",
                r"\btotals?\b",
                r"\bpoints?\b",
                r"\brebounds?\b",
                r"\bassists?\b",
                r"\bper game\b",
                r"\bppg\b",
                r"\brpg\b",
                r"\bapg\b",
            ],
            "ranking": [
                r"\bbest\b",
                r"\btop\b",
                r"\bgreatest\b",
                r"\bworst\b",
                r"\brank\b",
                r"\bleaders?\b",
                r"\blist\b",
            ],
            "prediction": [
                r"\bwill\b",
                r"\bpredict\b",
                r"\bforecast\b",
                r"\bexpect\b",
                r"\bchances?\b",
                r"\bodds\b",
                r"\blikely\b",
            ],
        }

        # Common NBA teams (abbreviations and full names)
        self.nba_teams = [
            "lakers",
            "celtics",
            "warriors",
            "bulls",
            "heat",
            "spurs",
            "cavaliers",
            "nets",
            "clippers",
            "knicks",
            "raptors",
            "sixers",
            "76ers",
            "bucks",
            "rockets",
            "mavericks",
            "suns",
            "lal",
            "bos",
            "gsw",
            "chi",
            "mia",
            "sas",
            "cle",
            "bkn",
            "lac",
            "nyk",
            "tor",
            "phi",
            "mil",
            "hou",
            "dal",
            "phx",
        ]

    def analyze_query(self, query: str) -> Dict:
        """
        Analyze query to extract all relevant information.

        Args:
            query: User's natural language query

        Returns:
            Dictionary with intent, entities, temporal info, and query type
        """
        query_lower = query.lower()

        analysis = {
            "original_query": query,
            "intent": self._classify_intent(query_lower),
            "entities": self._extract_entities(query),
            "temporal": self._extract_temporal(query),
            "query_type": None,
            "confidence": 0.0,
        }

        # Determine overall query type based on intent
        analysis["query_type"] = self._determine_query_type(analysis)

        # Estimate confidence based on entity detection
        analysis["confidence"] = self._estimate_confidence(analysis)

        return analysis

    def _classify_intent(self, query_lower: str) -> str:
        """
        Classify user's intent from query.

        Args:
            query_lower: Lowercase query string

        Returns:
            Intent category (comparison, narrative, statistics, ranking, prediction, general)
        """
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent

        return "general"

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract NBA entities (players, teams, seasons) from query.

        Args:
            query: Original query string

        Returns:
            Dictionary with lists of players, teams, and seasons
        """
        entities = {"players": [], "teams": [], "seasons": []}

        # Extract players from database if connection available
        if self.conn:
            entities["players"] = self._extract_players_from_db(query)
        else:
            # Fallback: Extract common player name patterns
            entities["players"] = self._extract_player_patterns(query)

        # Extract teams
        entities["teams"] = self._extract_teams(query)

        # Extract seasons
        entities["seasons"] = self._extract_seasons(query)

        return entities

    def _extract_players_from_db(self, query: str) -> List[str]:
        """
        Extract player names by matching against database.

        Args:
            query: Query string

        Returns:
            List of player names found in query
        """
        try:
            cur = self.conn.cursor()

            # Search for player names in raw_data.nba_players
            cur.execute(
                """
                SELECT DISTINCT
                    data->>'player_name' as name,
                    length(data->>'player_name') as name_length
                FROM raw_data.nba_players
                WHERE %s ILIKE '%%' || (data->>'player_name') || '%%'
                ORDER BY name_length DESC
                LIMIT 10;
            """,
                (query,),
            )

            players = [row[0] for row in cur.fetchall() if row[0]]
            cur.close()

            return players

        except Exception as e:
            print(f"Warning: Database player extraction failed: {e}")
            return self._extract_player_patterns(query)

    def _extract_player_patterns(self, query: str) -> List[str]:
        """
        Extract player names using pattern matching (fallback).

        Args:
            query: Query string

        Returns:
            List of potential player names
        """
        # Pattern: Capitalized First Last (e.g., "LeBron James")
        name_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
        matches = re.findall(name_pattern, query)

        return list(set(matches))

    def _extract_teams(self, query: str) -> List[str]:
        """
        Extract team names from query.

        Args:
            query: Query string

        Returns:
            List of team names/abbreviations found
        """
        query_lower = query.lower()
        found_teams = []

        for team in self.nba_teams:
            # Match whole word only
            if re.search(rf"\b{team}\b", query_lower):
                found_teams.append(team)

        return list(set(found_teams))

    def _extract_seasons(self, query: str) -> List[int]:
        """
        Extract season years from query.

        Args:
            query: Query string

        Returns:
            List of season years (e.g., [2022])
        """
        seasons = []

        # Pattern: "2022 season" or "2021-22 season"
        season_patterns = [
            r"(\d{4})(?:-\d{2})?\s*season",
            r"season\s*(\d{4})",
            r"\b(19\d{2}|20\d{2})\b",  # Any year 1900-2099
        ]

        for pattern in season_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                try:
                    year = int(match)
                    if 1946 <= year <= 2030:  # Valid NBA years
                        seasons.append(year)
                except ValueError:
                    continue

        return sorted(list(set(seasons)))

    def _extract_temporal(self, query: str) -> Dict:
        """
        Extract temporal references (dates, seasons, date ranges).

        Args:
            query: Query string

        Returns:
            Dictionary with season, date, and date_range info
        """
        temporal = {
            "season": None,
            "date": None,
            "date_range": None,
            "relative": None,  # e.g., "last week", "this season"
        }

        # Extract season (most specific to NBA)
        seasons = self._extract_seasons(query)
        if seasons:
            temporal["season"] = seasons[0]  # Use first/most prominent

        # Extract specific dates
        temporal["date"] = self._extract_date(query)

        # Extract date ranges
        temporal["date_range"] = self._extract_date_range(query)

        # Extract relative temporal references
        temporal["relative"] = self._extract_relative_temporal(query)

        return temporal

    def _extract_date(self, query: str) -> Optional[datetime]:
        """
        Extract specific date from query.

        Args:
            query: Query string

        Returns:
            Datetime object or None
        """
        # Date patterns
        date_patterns = [
            (r"(\w+\s+\d{1,2},?\s+\d{4})", "%B %d, %Y"),  # "June 15, 2022"
            (r"(\d{1,2}/\d{1,2}/\d{4})", "%m/%d/%Y"),  # "06/15/2022"
            (r"(\d{4}-\d{2}-\d{2})", "%Y-%m-%d"),  # "2022-06-15"
        ]

        for pattern, date_format in date_patterns:
            match = re.search(pattern, query)
            if match:
                try:
                    return datetime.strptime(match.group(1), date_format)
                except ValueError:
                    continue

        return None

    def _extract_date_range(self, query: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Extract date range from query.

        Args:
            query: Query string

        Returns:
            Tuple of (start_date, end_date) or None
        """
        # Pattern: "between X and Y"
        range_pattern = r"between\s+(.+?)\s+and\s+(.+?)(?:\s|$)"
        match = re.search(range_pattern, query, re.IGNORECASE)

        if match:
            start_str = match.group(1)
            end_str = match.group(2)

            start_date = self._extract_date(start_str)
            end_date = self._extract_date(end_str)

            if start_date and end_date:
                return (start_date, end_date)

        return None

    def _extract_relative_temporal(self, query: str) -> Optional[str]:
        """
        Extract relative temporal references.

        Args:
            query: Query string

        Returns:
            Relative temporal string or None
        """
        query_lower = query.lower()

        relative_patterns = {
            "current_season": [r"\bthis season\b", r"\bcurrent season\b"],
            "last_season": [r"\blast season\b", r"\bprevious season\b"],
            "last_game": [r"\blast game\b", r"\bmost recent game\b"],
            "this_week": [r"\bthis week\b"],
            "last_week": [r"\blast week\b"],
            "playoffs": [r"\bplayoffs\b", r"\bpostseason\b"],
            "finals": [r"\bfinals\b", r"\bchampionship\b"],
        }

        for category, patterns in relative_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return category

        return None

    def _determine_query_type(self, analysis: Dict) -> str:
        """
        Determine overall query type based on analysis.

        Args:
            analysis: Query analysis dictionary

        Returns:
            Query type string
        """
        intent = analysis["intent"]
        has_temporal = any(analysis["temporal"].values())
        has_entities = any(analysis["entities"].values())

        if intent == "comparison" and len(analysis["entities"]["players"]) >= 2:
            return "player_comparison"
        elif intent == "narrative" and has_temporal:
            return "game_narrative"
        elif intent == "statistics" and has_entities:
            return "entity_statistics"
        elif intent == "ranking":
            return "ranking_query"
        elif intent == "prediction":
            return "prediction_query"
        else:
            return "general_query"

    def _estimate_confidence(self, analysis: Dict) -> float:
        """
        Estimate confidence in query understanding.

        Args:
            analysis: Query analysis dictionary

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.0

        # Base confidence from intent detection
        if analysis["intent"] != "general":
            confidence += 0.3

        # Boost for entity detection
        if analysis["entities"]["players"]:
            confidence += 0.3
        if analysis["entities"]["teams"]:
            confidence += 0.2
        if analysis["entities"]["seasons"]:
            confidence += 0.1

        # Boost for temporal detection
        if analysis["temporal"]["date"] or analysis["temporal"]["season"]:
            confidence += 0.1

        return min(confidence, 1.0)


# Standalone testing
if __name__ == "__main__":
    # Test without database
    qp = QueryUnderstanding()

    test_queries = [
        "Who is LeBron James?",
        "Compare LeBron James and Michael Jordan",
        "What happened in the Lakers vs Warriors game on June 15, 2022?",
        "Who were the best three-point shooters in the 2022 season?",
        "What are Stephen Curry's stats this season?",
    ]

    print("Query Understanding Test Results:")
    print("=" * 80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        analysis = qp.analyze_query(query)
        print(f"  Intent: {analysis['intent']}")
        print(f"  Query Type: {analysis['query_type']}")
        print(f"  Players: {analysis['entities']['players']}")
        print(f"  Teams: {analysis['entities']['teams']}")
        print(f"  Season: {analysis['temporal']['season']}")
        print(f"  Confidence: {analysis['confidence']:.2f}")
