#!/usr/bin/env python3
"""
Generate Implementation Recommendations

This script analyzes a sub-phase README and generates specific, actionable
recommendations for how to implement the sub-phase into the project.

It considers:
- What the sub-phase is trying to accomplish
- What files need to be created/modified
- What dependencies are needed
- How it integrates with existing systems
- What tests are needed

Usage:
    python scripts/automation/generate_implementation_recommendations.py 0.1
    python scripts/automation/generate_implementation_recommendations.py 0.1 --verbose
    python scripts/automation/generate_implementation_recommendations.py 0.1 --implement

Author: Claude Code
Created: October 23, 2025
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional
import json


class ImplementationRecommendationGenerator:
    """Generate implementation recommendations for a sub-phase."""

    def __init__(self, sub_phase_id: str, verbose: bool = False):
        """
        Initialize generator.

        Args:
            sub_phase_id: Sub-phase ID (e.g., "0.1", "5.19")
            verbose: Enable verbose output
        """
        self.sub_phase_id = sub_phase_id
        self.verbose = verbose

        # Parse phase number
        parts = sub_phase_id.split(".")
        self.phase_num = int(parts[0])

        # Paths
        self.project_root = Path(__file__).parent.parent.parent
        self.docs_dir = self.project_root / "docs"
        self.phases_dir = self.docs_dir / "phases"

        if self.phase_num == 0:
            self.phase_dir = self.phases_dir / "phase_0"
        else:
            self.phase_dir = self.phases_dir / f"phase_{self.phase_num}"

        # Find sub-phase README
        self.sub_phase_readme = self._find_sub_phase_readme()
        self.recommendations = []

    def _find_sub_phase_readme(self) -> Optional[Path]:
        """Find the sub-phase README file."""
        for item in self.phase_dir.iterdir():
            if item.is_dir() and item.name.startswith(f"{self.sub_phase_id}_"):
                readme = item / "README.md"
                if readme.exists():
                    return readme

        for item in self.phase_dir.iterdir():
            if (
                item.is_file()
                and item.name.startswith(f"{self.sub_phase_id}_")
                and item.name.endswith(".md")
            ):
                return item

        return None

    def generate_recommendations(self) -> List[Dict]:
        """Generate implementation recommendations."""
        if not self.sub_phase_readme or not self.sub_phase_readme.exists():
            print(f"❌ Sub-phase README not found for {self.sub_phase_id}")
            return []

        content = self.sub_phase_readme.read_text()

        print(f"\n{'='*70}")
        print(f"Generating Implementation Recommendations: {self.sub_phase_id}")
        print(f"{'='*70}\n")

        # Read IMPLEMENTATION_GUIDE.md if it exists
        impl_guide_content = self._read_implementation_guide()
        if impl_guide_content:
            print(
                "  ✅ Found IMPLEMENTATION_GUIDE.md - incorporating technical details"
            )
            content += "\n\n" + impl_guide_content

        # Read RECOMMENDATIONS_FROM_BOOKS.md if it exists
        book_recs_content = self._read_book_recommendations()
        if book_recs_content:
            print(
                "  ✅ Found RECOMMENDATIONS_FROM_BOOKS.md - incorporating academic foundation"
            )
            content += "\n\n" + book_recs_content

        # Parse README sections
        overview = self._extract_section(content, "Overview")
        capabilities = self._extract_section(content, "Capabilities")
        architecture = self._extract_section(content, "Architecture")
        integration = self._extract_section(content, "Integration")

        # Analyze what needs to be implemented
        self._analyze_data_requirements(content)
        self._analyze_code_requirements(content)
        self._analyze_infrastructure_requirements(content)
        self._analyze_integration_points(content)
        self._analyze_testing_requirements(content)

        # Generate specific recommendations
        self._generate_file_recommendations()
        self._generate_dependency_recommendations()
        self._generate_database_recommendations(content)
        self._generate_api_recommendations(content)

        return self.recommendations

    def _read_implementation_guide(self) -> str:
        """Read IMPLEMENTATION_GUIDE.md if it exists."""
        # Check if sub-phase is in power directory
        readme_parent = self.sub_phase_readme.parent
        impl_guide = readme_parent / "IMPLEMENTATION_GUIDE.md"

        if impl_guide.exists():
            return impl_guide.read_text()
        return ""

    def _read_book_recommendations(self) -> str:
        """Read RECOMMENDATIONS_FROM_BOOKS.md if it exists."""
        # Check if sub-phase is in power directory
        readme_parent = self.sub_phase_readme.parent
        book_recs = readme_parent / "RECOMMENDATIONS_FROM_BOOKS.md"

        if book_recs.exists():
            return book_recs.read_text()
        return ""

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section from the README."""
        pattern = rf"##\s+{section_name}.*?\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _analyze_data_requirements(self, content: str):
        """Analyze what data needs to be collected/stored."""
        data_keywords = {
            "s3": ["s3", "bucket", "storage", "upload", "download"],
            "rds": ["rds", "database", "postgres", "sql", "table"],
            "csv": ["csv", "file", "data file"],
            "json": ["json", "jsonb", "json data"],
            "api": ["api", "endpoint", "rest", "http"],
        }

        data_needs = {}
        content_lower = content.lower()

        for data_type, keywords in data_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                data_needs[data_type] = True

        if data_needs:
            self.recommendations.append(
                {
                    "type": "data",
                    "priority": "HIGH",
                    "title": "Data Storage & Retrieval",
                    "description": f"Implement data handling for: {', '.join(data_needs.keys())}",
                    "files_to_create": self._suggest_data_files(data_needs),
                    "implementation_steps": self._suggest_data_steps(data_needs),
                }
            )

    def _analyze_code_requirements(self, content: str):
        """Analyze what code/scripts need to be created."""
        # Look for code examples or script mentions
        code_blocks = re.findall(r"```(?:python|bash|sql)(.*?)```", content, re.DOTALL)

        if code_blocks:
            self.recommendations.append(
                {
                    "type": "code",
                    "priority": "HIGH",
                    "title": "Core Implementation Scripts",
                    "description": f"Create {len(code_blocks)} main implementation files based on README examples",
                    "files_to_create": [
                        f"scripts/{self.sub_phase_id.replace('.', '_')}/main.py",
                        f"scripts/{self.sub_phase_id.replace('.', '_')}/utils.py",
                    ],
                    "implementation_steps": [
                        "1. Extract code examples from README",
                        "2. Create proper Python modules",
                        "3. Add error handling and logging",
                        "4. Add configuration management",
                        "5. Create CLI interface if needed",
                    ],
                }
            )

    def _analyze_infrastructure_requirements(self, content: str):
        """Analyze infrastructure needs (AWS, databases, etc.)."""
        infra_keywords = {
            "aws": ["aws", "boto3", "cloudformation"],
            "docker": ["docker", "container", "dockerfile"],
            "kubernetes": ["kubernetes", "k8s", "kubectl"],
        }

        content_lower = content.lower()
        infra_needs = []

        for infra_type, keywords in infra_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                infra_needs.append(infra_type)

        if infra_needs:
            self.recommendations.append(
                {
                    "type": "infrastructure",
                    "priority": "MEDIUM",
                    "title": "Infrastructure Setup",
                    "description": f"Set up infrastructure: {', '.join(infra_needs)}",
                    "files_to_create": [
                        f"config/{self.sub_phase_id.replace('.', '_')}_config.yaml"
                    ],
                    "implementation_steps": self._suggest_infra_steps(infra_needs),
                }
            )

    def _analyze_integration_points(self, content: str):
        """Analyze how this integrates with existing systems."""
        integration_patterns = [
            (r"integrate.*with.*(\w+)", "Integration with {}"),
            (r"connect.*to.*(\w+)", "Connection to {}"),
            (r"use.*existing.*(\w+)", "Use existing {}"),
        ]

        integrations = []
        for pattern, template in integration_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            integrations.extend(matches)

        if integrations:
            self.recommendations.append(
                {
                    "type": "integration",
                    "priority": "HIGH",
                    "title": "System Integration",
                    "description": f"Integrate with existing systems: {', '.join(list(set(integrations))[:3])}",
                    "files_to_modify": [
                        "Review and update integration points in existing files"
                    ],
                    "implementation_steps": [
                        "1. Review existing system architecture",
                        "2. Identify integration interfaces",
                        "3. Create adapter classes if needed",
                        "4. Update existing code to use new functionality",
                        "5. Add integration tests",
                    ],
                }
            )

    def _analyze_testing_requirements(self, content: str):
        """Analyze what tests are needed."""
        test_types = {
            "unit": ["unit test", "test each function", "test individual"],
            "integration": ["integration test", "test integration", "end-to-end"],
            "performance": ["performance", "benchmark", "load test"],
        }

        content_lower = content.lower()
        needed_tests = []

        for test_type, keywords in test_types.items():
            if any(keyword in content_lower for keyword in keywords):
                needed_tests.append(test_type)

        # Always recommend at least unit and integration tests
        if not needed_tests:
            needed_tests = ["unit", "integration"]

        self.recommendations.append(
            {
                "type": "testing",
                "priority": "HIGH",
                "title": "Comprehensive Testing",
                "description": f"Implement {', '.join(needed_tests)} tests",
                "files_to_create": [
                    f"tests/{self.sub_phase_id.replace('.', '_')}/test_main.py",
                    f"tests/{self.sub_phase_id.replace('.', '_')}/test_integration.py",
                ],
                "implementation_steps": [
                    f"1. Create {test_type} tests" for test_type in needed_tests
                ]
                + [
                    "2. Ensure 100% test coverage",
                    "3. Add fixtures and mocks",
                    "4. Create test data if needed",
                ],
            }
        )

    def _suggest_data_files(self, data_needs: Dict) -> List[str]:
        """Suggest data handling files."""
        files = []
        sub_phase_clean = self.sub_phase_id.replace(".", "_")

        if "s3" in data_needs:
            files.append(f"scripts/data/{sub_phase_clean}_s3_handler.py")
        if "rds" in data_needs or "postgres" in data_needs:
            files.append(f"scripts/data/{sub_phase_clean}_db_handler.py")
        if "api" in data_needs:
            files.append(f"scripts/data/{sub_phase_clean}_api_client.py")

        return files

    def _suggest_data_steps(self, data_needs: Dict) -> List[str]:
        """Suggest implementation steps for data handling."""
        steps = []

        if "s3" in data_needs:
            steps.append("1. Create S3 client wrapper with upload/download methods")
        if "rds" in data_needs:
            steps.append("2. Create database connection pool")
            steps.append("3. Implement CRUD operations")
        if "api" in data_needs:
            steps.append("4. Create API client with authentication")
            steps.append("5. Implement rate limiting and retries")

        steps.append("6. Add error handling and logging")
        steps.append("7. Create configuration file for credentials")

        return steps

    def _suggest_infra_steps(self, infra_needs: List[str]) -> List[str]:
        """Suggest infrastructure setup steps."""
        steps = []

        if "aws" in infra_needs:
            steps.append("1. Create AWS resource configuration")
            steps.append("2. Set up IAM roles and policies")
        if "docker" in infra_needs:
            steps.append("3. Create Dockerfile")
            steps.append("4. Create docker-compose.yml")
        if "kubernetes" in infra_needs:
            steps.append("5. Create Kubernetes manifests")

        steps.append("6. Document setup procedures")

        return steps

    def _generate_file_recommendations(self):
        """Generate recommendations for file structure."""
        sub_phase_clean = self.sub_phase_id.replace(".", "_")

        self.recommendations.append(
            {
                "type": "structure",
                "priority": "HIGH",
                "title": "Project Structure",
                "description": "Create proper directory structure for this sub-phase",
                "files_to_create": [
                    f"scripts/{sub_phase_clean}/__init__.py",
                    f"scripts/{sub_phase_clean}/config.py",
                    f"scripts/{sub_phase_clean}/main.py",
                    f"tests/{sub_phase_clean}/__init__.py",
                    f"docs/{sub_phase_clean}/IMPLEMENTATION.md",
                ],
                "implementation_steps": [
                    "1. Create main module directory",
                    "2. Set up configuration management",
                    "3. Create main entry point",
                    "4. Add test directory",
                    "5. Document implementation",
                ],
            }
        )

    def _generate_dependency_recommendations(self):
        """Generate dependency recommendations."""
        if self.sub_phase_readme:
            content = self.sub_phase_readme.read_text()

            # Look for import statements or package names
            imports = re.findall(r"import\s+(\w+)", content)
            packages = re.findall(r"pip install\s+([\w\-]+)", content)

            if imports or packages:
                self.recommendations.append(
                    {
                        "type": "dependencies",
                        "priority": "MEDIUM",
                        "title": "Python Dependencies",
                        "description": f"Add required packages: {', '.join(list(set(imports + packages))[:5])}",
                        "files_to_modify": ["requirements.txt"],
                        "implementation_steps": [
                            "1. Add packages to requirements.txt",
                            "2. Run pip install -r requirements.txt",
                            "3. Update environment.yml if using conda",
                            "4. Document version requirements",
                        ],
                    }
                )

    def _generate_database_recommendations(self, content: str):
        """Generate database-related recommendations."""
        if (
            "database" in content.lower()
            or "rds" in content.lower()
            or "postgres" in content.lower()
        ):
            self.recommendations.append(
                {
                    "type": "database",
                    "priority": "HIGH",
                    "title": "Database Schema & Migrations",
                    "description": "Create database schema and migration scripts",
                    "files_to_create": [
                        f"scripts/db/migrations/{self.sub_phase_id.replace('.', '_')}_schema.sql",
                        f"scripts/db/{self.sub_phase_id.replace('.', '_')}_init.py",
                    ],
                    "implementation_steps": [
                        "1. Design database schema",
                        "2. Create migration scripts",
                        "3. Add indexes for performance",
                        "4. Create seed data if needed",
                        "5. Test migrations on dev database",
                    ],
                }
            )

    def _generate_api_recommendations(self, content: str):
        """Generate API-related recommendations."""
        if "api" in content.lower() or "endpoint" in content.lower():
            self.recommendations.append(
                {
                    "type": "api",
                    "priority": "MEDIUM",
                    "title": "API Implementation",
                    "description": "Create API endpoints and client",
                    "files_to_create": [
                        f"api/{self.sub_phase_id.replace('.', '_')}/routes.py",
                        f"api/{self.sub_phase_id.replace('.', '_')}/schemas.py",
                    ],
                    "implementation_steps": [
                        "1. Define API schemas",
                        "2. Create route handlers",
                        "3. Add authentication",
                        "4. Implement rate limiting",
                        "5. Add API documentation",
                    ],
                }
            )

    def print_recommendations(self):
        """Print recommendations in a readable format."""
        if not self.recommendations:
            print("ℹ️  No specific recommendations generated\n")
            return

        print(f"\n{'='*70}")
        print(f"Implementation Recommendations: {self.sub_phase_id}")
        print(f"{'='*70}\n")

        # Sort by priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_recs = sorted(
            self.recommendations,
            key=lambda x: priority_order.get(x.get("priority", "LOW"), 3),
        )

        for i, rec in enumerate(sorted_recs, 1):
            priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(
                rec["priority"], "⚪"
            )

            print(f"{i}. {priority_emoji} {rec['title']} ({rec['priority']})")
            print(f"   Type: {rec['type']}")
            print(f"   Description: {rec['description']}")

            if "files_to_create" in rec:
                print(f"   Files to create:")
                for file in rec["files_to_create"][:3]:
                    print(f"     - {file}")
                if len(rec["files_to_create"]) > 3:
                    print(f"     ... and {len(rec['files_to_create']) - 3} more")

            if "files_to_modify" in rec:
                print(f"   Files to modify:")
                for file in rec["files_to_modify"]:
                    print(f"     - {file}")

            if "implementation_steps" in rec:
                print(f"   Implementation steps:")
                for step in rec["implementation_steps"][:3]:
                    print(f"     {step}")
                if len(rec["implementation_steps"]) > 3:
                    print(
                        f"     ... and {len(rec['implementation_steps']) - 3} more steps"
                    )

            print()

        print(f"{'='*70}\n")
        print(f"Total recommendations: {len(self.recommendations)}")
        print(
            f"High priority: {sum(1 for r in self.recommendations if r['priority'] == 'HIGH')}"
        )
        print(f"{'='*70}\n")

    def save_recommendations(self, output_file: Path = None):
        """Save recommendations to JSON file."""
        if output_file is None:
            output_file = (
                self.project_root
                / "recommendations"
                / f"{self.sub_phase_id.replace('.', '_')}_recommendations.json"
            )

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(
                {
                    "sub_phase_id": self.sub_phase_id,
                    "recommendations": self.recommendations,
                    "total_count": len(self.recommendations),
                    "high_priority_count": sum(
                        1 for r in self.recommendations if r["priority"] == "HIGH"
                    ),
                },
                f,
                indent=2,
            )

        print(f"✅ Recommendations saved to: {output_file}\n")
        return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate implementation recommendations"
    )
    parser.add_argument("sub_phase_id", help="Sub-phase ID (e.g., 0.1, 5.19)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--save", action="store_true", help="Save recommendations to JSON file"
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Output file path for recommendations JSON"
    )
    parser.add_argument(
        "--implement",
        action="store_true",
        help="Generate and then implement recommendations",
    )
    args = parser.parse_args()

    generator = ImplementationRecommendationGenerator(
        args.sub_phase_id, verbose=args.verbose
    )
    recommendations = generator.generate_recommendations()

    # Don't print if saving to specific output file
    if not args.output:
        generator.print_recommendations()

    if args.save or args.implement or args.output:
        if args.output:
            output_file = generator.save_recommendations(Path(args.output))
        else:
            output_file = generator.save_recommendations()

    if args.implement:
        print("🚀 Launching implementation...")
        print("   (Implementation script will be called here)")
        # TODO: Call implementation script
        print()


if __name__ == "__main__":
    main()
