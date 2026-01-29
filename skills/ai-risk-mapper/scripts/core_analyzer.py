#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
# ///
"""
CoSAI Core Risk Analyzer

Core module providing comprehensive access to the CoSAI Risk Map framework data.
Supports both online (cached) and offline (bundled) schema access with 30+ query methods
for risk analysis, control mapping, gap assessment, and framework compliance.

Usage:
    from core_analyzer import RiskAnalyzer

    # Standard mode (uses ~/.cosai-cache/yaml/)
    analyzer = RiskAnalyzer()

    # Offline mode (uses bundled assets)
    analyzer = RiskAnalyzer(offline=True)

    # Custom path
    analyzer = RiskAnalyzer(yaml_dir='/path/to/yaml')

    # Query examples
    risks = analyzer.search_risks("data poisoning")
    controls = analyzer.get_controls_for_risk("DP")
    profile = analyzer.get_persona_risk_profile("personaModelProvider")
    gap = analyzer.assess_risk_gap("DP", ["controlTrainingDataSanitization"])
"""

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Risk:
    """Represents a CoSAI security risk."""

    id: str
    title: str
    short_description: str
    long_description: str
    category: str
    personas: List[str]
    controls: List[str]
    examples: List[str]
    mappings: Dict[str, List[str]]
    lifecycle_stages: List[str]
    impact_types: List[str]


@dataclass
class Control:
    """Represents a CoSAI security control."""

    id: str
    title: str
    description: str
    category: str
    personas: List[str]
    components: List[str]
    risks: List[str]
    mappings: Dict[str, List[str]]


@dataclass
class Component:
    """Represents a CoSAI AI system component."""

    id: str
    title: str
    description: str
    category: str
    edges: List[Dict[str, str]]


@dataclass
class Persona:
    """Represents a CoSAI stakeholder persona."""

    id: str
    title: str
    description: str
    responsibilities: List[str]
    mappings: Dict[str, List[str]]
    identification_questions: Optional[List[str]] = None


class RiskAnalyzer:
    """
    Core analyzer for CoSAI Risk Map data.

    Provides comprehensive access to risks, controls, components, and personas
    with support for both cached and offline (bundled) schema access.
    """

    def __init__(
        self,
        yaml_dir: Optional[Union[str, Path]] = None,
        offline: bool = False,
    ):
        """
        Initialize the analyzer with YAML data files.

        Args:
            yaml_dir: Path to the YAML data directory. If None, uses default paths.
            offline: If True and yaml_dir is None, uses bundled assets.
        """
        if yaml_dir:
            self.yaml_dir = Path(yaml_dir)
        elif offline:
            # Use bundled schemas from assets directory
            self.yaml_dir = (
                Path(__file__).parent.parent / "assets" / "cosai-schemas" / "yaml"
            )
        else:
            # Use cached schemas from user's home directory
            self.yaml_dir = Path.home() / ".cosai-cache" / "yaml"

        self.offline = offline
        self.risks: Dict[str, Risk] = {}
        self.controls: Dict[str, Control] = {}
        self.components: Dict[str, Component] = {}
        self.personas: Dict[str, Persona] = {}
        self.frameworks: Dict[str, Any] = {}

        if not self.yaml_dir.exists():
            raise FileNotFoundError(
                f"Schema directory not found: {self.yaml_dir}\n"
                f"Run fetch_cosai_schemas.py first or use offline=True for bundled schemas."
            )

        self._load_data()
        logger.info(
            "RiskAnalyzer initialized: %d risks, %d controls, %d components, %d personas",
            len(self.risks),
            len(self.controls),
            len(self.components),
            len(self.personas),
        )

    def _load_data(self) -> None:
        """Load all YAML data files."""
        self._load_risks()
        self._load_controls()
        self._load_components()
        self._load_personas()
        self._load_frameworks()

    def _load_risks(self) -> None:
        """Load risks from YAML."""
        risks_file = self.yaml_dir / "risks.yaml"
        if not risks_file.exists():
            logger.warning("Risks file not found: %s", risks_file)
            return

        with open(risks_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for risk_data in data.get("risks", []):
            risk = Risk(
                id=risk_data.get("id", ""),
                title=risk_data.get("title", ""),
                short_description=self._flatten_text(
                    risk_data.get("shortDescription", [])
                ),
                long_description=self._flatten_text(
                    risk_data.get("longDescription", [])
                ),
                category=risk_data.get("category", ""),
                personas=risk_data.get("personas", []),
                controls=risk_data.get("controls", []),
                examples=self._flatten_text_list(risk_data.get("examples", [])),
                mappings=risk_data.get("mappings", {}),
                lifecycle_stages=risk_data.get("lifecycleStages", []),
                impact_types=risk_data.get("impactTypes", []),
            )
            self.risks[risk.id] = risk
        logger.debug("Loaded %d risks", len(self.risks))

    def _load_controls(self) -> None:
        """Load controls from YAML."""
        controls_file = self.yaml_dir / "controls.yaml"
        if not controls_file.exists():
            logger.warning("Controls file not found: %s", controls_file)
            return

        with open(controls_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for control_data in data.get("controls", []):
            control = Control(
                id=control_data.get("id", ""),
                title=control_data.get("title", ""),
                description=self._flatten_text(control_data.get("description", [])),
                category=control_data.get("category", ""),
                personas=control_data.get("personas", []),
                components=control_data.get("components", []),
                risks=control_data.get("risks", []),
                mappings=control_data.get("mappings", {}),
            )
            self.controls[control.id] = control
        logger.debug("Loaded %d controls", len(self.controls))

    def _load_components(self) -> None:
        """Load components from YAML."""
        components_file = self.yaml_dir / "components.yaml"
        if not components_file.exists():
            logger.warning("Components file not found: %s", components_file)
            return

        with open(components_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Handle both flat and hierarchical component structures
        if "components" in data:
            for comp_data in data["components"]:
                self._add_component(comp_data)
        elif "categories" in data:
            self._extract_components(data.get("categories", []))
        logger.debug("Loaded %d components", len(self.components))

    def _extract_components(
        self, categories: List[Dict], parent_id: Optional[str] = None
    ) -> None:
        """Recursively extract components from hierarchical structure."""
        for category in categories:
            self._add_component(category, parent_id)
            # Recursively extract subcategories
            if "subcategory" in category:
                self._extract_components(category["subcategory"], category.get("id"))

    def _add_component(
        self, comp_data: Dict[str, Any], parent_id: Optional[str] = None
    ) -> None:
        """Add a single component to the components dictionary."""
        component_id = comp_data.get("id", "")
        if not component_id:
            return

        component = Component(
            id=component_id,
            title=comp_data.get("title", ""),
            description=self._flatten_text(comp_data.get("description", [])),
            category=parent_id or comp_data.get("category", "root"),
            edges=comp_data.get("edges", []),
        )
        self.components[component_id] = component

    def _load_personas(self) -> None:
        """Load personas from YAML."""
        personas_file = self.yaml_dir / "personas.yaml"
        if not personas_file.exists():
            logger.warning("Personas file not found: %s", personas_file)
            return

        with open(personas_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for persona_data in data.get("personas", []):
            persona = Persona(
                id=persona_data.get("id", ""),
                title=persona_data.get("title", ""),
                description=self._flatten_text(persona_data.get("description", [])),
                responsibilities=persona_data.get("responsibilities", []),
                mappings=persona_data.get("mappings", {}),
                identification_questions=persona_data.get("identificationQuestions"),
            )
            self.personas[persona.id] = persona
        logger.debug("Loaded %d personas", len(self.personas))

    def _load_frameworks(self) -> None:
        """Load framework mappings from YAML if available."""
        frameworks_file = self.yaml_dir / "frameworks.yaml"
        if not frameworks_file.exists():
            logger.debug("Frameworks file not found (optional): %s", frameworks_file)
            return

        with open(frameworks_file, "r", encoding="utf-8") as f:
            self.frameworks = yaml.safe_load(f) or {}
        logger.debug("Loaded frameworks data")

    def _flatten_text(self, text_data: Any) -> str:
        """Flatten text data (string or list) into a single string."""
        if isinstance(text_data, str):
            return text_data
        if isinstance(text_data, list):
            return " ".join(str(t) for t in text_data if t)
        return str(text_data) if text_data else ""

    def _flatten_text_list(self, text_data: Any) -> List[str]:
        """Flatten text data into a list of strings."""
        if isinstance(text_data, str):
            return [text_data]
        if isinstance(text_data, list):
            result = []
            for item in text_data:
                if isinstance(item, list):
                    result.extend(str(i) for i in item if i)
                elif item:
                    result.append(str(item))
            return result
        return [str(text_data)] if text_data else []

    # ========================================================================
    # Risk Operations
    # ========================================================================

    def find_risk(self, risk_id: str) -> Optional[Risk]:
        """
        Find a risk by ID.

        Args:
            risk_id: Risk identifier (e.g., 'DP' for Data Poisoning)

        Returns:
            Risk object or None if not found
        """
        return self.risks.get(risk_id)

    def get_all_risks(self) -> List[Risk]:
        """
        Get all risks.

        Returns:
            List of all risks
        """
        return list(self.risks.values())

    def search_risks(self, keyword: str) -> List[Risk]:
        """
        Search risks by keyword in title and descriptions.

        Args:
            keyword: Search term to match

        Returns:
            List of matching risks
        """
        keyword_lower = keyword.lower()
        return [
            risk
            for risk in self.risks.values()
            if keyword_lower in risk.title.lower()
            or keyword_lower in risk.short_description.lower()
            or keyword_lower in risk.long_description.lower()
        ]

    def get_risks_by_persona(self, persona_id: str) -> List[Risk]:
        """
        Get all risks relevant to a specific persona.

        Args:
            persona_id: Persona identifier

        Returns:
            List of risks relevant to the persona
        """
        return [risk for risk in self.risks.values() if persona_id in risk.personas]

    def get_risks_by_lifecycle_stage(self, stage: str) -> List[Risk]:
        """
        Get risks for a specific lifecycle stage.

        Args:
            stage: Lifecycle stage identifier

        Returns:
            List of risks in that lifecycle stage
        """
        return [
            risk for risk in self.risks.values() if stage in risk.lifecycle_stages
        ]

    def get_risks_by_impact_type(self, impact_type: str) -> List[Risk]:
        """
        Get risks by impact type.

        Args:
            impact_type: Impact type (security, privacy, safety, etc.)

        Returns:
            List of risks with that impact type
        """
        return [
            risk for risk in self.risks.values() if impact_type in risk.impact_types
        ]

    def get_risks_by_category(self, category: str) -> List[Risk]:
        """
        Get risks by category.

        Args:
            category: Risk category identifier

        Returns:
            List of risks in that category
        """
        return [risk for risk in self.risks.values() if risk.category == category]

    def get_risks_by_component(self, component_id: str) -> List[Risk]:
        """
        Get risks associated with controls that protect a specific component.

        Args:
            component_id: Component identifier

        Returns:
            List of risks relevant to that component
        """
        # Find controls that protect this component
        relevant_control_ids = {
            control.id
            for control in self.controls.values()
            if component_id in control.components
        }

        # Find risks that are mitigated by these controls
        return [
            risk
            for risk in self.risks.values()
            if any(control_id in risk.controls for control_id in relevant_control_ids)
        ]

    # ========================================================================
    # Control Operations
    # ========================================================================

    def find_control(self, control_id: str) -> Optional[Control]:
        """
        Find a control by ID.

        Args:
            control_id: Control identifier

        Returns:
            Control object or None if not found
        """
        return self.controls.get(control_id)

    def get_all_controls(self) -> List[Control]:
        """
        Get all controls.

        Returns:
            List of all controls
        """
        return list(self.controls.values())

    def search_controls(self, keyword: str) -> List[Control]:
        """
        Search controls by keyword in title and description.

        Args:
            keyword: Search term

        Returns:
            List of matching controls
        """
        keyword_lower = keyword.lower()
        return [
            control
            for control in self.controls.values()
            if keyword_lower in control.title.lower()
            or keyword_lower in control.description.lower()
        ]

    def get_controls_for_risk(self, risk_id: str) -> List[Control]:
        """
        Get all controls that mitigate a specific risk.

        Args:
            risk_id: Risk identifier

        Returns:
            List of applicable controls
        """
        risk = self.risks.get(risk_id)
        if not risk:
            return []

        return [
            self.controls[cid] for cid in risk.controls if cid in self.controls
        ]

    def get_controls_by_persona(self, persona_id: str) -> List[Control]:
        """
        Get all controls relevant to a specific persona.

        Args:
            persona_id: Persona identifier

        Returns:
            List of controls for the persona
        """
        return [
            control
            for control in self.controls.values()
            if persona_id in control.personas
        ]

    def get_controls_by_component(self, component_id: str) -> List[Control]:
        """
        Get controls that protect a specific component.

        Args:
            component_id: Component identifier

        Returns:
            List of controls protecting that component
        """
        return [
            control
            for control in self.controls.values()
            if component_id in control.components
        ]

    def get_controls_by_category(self, category: str) -> List[Control]:
        """
        Get controls by category.

        Args:
            category: Control category identifier

        Returns:
            List of controls in that category
        """
        return [
            control for control in self.controls.values() if control.category == category
        ]

    # ========================================================================
    # Component Operations
    # ========================================================================

    def find_component(self, component_id: str) -> Optional[Component]:
        """
        Find a component by ID.

        Args:
            component_id: Component identifier

        Returns:
            Component object or None if not found
        """
        return self.components.get(component_id)

    def get_all_components(self) -> List[Component]:
        """
        Get all components.

        Returns:
            List of all components
        """
        return list(self.components.values())

    def search_components(self, keyword: str) -> List[Component]:
        """
        Search components by keyword in title and description.

        Args:
            keyword: Search term

        Returns:
            List of matching components
        """
        keyword_lower = keyword.lower()
        return [
            component
            for component in self.components.values()
            if keyword_lower in component.title.lower()
            or keyword_lower in component.description.lower()
        ]

    def get_component_edges(self, component_id: str) -> List[Dict[str, str]]:
        """
        Get relationships (edges) for a component.

        Args:
            component_id: Component identifier

        Returns:
            List of edge relationships
        """
        component = self.components.get(component_id)
        if not component:
            return []
        return component.edges

    # ========================================================================
    # Persona Operations
    # ========================================================================

    def find_persona(self, persona_id: str) -> Optional[Persona]:
        """
        Find a persona by ID.

        Args:
            persona_id: Persona identifier

        Returns:
            Persona object or None if not found
        """
        return self.personas.get(persona_id)

    def get_all_personas(self) -> List[Persona]:
        """
        Get all personas.

        Returns:
            List of all personas
        """
        return list(self.personas.values())

    # ========================================================================
    # Framework Operations
    # ========================================================================

    def get_framework_mappings(self, risk_id: str, framework: str) -> List[str]:
        """
        Get framework mappings for a risk.

        Args:
            risk_id: Risk identifier
            framework: Framework name (mitre-atlas, nist-ai-rmf, stride, owasp-llm)

        Returns:
            List of framework references
        """
        risk = self.risks.get(risk_id)
        if not risk:
            return []

        mappings = risk.mappings.get(framework, [])
        return mappings if isinstance(mappings, list) else [mappings]

    def get_control_framework_mappings(
        self, control_id: str, framework: str
    ) -> List[str]:
        """
        Get framework mappings for a control.

        Args:
            control_id: Control identifier
            framework: Framework name

        Returns:
            List of framework references
        """
        control = self.controls.get(control_id)
        if not control:
            return []

        mappings = control.mappings.get(framework, [])
        return mappings if isinstance(mappings, list) else [mappings]

    def get_all_framework_mappings(self, risk_id: str) -> Dict[str, List[str]]:
        """
        Get all framework mappings for a risk.

        Args:
            risk_id: Risk identifier

        Returns:
            Dictionary of framework name to list of references
        """
        risk = self.risks.get(risk_id)
        if not risk:
            return {}
        return risk.mappings

    # ========================================================================
    # Analysis Operations
    # ========================================================================

    def assess_risk_gap(
        self, risk_id: str, implemented_controls: List[str]
    ) -> Dict[str, Any]:
        """
        Assess gaps between a risk and implemented controls.

        Args:
            risk_id: Risk identifier
            implemented_controls: List of implemented control IDs

        Returns:
            Assessment dictionary with coverage and gaps
        """
        risk = self.risks.get(risk_id)
        if not risk:
            return {"error": f"Risk not found: {risk_id}"}

        applicable_controls = set(risk.controls)
        implemented_set = set(implemented_controls) & applicable_controls
        gaps = applicable_controls - implemented_set

        coverage = (
            (len(implemented_set) / len(applicable_controls) * 100)
            if applicable_controls
            else 0
        )

        return {
            "risk_id": risk_id,
            "risk_title": risk.title,
            "applicable_controls": len(applicable_controls),
            "implemented_count": len(implemented_set),
            "coverage_percentage": round(coverage, 1),
            "missing_controls": [
                self.controls[cid] for cid in gaps if cid in self.controls
            ],
            "implemented_controls": [
                self.controls[cid] for cid in implemented_set if cid in self.controls
            ],
        }

    def get_persona_risk_profile(self, persona_id: str) -> Dict[str, Any]:
        """
        Get a complete risk profile for a persona.

        Args:
            persona_id: Persona identifier

        Returns:
            Risk profile with all relevant risks and controls
        """
        persona = self.personas.get(persona_id)
        if not persona:
            return {"error": f"Persona not found: {persona_id}"}

        relevant_risks = self.get_risks_by_persona(persona_id)
        relevant_controls = self.get_controls_by_persona(persona_id)

        # Group risks by category
        risks_by_category: Dict[str, List[Risk]] = {}
        for risk in relevant_risks:
            category = risk.category
            if category not in risks_by_category:
                risks_by_category[category] = []
            risks_by_category[category].append(risk)

        return {
            "persona_id": persona_id,
            "persona_title": persona.title,
            "description": persona.description,
            "responsibilities": persona.responsibilities,
            "risks_count": len(relevant_risks),
            "controls_count": len(relevant_controls),
            "risks": relevant_risks,
            "risks_by_category": risks_by_category,
            "controls": relevant_controls,
        }

    def search_all(self, keyword: str) -> Dict[str, List[Any]]:
        """
        Search across all entity types (risks, controls, components, personas).

        Args:
            keyword: Search term

        Returns:
            Dictionary with results by entity type
        """
        return {
            "risks": self.search_risks(keyword),
            "controls": self.search_controls(keyword),
            "components": self.search_components(keyword),
        }

    # ========================================================================
    # Export Operations
    # ========================================================================

    def export_risk_as_dict(self, risk_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a risk as a dictionary.

        Args:
            risk_id: Risk identifier

        Returns:
            Risk as dictionary or None
        """
        risk = self.risks.get(risk_id)
        if not risk:
            return None

        return {
            "id": risk.id,
            "title": risk.title,
            "shortDescription": risk.short_description,
            "longDescription": risk.long_description,
            "category": risk.category,
            "personas": risk.personas,
            "controls": risk.controls,
            "examples": risk.examples,
            "mappings": risk.mappings,
            "lifecycleStages": risk.lifecycle_stages,
            "impactTypes": risk.impact_types,
        }

    def export_control_as_dict(self, control_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a control as a dictionary.

        Args:
            control_id: Control identifier

        Returns:
            Control as dictionary or None
        """
        control = self.controls.get(control_id)
        if not control:
            return None

        return {
            "id": control.id,
            "title": control.title,
            "description": control.description,
            "category": control.category,
            "personas": control.personas,
            "components": control.components,
            "risks": control.risks,
            "mappings": control.mappings,
        }

    def export_all_risks_as_json(self) -> str:
        """
        Export all risks as JSON.

        Returns:
            JSON string of all risks
        """
        risks_list = [
            self.export_risk_as_dict(rid) for rid in self.risks.keys()
        ]
        return json.dumps(risks_list, indent=2)

    def export_all_controls_as_json(self) -> str:
        """
        Export all controls as JSON.

        Returns:
            JSON string of all controls
        """
        controls_list = [
            self.export_control_as_dict(cid) for cid in self.controls.keys()
        ]
        return json.dumps(controls_list, indent=2)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_statistics(self) -> Dict[str, int]:
        """
        Get basic statistics about the loaded data.

        Returns:
            Dictionary with counts of each entity type
        """
        return {
            "total_risks": len(self.risks),
            "total_controls": len(self.controls),
            "total_components": len(self.components),
            "total_personas": len(self.personas),
        }

    def get_risk_ids(self) -> List[str]:
        """Get all risk IDs."""
        return list(self.risks.keys())

    def get_control_ids(self) -> List[str]:
        """Get all control IDs."""
        return list(self.controls.keys())

    def get_component_ids(self) -> List[str]:
        """Get all component IDs."""
        return list(self.components.keys())

    def get_persona_ids(self) -> List[str]:
        """Get all persona IDs."""
        return list(self.personas.keys())


def main():
    """Example usage of the RiskAnalyzer."""
    # Configure logging for CLI usage
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Try offline mode first (bundled schemas)
    try:
        analyzer = RiskAnalyzer(offline=True)
    except FileNotFoundError:
        # Fall back to cached schemas
        try:
            analyzer = RiskAnalyzer()
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Print statistics
    stats = analyzer.get_statistics()
    print(f"\nCoSAI Risk Map Statistics:")
    print(f"  Risks:      {stats['total_risks']}")
    print(f"  Controls:   {stats['total_controls']}")
    print(f"  Components: {stats['total_components']}")
    print(f"  Personas:   {stats['total_personas']}")

    # Find a specific risk
    print("\n--- Example: Data Poisoning Risk ---")
    risk = analyzer.find_risk("DP")
    if risk:
        print(f"Risk: {risk.title}")
        print(f"Description: {risk.short_description[:100]}...")

        # Get controls for this risk
        controls = analyzer.get_controls_for_risk("DP")
        print(f"Applicable Controls: {len(controls)}")
        for control in controls[:3]:
            print(f"  - {control.title}")
        if len(controls) > 3:
            print(f"  ... and {len(controls) - 3} more")

    # Get persona profile
    print("\n--- Example: Model Provider Persona ---")
    profile = analyzer.get_persona_risk_profile("personaModelProvider")
    if "persona_title" in profile:
        print(f"Persona: {profile['persona_title']}")
        print(f"Relevant Risks: {profile['risks_count']}")
        print(f"Relevant Controls: {profile['controls_count']}")

    # Search example
    print("\n--- Example: Search for 'injection' ---")
    results = analyzer.search_all("injection")
    print(f"Found: {len(results['risks'])} risks, {len(results['controls'])} controls")


if __name__ == "__main__":
    main()
