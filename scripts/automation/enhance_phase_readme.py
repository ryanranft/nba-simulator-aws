#!/usr/bin/env python3
"""
Phase README Enhancement Tool

This script enhances basic phase READMEs with comprehensive "How This Phase Enables the
Simulation Vision" sections that integrate econometric and nonparametric methodology from
the main README.

It analyzes the sub-phase purpose and generates detailed sections showing how the sub-phase
contributes to:
1. Econometric Causal Inference Foundation
2. Nonparametric Event Modeling
3. Context-Adaptive Simulations
4. Integration with Main README Methodology

Usage:
    python scripts/automation/enhance_phase_readme.py 0.8
    python scripts/automation/enhance_phase_readme.py 0.8 --dry-run
    python scripts/automation/enhance_phase_readme.py --all

Author: Claude Code
Created: October 23, 2025
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PhaseREADMEEnhancer:
    """Enhance phase READMEs with methodology integration."""

    def __init__(self, project_root: Path = None, dry_run: bool = False):
        """Initialize enhancer."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.dry_run = dry_run
        self.phases_dir = self.project_root / "docs" / "phases"
        self.main_readme = self.project_root / "README.md"

        # Load main README for methodology integration
        self.main_readme_content = (
            self.main_readme.read_text() if self.main_readme.exists() else ""
        )

    def enhance_sub_phase(self, sub_phase_id: str) -> bool:
        """
        Enhance a single sub-phase README.

        Args:
            sub_phase_id: Sub-phase ID (e.g., "0.8", "5.19")

        Returns:
            True if enhancement successful, False otherwise
        """
        phase_num = int(sub_phase_id.split(".")[0])

        # Find sub-phase directory
        if phase_num == 0:
            phase_dir = self.phases_dir / "phase_0"
        else:
            phase_dir = self.phases_dir / f"phase_{phase_num}"

        # Find README
        readme_path = self._find_readme(phase_dir, sub_phase_id)
        if not readme_path:
            print(f"❌ README not found for sub-phase {sub_phase_id}")
            return False

        print(f"\n{'='*70}")
        print(f"Enhancing Sub-Phase {sub_phase_id} README")
        print(f"{'='*70}\n")
        print(f"README: {readme_path}")

        # Read current content
        current_content = readme_path.read_text()

        # Check if already has "How This Phase Enables" section
        if (
            "How This Phase Enables" in current_content
            or "How Phase" in current_content
        ):
            print("✅ README already has methodology integration section")
            return True

        # Analyze sub-phase
        sub_phase_info = self._analyze_sub_phase(
            phase_dir, sub_phase_id, current_content
        )

        # Generate enhancement section
        enhancement_section = self._generate_methodology_section(
            sub_phase_id, sub_phase_info
        )

        # Insert into README
        enhanced_content = self._insert_enhancement(
            current_content, enhancement_section
        )

        if self.dry_run:
            print("[DRY RUN] Would update README with enhanced content")
            print(f"\nNew section preview:")
            print(enhancement_section[:500] + "...")
            return True

        # Write enhanced content
        readme_path.write_text(enhanced_content)
        print(f"✅ README enhanced successfully")
        return True

    def _find_readme(self, phase_dir: Path, sub_phase_id: str) -> Optional[Path]:
        """Find README for sub-phase."""
        # Try power directory structure first
        for item in phase_dir.iterdir():
            if item.is_dir() and item.name.startswith(f"{sub_phase_id}_"):
                readme = item / "README.md"
                if readme.exists():
                    return readme

        # Try simple file
        for item in phase_dir.iterdir():
            if (
                item.is_file()
                and item.name.startswith(f"{sub_phase_id}_")
                and item.name.endswith(".md")
            ):
                return item

        return None

    def _analyze_sub_phase(
        self, phase_dir: Path, sub_phase_id: str, readme_content: str
    ) -> Dict:
        """Analyze sub-phase to understand its purpose."""
        info = {
            "id": sub_phase_id,
            "name": "",
            "purpose": "",
            "capabilities": [],
            "data_types": [],
            "techniques": [],
            "integration_points": [],
        }

        # Extract name from README header
        name_match = re.search(r"#\s+(.+?)(?:\n|$)", readme_content)
        if name_match:
            info["name"] = name_match.group(1).strip()

        # Extract overview/purpose
        overview_match = re.search(
            r"##\s+Overview\s+(.+?)(?=\n##|\n---|\Z)", readme_content, re.DOTALL
        )
        if overview_match:
            info["purpose"] = overview_match.group(1).strip()

        # Extract capabilities
        if "Key Capabilities:" in readme_content or "Capabilities:" in readme_content:
            caps_match = re.findall(r"[-*]\s+(.+?)(?:\n|$)", readme_content)
            info["capabilities"] = [cap.strip() for cap in caps_match[:10]]

        # Check for related files (IMPLEMENTATION_GUIDE, RECOMMENDATIONS_FROM_BOOKS)
        parent_dir = phase_dir
        for item in parent_dir.iterdir():
            if item.is_dir() and item.name.startswith(f"{sub_phase_id}_"):
                parent_dir = item
                break

        impl_guide = parent_dir / "IMPLEMENTATION_GUIDE.md"
        if impl_guide.exists():
            impl_content = impl_guide.read_text()
            # Extract technical details
            if "technical" in impl_content.lower():
                info["techniques"].append("Technical implementation details available")

        recommendations = parent_dir / "RECOMMENDATIONS_FROM_BOOKS.md"
        if recommendations.exists():
            rec_content = recommendations.read_text()
            # Extract academic foundation
            if "recommendation" in rec_content.lower():
                info["techniques"].append("Academic recommendations available")

        return info

    def _generate_methodology_section(
        self, sub_phase_id: str, sub_phase_info: Dict
    ) -> str:
        """Generate comprehensive methodology integration section."""
        name = sub_phase_info.get("name", f"Sub-phase {sub_phase_id}")
        purpose = sub_phase_info.get("purpose", "")

        # Determine what kind of sub-phase this is
        is_security = "security" in name.lower() or "security" in purpose.lower()
        is_data_collection = (
            "data" in name.lower()
            or "collection" in name.lower()
            or "scraper" in name.lower()
        )
        is_database = (
            "database" in name.lower()
            or "postgresql" in name.lower()
            or "storage" in name.lower()
        )
        is_ml_ai = (
            "rag" in name.lower()
            or "llm" in name.lower()
            or "vector" in name.lower()
            or "machine learning" in name.lower()
        )
        is_pipeline = (
            "pipeline" in name.lower()
            or "dispatcher" in name.lower()
            or "orchestrat" in name.lower()
        )
        is_analysis = (
            "analysis" in name.lower()
            or "error" in name.lower()
            or "validation" in name.lower()
        )

        section = f"""

---

## How This Phase Enables the Simulation Vision

This phase provides critical infrastructure that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What this phase enables:**

### 1. Econometric Causal Inference Foundation

{self._generate_econometric_section(name, purpose, is_security, is_data_collection, is_database, is_ml_ai, is_pipeline, is_analysis)}

### 2. Nonparametric Event Modeling (Distribution-Free)

{self._generate_nonparametric_section(name, purpose, is_security, is_data_collection, is_database, is_ml_ai, is_pipeline, is_analysis)}

### 3. Context-Adaptive Simulations

{self._generate_context_adaptive_section(name, purpose, is_security, is_data_collection, is_database, is_ml_ai, is_pipeline, is_analysis)}

### 4. Integration with Main README Methodology

**Panel data regression (Main README: Lines 81-87):**
{self._generate_panel_data_integration(name, is_security, is_data_collection, is_database, is_ml_ai, is_pipeline, is_analysis)}

**Nonparametric validation (Main README: Line 116):**
{self._generate_nonparametric_validation(name, is_security, is_data_collection, is_database, is_ml_ai, is_pipeline, is_analysis)}

**Monte Carlo simulation (Main README: Line 119):**
{self._generate_monte_carlo_integration(name, is_security, is_data_collection, is_database, is_ml_ai, is_pipeline, is_analysis)}

**See [main README](../../../README.md) for complete methodology.**

---
"""

        return section

    def _generate_econometric_section(
        self,
        name,
        purpose,
        is_security,
        is_data_collection,
        is_database,
        is_ml_ai,
        is_pipeline,
        is_analysis,
    ) -> str:
        """Generate econometric causal inference section."""
        if is_security:
            return """Security infrastructure enables unbiased causal estimation:

**Data integrity protection:**
- **Panel data structure preservation:** Prevents data contamination that could bias fixed effects estimates
- **Audit logging:** Creates immutable record for falsification tests and placebo checks
- **Access control:** Ensures reproducibility by tracking data lineage and access patterns

**Causal identification support:**
- **Credential management:** Enables secure IV estimation by protecting instrumental variables data
- **Encryption:** Protects treatment assignment data in natural experiments
- **Authentication:** Validates data sources for propensity score matching

**Econometric workflow security:**
- Secure storage of regression outputs and coefficients
- Protected access to historical data for panel data models
- Authenticated API calls for real-time causal inference"""

        elif is_data_collection:
            return """Data collection infrastructure provides raw material for causal inference:

**Panel data structure:**
- **Temporal precision:** Enables within-unit variation analysis (player-game, team-season observations)
- **Longitudinal tracking:** Supports fixed effects models controlling for unobserved heterogeneity
- **Time-varying covariates:** Captures dynamic relationships for panel regression

**Causal identification:**
- **Instrumental variables:** Provides data for IV estimation (draft position, injuries as instruments)
- **Natural experiments:** Collects data around policy changes (rule changes, coaching transitions)
- **Regression discontinuity:** Captures data at cutoffs (playoff thresholds, draft lottery)

**Treatment effect estimation:**
- Propensity score matching: Comparable observations across treatment/control groups
- Difference-in-differences: Pre/post treatment data for causal impact estimation
- Heterogeneous effects: Data stratification for subgroup analysis"""

        elif is_database:
            return """Database infrastructure enables efficient econometric analysis:

**Panel data storage:**
- **Indexed time series:** Fast retrieval for fixed effects, random effects models
- **Player-season observations:** Enables within-player variation analysis
- **Team-game structure:** Supports difference-in-differences estimation

**Query optimization for causal inference:**
- **Instrumental variables:** Efficient joins for IV regression data preparation
- **Propensity score matching:** Fast similarity searches across observational units
- **Synthetic control:** Rapid donor pool selection for counterfactual construction

**Estimation infrastructure:**
- Clustered standard errors: Group-level aggregation for within-cluster correlation
- Bootstrap resampling: Efficient random sampling for uncertainty quantification
- Cross-validation: Partitioned data access for out-of-sample testing"""

        elif is_ml_ai:
            return """ML/AI infrastructure augments econometric causal inference:

**Causal ML integration:**
- **Double machine learning:** ML for nuisance parameter estimation in causal models
- **Causal forests:** Heterogeneous treatment effect estimation using random forests
- **Targeted learning:** Data-adaptive causal inference combining ML with econometrics

**Instrumental variables enhancement:**
- **Deep IV:** Neural networks for flexible IV estimation with high-dimensional instruments
- **Weak instrument detection:** ML-based tests for instrument relevance
- **Optimal instrument selection:** Automated IV selection from candidate set

**Propensity score refinement:**
- **ML for propensity scores:** Gradient boosting, random forests for treatment assignment modeling
- **Overlap diagnostics:** Automated detection of common support violations
- **Doubly robust estimation:** Combines outcome regression with propensity scores"""

        elif is_pipeline:
            return """Pipeline infrastructure orchestrates econometric workflows:

**Automated causal analysis:**
- **Sequential estimation:** Coordinates multi-stage IV and 2SLS estimation
- **Parallel model comparison:** Runs fixed effects, random effects, GMM in parallel
- **Model selection:** Automates Hausman tests, information criteria comparison

**Data preparation:**
- **Panel data construction:** Assembles player-season, team-game observations
- **Treatment variable creation:** Constructs indicators for natural experiments
- **Covariate engineering:** Generates interactions, polynomials, splines

**Quality control:**
- **Specification tests:** Automated falsification tests, placebo checks
- **Sensitivity analysis:** Tests robustness to specification changes
- **Diagnostic checks:** Validates identification assumptions"""

        elif is_analysis:
            return """Error analysis enables rigorous econometric validation:

**Model diagnostics:**
- **Residual analysis:** Detects heteroskedasticity, autocorrelation in panel regressions
- **Specification tests:** Ramsey RESET, linktest for functional form
- **Endogeneity detection:** Wu-Hausman tests for endogenous regressors

**Identification validation:**
- **Falsification tests:** Tests identifying assumptions on placebo outcomes
- **Overidentification tests:** Hansen J-test for IV validity
- **Weak instrument detection:** F-statistics for instrument relevance

**Causal inference quality:**
- **Covariate balance:** Checks balance in propensity score matching
- **Common support:** Validates overlap in treatment/control distributions
- **Sensitivity to unobservables:** Rosenbaum bounds for hidden bias"""

        else:
            # Generic econometric section
            return """This phase supports econometric causal inference:

**Panel data infrastructure:**
- Enables fixed effects and random effects estimation
- Supports instrumental variables (IV) regression
- Facilitates propensity score matching

**Causal identification:**
- Provides data for difference-in-differences estimation
- Enables regression discontinuity designs
- Supports synthetic control methods

**Treatment effect estimation:**
- Heterogeneous treatment effects across subgroups
- Time-varying treatment effects in dynamic panels
- Robustness checks and sensitivity analysis"""

    def _generate_nonparametric_section(
        self,
        name,
        purpose,
        is_security,
        is_data_collection,
        is_database,
        is_ml_ai,
        is_pipeline,
        is_analysis,
    ) -> str:
        """Generate nonparametric event modeling section."""
        if is_security:
            return """Security monitoring informs irregular event modeling:

**Empirical distribution estimation:**
- **Kernel density estimation:** Models security event frequencies without parametric assumptions
- **Bootstrap resampling:** Generates authentication failure scenarios from observed data
- **Empirical CDFs:** Draws anomaly occurrences directly from observed cumulative distributions

**Distribution-free validation:**
- **Kolmogorov-Smirnov tests:** Validates simulated security events match empirical distributions
- **Quantile checks:** Ensures tail behavior of rare security events matches observations
- **Changepoint detection:** Identifies security regime shifts using PELT algorithm"""

        elif is_data_collection:
            return """Raw data enables empirical distribution estimation without parametric assumptions:

**Irregular event frequencies:**
- **Kernel density estimation:** Models technical fouls, coach's challenges, ejections using empirical densities
- **Bootstrap resampling:** Generates injury occurrences by resampling from observed transaction data
- **Empirical CDFs:** Draws flagrant fouls, shot clock violations directly from observed distributions

**Performance variability:**
- **Quantile regression:** Models shooting "hot streaks" with fat-tailed distributions
- **Empirical transition matrices:** Captures make/miss patterns without geometric assumptions
- **Changepoint detection:** Identifies momentum shifts using PELT on play-by-play data

**Distribution-free inference:**
- No parametric assumptions (no Poisson, normal, exponential)
- Directly sample from empirical distributions
- Preserve tail behavior and extreme events"""

        elif is_database:
            return """Database queries enable efficient nonparametric estimation:

**Empirical distribution queries:**
- **Fast sampling:** Rapid random draws from large empirical datasets
- **Stratified sampling:** Conditional distributions by game context (playoff vs regular season)
- **Temporal queries:** Historical empirical distributions at specific time points

**Kernel density estimation:**
- **Bandwidth selection:** Efficient cross-validation for optimal smoothing
- **Local density computation:** Fast nearest-neighbor searches for KDE
- **Multivariate densities:** Joint empirical distributions across multiple variables

**Bootstrap infrastructure:**
- **Resampling efficiency:** Fast random sampling with replacement
- **Parallel bootstrap:** Distributed bootstrap replications
- **Block bootstrap:** Time series bootstrap preserving temporal dependence"""

        elif is_ml_ai:
            return """ML/AI enhances nonparametric modeling:

**Flexible function approximation:**
- **Neural networks:** Universal approximators without functional form assumptions
- **Random forests:** Nonparametric regression trees for conditional distributions
- **Gaussian processes:** Nonparametric Bayesian approach with uncertainty quantification

**Density estimation:**
- **Normalizing flows:** Deep generative models for complex empirical distributions
- **Mixture density networks:** Neural networks outputting full conditional distributions
- **Variational autoencoders:** Learn latent representations of irregular events

**Distribution-free prediction:**
- **Conformal prediction:** Distribution-free prediction intervals with coverage guarantees
- **Quantile regression forests:** Estimate conditional quantiles without distributional assumptions
- **Kernel methods:** Nonparametric classification and regression"""

        elif is_pipeline:
            return """Pipeline orchestrates nonparametric estimation workflows:

**Automated empirical analysis:**
- **Kernel density estimation pipeline:** Automated bandwidth selection and smoothing
- **Bootstrap coordination:** Manages parallel bootstrap replications
- **Empirical CDF construction:** Builds cumulative distributions from raw data

**Distribution-free validation:**
- **Kolmogorov-Smirnov tests:** Validates simulated vs. empirical distributions
- **Q-Q plots:** Visual checks of distributional fit without parametric assumptions
- **Goodness-of-fit tests:** Distribution-free tests (Anderson-Darling, Cramér-von Mises)

**Irregular event simulation:**
- Samples technical fouls from empirical KDE
- Draws injuries from bootstrap resampled data
- Generates momentum shifts via changepoint detection"""

        elif is_analysis:
            return """Error analysis validates nonparametric models:

**Distribution-free diagnostics:**
- **Kolmogorov-Smirnov tests:** Validates simulated event frequencies match empirical distributions
- **Q-Q plots:** Checks tail behavior without assuming specific distributions
- **Empirical coverage:** Tests prediction interval calibration

**Nonparametric validation:**
- **Cross-validation:** Out-of-sample testing without distributional assumptions
- **Bootstrap confidence intervals:** Distribution-free uncertainty quantification
- **Permutation tests:** Distribution-free hypothesis testing

**Irregular event validation:**
- Checks technical foul simulation matches observed rates
- Validates injury frequency distributions
- Tests momentum shift detection accuracy"""

        else:
            return """This phase supports nonparametric event modeling:

**Empirical distributions:**
- Kernel density estimation for irregular events
- Bootstrap resampling from observed data
- Empirical CDFs without parametric assumptions

**Distribution-free methods:**
- No assumptions on functional form
- Direct sampling from empirical distributions
- Preserves tail behavior and extreme events"""

    def _generate_context_adaptive_section(
        self,
        name,
        purpose,
        is_security,
        is_data_collection,
        is_database,
        is_ml_ai,
        is_pipeline,
        is_analysis,
    ) -> str:
        """Generate context-adaptive simulations section."""
        if is_security:
            return """Using security context, simulations adapt dynamically:

**Data availability context:**
- Models degraded performance under security constraints
- Simulates authenticated vs. anonymous access scenarios
- Incorporates encryption overhead in real-time predictions

**Audit-driven behavior:**
- Uses security logs to model access patterns
- Incorporates anomaly detection in simulation branching
- Adapts to detected security events"""

        elif is_data_collection:
            return """Using collected data, simulations adapt to:

**Historical context:**
- Queries team standings at exact date to model "playoff push" vs. "tanking" behavior
- Uses schedule density (back-to-backs, road trips) for fatigue modeling
- Incorporates playoff seeding implications in late-season game intensity

**Player career arcs:**
- Estimates aging curves with player fixed effects + time-varying coefficients
- Models "prime years" vs. "declining phase" using nonlinear age effects
- Tracks skill evolution (3PT%, assist rates) across player development

**Game situation dynamics:**
- Adapts strategy based on real-time score differential
- Incorporates time remaining for late-game adjustments
- Uses momentum detection for psychological effects"""

        elif is_database:
            return """Using database queries, simulations adapt in real-time:

**Dynamic parameter retrieval:**
- Queries player fatigue levels for current minute load
- Fetches recent performance trends (last 5 games)
- Retrieves matchup-specific data (defender vs. offensive player history)

**Context-specific estimation:**
- Pulls playoff vs. regular season coefficients
- Queries home vs. away performance differentials
- Retrieves clutch vs. non-clutch performance data

**Temporal adaptation:**
- Historical queries at exact game time for realistic context
- Dynamic updates based on game flow
- Real-time incorporation of lineup changes"""

        elif is_ml_ai:
            return """Using ML/AI, simulations adapt intelligently:

**Real-time predictions:**
- Neural networks for instant win probability updates
- Reinforcement learning for adaptive strategy selection
- Transfer learning from historical to current game context

**Context-aware embeddings:**
- Vector representations capture game situation nuances
- Attention mechanisms focus on relevant historical context
- Contextual bandits for dynamic decision-making

**Personalized modeling:**
- Player-specific models learned from individual history
- Team-specific strategy models
- Matchup-specific performance predictions"""

        elif is_pipeline:
            return """Pipeline coordinates context-adaptive simulation:

**Dynamic workflow orchestration:**
- Routes requests based on game context (playoff vs. regular season)
- Prioritizes computations for critical game situations
- Scales resources for high-stakes simulations

**Context injection:**
- Injects player fatigue into possession modeling
- Incorporates momentum into strategy selection
- Updates parameters based on game flow

**Adaptive branching:**
- Different simulation paths for different contexts
- Context-specific event probability distributions
- Dynamic strategy optimization"""

        elif is_analysis:
            return """Error analysis enables adaptive corrections:

**Real-time calibration:**
- Detects model drift and triggers recalibration
- Identifies context-specific biases for correction
- Adjusts confidence intervals based on error patterns

**Adaptive validation:**
- Context-specific error thresholds
- Dynamic model selection based on current context
- Real-time quality monitoring"""

        else:
            return """Using this phase's capabilities, simulations adapt to:

**Game context:**
- Score differential and time remaining
- Playoff vs. regular season
- Home vs. away venue

**Player state:**
- Fatigue levels and minute load
- Recent performance trends
- Matchup-specific adjustments"""

    def _generate_panel_data_integration(
        self,
        name,
        is_security,
        is_data_collection,
        is_database,
        is_ml_ai,
        is_pipeline,
        is_analysis,
    ) -> str:
        """Generate panel data integration paragraph."""
        if is_security:
            return "- Security measures protect panel data integrity for fixed effects estimation"
        elif is_data_collection:
            return "- Collected data forms player-season, team-game panel structure for econometric analysis"
        elif is_database:
            return "- Database schema optimized for panel data retrieval (indexed by player, season, game)"
        elif is_ml_ai:
            return "- ML models trained on panel data structure with cross-sectional and time series dimensions"
        elif is_pipeline:
            return "- Pipeline constructs panel data observations and manages panel regression workflows"
        elif is_analysis:
            return "- Error analysis validates panel data model assumptions (no serial correlation, homoskedasticity)"
        else:
            return "- This phase supports panel data regression infrastructure"

    def _generate_nonparametric_validation(
        self,
        name,
        is_security,
        is_data_collection,
        is_database,
        is_ml_ai,
        is_pipeline,
        is_analysis,
    ) -> str:
        """Generate nonparametric validation paragraph."""
        if is_security:
            return "- Security logs validated using Kolmogorov-Smirnov tests against empirical distributions"
        elif is_data_collection:
            return "- Collected event frequencies validated using distribution-free tests (K-S, Anderson-Darling)"
        elif is_database:
            return "- Database queries enable efficient K-S tests for distribution-free validation"
        elif is_ml_ai:
            return "- ML predictions validated using conformal prediction with distribution-free guarantees"
        elif is_pipeline:
            return "- Pipeline automates nonparametric validation tests (K-S, Q-Q plots, goodness-of-fit)"
        elif is_analysis:
            return "- Error analysis uses nonparametric tests to validate model-free assumptions"
        else:
            return "- This phase supports nonparametric validation infrastructure"

    def _generate_monte_carlo_integration(
        self,
        name,
        is_security,
        is_data_collection,
        is_database,
        is_ml_ai,
        is_pipeline,
        is_analysis,
    ) -> str:
        """Generate Monte Carlo integration paragraph."""
        if is_security:
            return "- Security framework enables 10,000+ secure simulation runs with parameter uncertainty"
        elif is_data_collection:
            return "- Collected data provides empirical distributions for Monte Carlo sampling with uncertainty"
        elif is_database:
            return "- Database enables fast parameter retrieval for 10,000+ Monte Carlo simulation runs"
        elif is_ml_ai:
            return "- ML models provide parameter distributions for Monte Carlo uncertainty quantification"
        elif is_pipeline:
            return "- Pipeline orchestrates 10,000+ parallel Monte Carlo simulations with parameter uncertainty"
        elif is_analysis:
            return "- Error analysis validates Monte Carlo coverage and prediction interval calibration"
        else:
            return "- This phase supports Monte Carlo simulation infrastructure"

    def _insert_enhancement(
        self, current_content: str, enhancement_section: str
    ) -> str:
        """Insert enhancement section into README."""
        # Find insertion point (before "Related Documentation" or at end)
        if "## Related Documentation" in current_content:
            return current_content.replace(
                "## Related Documentation",
                enhancement_section + "\n## Related Documentation",
            )
        elif "## Navigation" in current_content:
            return current_content.replace(
                "## Navigation", enhancement_section + "\n## Navigation"
            )
        else:
            # Append to end
            return current_content + "\n" + enhancement_section


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhance phase READMEs with methodology"
    )
    parser.add_argument("sub_phase_id", nargs="?", help="Sub-phase ID (e.g., 0.8)")
    parser.add_argument("--all", action="store_true", help="Enhance all sub-phases")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing"
    )

    args = parser.parse_args()

    enhancer = PhaseREADMEEnhancer(dry_run=args.dry_run)

    if args.all:
        print("\nEnhancing all Phase 0 sub-phases (0.8-0.17)...\n")
        success_count = 0
        for i in range(8, 18):
            sub_phase_id = f"0.{i}"
            if enhancer.enhance_sub_phase(sub_phase_id):
                success_count += 1

        print(f"\n{'='*70}")
        print(f"Completed: {success_count}/10 sub-phases enhanced")
        print(f"{'='*70}\n")

    elif args.sub_phase_id:
        enhancer.enhance_sub_phase(args.sub_phase_id)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
