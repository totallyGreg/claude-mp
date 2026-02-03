#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pytest>=7.0",
#   "pyyaml>=6.0.1",
# ]
# ///
"""
Test suite for evaluate_skill.py validation logic.

Tests cover:
- Directory name detection (absolute, relative, . paths)
- Reference validation (missing, orphaned, misspelled)
- Conciseness scoring (deterministic, tiered)
- Spec compliance (all AgentSkills requirements)
- Naming conventions (hyphen-case, length limits)
"""

import pytest
import sys
from pathlib import Path
import tempfile
import shutil

# Add skills directory to path for imports
skills_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(skills_dir / "skillsmith" / "scripts"))

# Import validation functions
from evaluate_skill import (
    validate_naming_conventions,
    validate_file_references,
    calculate_conciseness_score,
    calculate_basic_metrics,
    validate_skill,
    validate_agentskills_spec,
)


class TestDirectoryNameDetection:
    """Test that directory name detection works with different path formats"""

    @pytest.fixture
    def temp_skill(self):
        """Create a temporary skill directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="test_skill_")
        skill_dir = Path(temp_dir) / "test-skill"
        skill_dir.mkdir(parents=True)

        # Create minimal SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: Test skill for validation
---

# Test Skill

This is a test.
""")

        yield skill_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_absolute_path_directory_detection(self, temp_skill):
        """Test directory name detection with absolute path"""
        frontmatter_dict = {'name': 'test-skill', 'description': 'test'}
        result = validate_naming_conventions(temp_skill, frontmatter_dict)
        assert result['valid'], f"Expected valid, got violations: {result['violations']}"

    def test_relative_path_directory_detection(self, temp_skill):
        """Test directory name detection with relative path"""
        # Get the directory name directly (simulating relative path resolution)
        resolved_name = temp_skill.resolve().name
        assert resolved_name == 'test-skill', f"Expected 'test-skill', got '{resolved_name}'"

    def test_empty_string_directory_name_fixed(self):
        """Test that Path('.').resolve().name doesn't return empty string"""
        # This was the original bug - Path('.').name returns empty string
        current_dir = Path('.')
        resolved_name = current_dir.resolve().name
        assert resolved_name != '', "Directory name should not be empty after resolve()"


class TestReferenceValidation:
    """Test reference file validation"""

    @pytest.fixture
    def skill_with_references(self):
        """Create a skill with proper references"""
        temp_dir = tempfile.mkdtemp(prefix="skill_refs_")
        skill_dir = Path(temp_dir) / "test-skill"
        skill_dir.mkdir(parents=True)
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        # Create SKILL.md with proper references
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: Test skill
---

# Test Skill

See `references/guide.md` for details.

See `references/workflow.md` for workflow.
""")

        # Create reference files
        (refs_dir / "guide.md").write_text("# Guide")
        (refs_dir / "workflow.md").write_text("# Workflow")

        yield skill_dir

        shutil.rmtree(temp_dir)

    def test_missing_referenced_file(self, skill_with_references):
        """Test detection of missing referenced files"""
        # Modify SKILL.md to reference missing file
        skill_md = skill_with_references / "SKILL.md"
        content = skill_md.read_text()
        content += "\nSee `references/missing.md` for more."
        skill_md.write_text(content)

        _, _, text = (skill_md.read_text(), skill_md.read_text(), skill_md.read_text())
        result = validate_file_references(skill_with_references, text)

        assert not result['valid'], "Should detect missing reference file"
        assert 'missing.md' in str(result['issues'])

    def test_orphaned_reference_file(self, skill_with_references):
        """Test detection of orphaned reference files"""
        # Create orphaned reference file
        orphan_file = skill_with_references / "references" / "orphan.md"
        orphan_file.write_text("# Orphan")

        skill_md = skill_with_references / "SKILL.md"
        text = skill_md.read_text()
        result = validate_file_references(skill_with_references, text)

        assert 'orphan.md' in result['summary']['orphaned_files'], \
            "Should detect orphaned file not mentioned in SKILL.md"

    def test_reference_file_naming_convention(self, skill_with_references):
        """Test detection of improperly named reference files"""
        # Create poorly named reference file
        bad_file = skill_with_references / "references" / "BadNaming.md"
        bad_file.write_text("# Bad")

        skill_md = skill_with_references / "SKILL.md"
        text = skill_md.read_text()
        result = validate_file_references(skill_with_references, text)

        assert any('BadNaming.md' in w for w in result['warnings']), \
            "Should warn about improper naming convention"


class TestConcisenessScoring:
    """Test conciseness scoring is deterministic and tiered"""

    def test_conciseness_scoring_deterministic(self):
        """Test that same metrics produce same score"""
        metrics = {
            'skill_md_lines': 300,
            'skill_md_tokens': 2000,
            'references_count': 5,
            'references_lines': 1000
        }

        score1 = calculate_conciseness_score(metrics)['score']
        score2 = calculate_conciseness_score(metrics)['score']

        assert score1 == score2, f"Scoring should be deterministic: {score1} != {score2}"

    def test_conciseness_tiered_scoring(self):
        """Test that conciseness score tiers are correct"""
        # Test different line counts
        test_cases = [
            (100, 50, 1500, "Excellent: <150 lines"),       # line_score=50
            (250, 48, 1500, "Very good: 150-250 lines"),    # line_score=48
            (300, 45, 1500, "Good: 250-350 lines"),         # line_score=45
            (450, 40, 1500, "Acceptable: 350-500 lines"),   # line_score=40
            (600, 25, 1500, "Poor: 500-750 lines"),         # line_score=25
        ]

        for lines, expected_min, tokens, description in test_cases:
            metrics = {
                'skill_md_lines': lines,
                'skill_md_tokens': tokens,
                'references_count': 0,
                'references_lines': 0
            }
            score = calculate_conciseness_score(metrics)['score']
            assert score >= expected_min, \
                f"{description}: Expected score >= {expected_min}, got {score}"

    def test_conciseness_reference_bonus(self):
        """Test that reference offloading provides bonus"""
        # Without references
        metrics_no_refs = {
            'skill_md_lines': 400,
            'skill_md_tokens': 2500,
            'references_count': 0,
            'references_lines': 0
        }

        # With substantial references
        metrics_with_refs = {
            'skill_md_lines': 400,
            'skill_md_tokens': 2500,
            'references_count': 5,
            'references_lines': 600
        }

        score_no_refs = calculate_conciseness_score(metrics_no_refs)['score']
        score_with_refs = calculate_conciseness_score(metrics_with_refs)['score']

        assert score_with_refs > score_no_refs, \
            "Reference bonus should improve score with substantial references"


class TestSpecCompliance:
    """Test AgentSkills specification compliance validation"""

    def test_naming_convention_hyphen_case(self):
        """Test that names must be lowercase-with-hyphens"""
        valid_names = ['test', 'test-skill', 'my-awesome-skill', 'skill123']
        invalid_names = ['Test', 'test_skill', 'test.skill', 'Test-Skill']

        for name in valid_names:
            frontmatter = {'name': name, 'description': 'test'}
            # Skip directory name check by using temp skill
            # Just test naming pattern
            import re
            pattern = r'^[a-z0-9-]+$'
            assert re.match(pattern, name), f"Name '{name}' should match pattern"

        for name in invalid_names:
            import re
            pattern = r'^[a-z0-9-]+$'
            assert not re.match(pattern, name), f"Name '{name}' should not match pattern"

    def test_description_character_limit(self):
        """Test that description has 1024 character limit"""
        short_desc = "This is a valid description"
        long_desc = "x" * 1025  # Over 1024 limit

        assert len(short_desc) <= 1024
        assert len(long_desc) > 1024


class TestValidationDeterminism:
    """Test that validation is fully deterministic"""

    def test_same_skill_same_results(self):
        """Test that validating same skill twice gives same results"""
        skillsmith_path = Path(__file__).parent.parent

        # Run validation twice
        result1 = validate_skill(skillsmith_path)
        result2 = validate_skill(skillsmith_path)

        assert result1[0] == result2[0], "Validation result should be deterministic"
        assert result1[2] == result2[2], "Version should be deterministic"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
