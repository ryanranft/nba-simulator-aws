"""
AWS Services Configuration

Provides AWS service configuration using existing credentials and settings.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class AWSConfig:
    """
    AWS configuration container.

    Loads from existing environment variables and credentials.
    """

    access_key_id: str
    secret_access_key: str
    region: str
    s3_bucket: str

    @classmethod
    def from_env(cls) -> "AWSConfig":
        """
        Create AWSConfig from environment variables.

        Returns:
            AWSConfig instance
        """
        return cls(
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            s3_bucket=os.getenv("S3_BUCKET", "nba-sim-raw-data-lake"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Configuration dictionary (without sensitive credentials)
        """
        return {
            "region": self.region,
            "s3_bucket": self.s3_bucket,
            "has_credentials": bool(self.access_key_id and self.secret_access_key),
        }

    def get_boto3_config(self) -> Dict[str, str]:
        """
        Get boto3 client configuration.

        Returns:
            Configuration dict for boto3.client()
        """
        config = {
            "region_name": self.region,
        }

        if self.access_key_id and self.secret_access_key:
            config["aws_access_key_id"] = self.access_key_id
            config["aws_secret_access_key"] = self.secret_access_key

        return config
