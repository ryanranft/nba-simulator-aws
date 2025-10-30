"""
Database Configuration

Provides database configuration management using existing credentials.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """
    Database configuration container.

    Loads from existing /Users/ryanranft/nba-sim-credentials.env file.
    """

    host: str
    port: int
    database: str
    user: str
    password: str
    url: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """
        Create DatabaseConfig from environment variables.

        Returns:
            DatabaseConfig instance
        """
        return cls(
            host=os.getenv("RDS_HOST", ""),
            port=int(os.getenv("RDS_PORT", "5432")),
            database=os.getenv("RDS_DATABASE", ""),
            user=os.getenv("RDS_USERNAME", ""),
            password=os.getenv("RDS_PASSWORD", ""),
            url=os.getenv("DATABASE_URL", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "url": self.url,
        }

    def get_connection_string(self) -> str:
        """
        Get database connection URL.

        Returns:
            PostgreSQL connection URL
        """
        if self.url:
            return self.url

        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
