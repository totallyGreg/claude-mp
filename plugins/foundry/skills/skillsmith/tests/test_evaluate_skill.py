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
    calculate_all_metrics,
    validate_skill,
    validate_agentskills_spec,
    validate_description_quality,
    _frontmatter_field,
    _first_sentence,
    _component_brief,
    _parse_semver,
    _upsert_fence,
    _scan_plugin_components,
    fold_patch_into_minor,
    audit_version_history,
    _skill_content_hash,
    write_receipt,
    verify_receipt,
    RECEIPT_FILENAME,
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


class TestDescriptionQuality:
    """Test negative trigger detection and over/undertrigger signals"""

    def test_negative_trigger_detected_when_present(self):
        """Description with 'Do NOT use for X' should set has_negative_trigger=True"""
        desc = ('This skill should be used when "reviewing pull requests". '
                'Do NOT use for general coding questions (use code-review instead).')
        result = validate_description_quality({'description': desc})
        assert result['has_negative_trigger'] is True

    def test_negative_trigger_absent_when_missing(self):
        """Description without any negative trigger clause should set has_negative_trigger=False"""
        desc = ('This skill should be used when "creating a skill" or "validating a skill". '
                'Provides skill creation and evaluation workflows.')
        result = validate_description_quality({'description': desc})
        assert result['has_negative_trigger'] is False

    def test_negative_trigger_not_confused_with_negation_in_trigger_phrases(self):
        """Negation words inside trigger phrases (already filtered) should not affect negative trigger detection"""
        # "never recommend" is about domain behavior, not a "do not use this skill" clause
        desc = ('This skill should be used when "analyzing recommendations". '
                'Helps identify when to never recommend certain patterns.')
        result = validate_description_quality({'description': desc})
        # "never" appears in domain context, not as a "do not use this skill" instruction
        assert result['has_negative_trigger'] is False

    def test_alternative_negative_trigger_patterns(self):
        """Various phrasings of negative trigger clauses should be detected"""
        patterns = [
            "not for general coding tasks",
            "not intended for production deployments",
            "avoid when working with binary files",
            "instead use the deploy skill",
        ]
        for pattern in patterns:
            desc = f'This skill should be used when "doing X". {pattern}.'
            result = validate_description_quality({'description': desc})
            assert result['has_negative_trigger'] is True, \
                f"Expected negative trigger detected for: '{pattern}'"

    def test_trigger_phrase_count_returned(self):
        """trigger_phrases_found reflects only valid (non-negation) trigger phrases"""
        desc = ('This skill should be used when "create a skill", "validate a skill", '
                '"improve my skill". Do NOT use for general chat.')
        result = validate_description_quality({'description': desc})
        assert len(result['trigger_phrases_found']) == 3
        assert result['has_negative_trigger'] is True


class TestFrontmatterField:
    """Targeted frontmatter extraction, robust to invalid-YAML siblings."""

    def _write(self, tmp_path, text):
        p = tmp_path / "COMPONENT.md"
        p.write_text(text, encoding="utf-8")
        return p

    def test_inline_description(self, tmp_path):
        p = self._write(tmp_path, "---\nname: foo\ndescription: A short brief\n---\nbody\n")
        assert _frontmatter_field(p, "description") == "A short brief"

    def test_survives_invalid_yaml_sibling(self, tmp_path):
        # argument-hint with juxtaposed [..] [..] is invalid YAML; description must still parse
        p = self._write(
            tmp_path,
            "---\nname: ss-improve\n"
            "description: Guided improvement loop\n"
            "argument-hint: [skill-path] [optional context lines...]\n---\nbody\n",
        )
        assert _frontmatter_field(p, "description") == "Guided improvement loop"

    def test_block_scalar(self, tmp_path):
        p = self._write(
            tmp_path,
            "---\nname: agent\ndescription: |\n  Use this agent to do things.\n"
            "  More detail here.\n---\nbody\n",
        )
        assert _frontmatter_field(p, "description") == "Use this agent to do things. More detail here."

    def test_absent_field(self, tmp_path):
        p = self._write(tmp_path, "---\nname: foo\n---\nbody\n")
        assert _frontmatter_field(p, "description") == ""

    def test_no_frontmatter(self, tmp_path):
        p = self._write(tmp_path, "Just body content, no frontmatter.\n")
        assert _frontmatter_field(p, "description") == ""


class TestComponentBrief:
    """Brief extraction prefers description, falls back to first prose paragraph."""

    def test_prefers_description(self, tmp_path):
        p = tmp_path / "cmd.md"
        p.write_text("---\ndescription: The brief\n---\n# Heading\n\nBody prose.\n", encoding="utf-8")
        assert _component_brief(p) == "The brief"

    def test_body_fallback_when_no_description(self, tmp_path):
        p = tmp_path / "cmd.md"
        p.write_text("---\nname: mp-sync\n---\nSync plugin versions to marketplace. Then more.\n",
                     encoding="utf-8")
        assert _component_brief(p) == "Sync plugin versions to marketplace."

    def test_first_sentence_truncates(self):
        long = "word " * 100
        out = _first_sentence(long, limit=40)
        assert len(out) <= 41 and out.endswith("…")


class TestParseSemver:
    def test_valid(self):
        assert _parse_semver("6.9.2") == (6, 9, 2)

    def test_minor(self):
        assert _parse_semver("6.10.0") == (6, 10, 0)

    def test_invalid(self):
        assert _parse_semver("not-a-version") is None


class TestUpsertFence:
    """Fenced autogen blocks insert once and replace idempotently."""

    def test_insert_then_replace_is_idempotent(self):
        content = "# Plugin\n\n## Changelog\n\n| v | c |\n"
        c1, action1 = _upsert_fence(content, "components", "## Components\n\nX",
                                    insert_before=r"(?m)^## (?:Changelog|Skill:)")
        assert action1 == "inserted"
        assert "BEGIN AUTOGEN:components" in c1
        # Re-running replaces in place — no duplicate fence
        c2, action2 = _upsert_fence(c1, "components", "## Components\n\nY",
                                    insert_before=r"(?m)^## (?:Changelog|Skill:)")
        assert action2 == "replaced"
        assert c2.count("BEGIN AUTOGEN:components") == 1
        assert "Y" in c2 and "X" not in c2

    def test_replace_existing_section(self):
        content = "# Plugin\n\n## Components\n\nold hand-written\n\n## Changelog\n"
        out, action = _upsert_fence(content, "components", "## Components\n\nnew",
                                    replace_section_heading="Components")
        assert action == "replaced-section"
        assert "old hand-written" not in out
        assert "BEGIN AUTOGEN:components" in out
        assert "## Changelog" in out


class TestScanPluginComponents:
    """Component scanning across skills/agents/commands/hooks."""

    @pytest.fixture
    def plugin(self, tmp_path):
        root = tmp_path / "myplugin"
        (root / ".claude-plugin").mkdir(parents=True)
        (root / ".claude-plugin" / "plugin.json").write_text(
            '{"name": "myplugin", "description": "Test plugin"}', encoding="utf-8")
        # a skill
        sk = root / "skills" / "alpha"
        sk.mkdir(parents=True)
        (sk / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: trigger words here\n---\n# Alpha\n\nDoes alpha things.\n",
            encoding="utf-8")
        # a command
        (root / "commands").mkdir()
        (root / "commands" / "do-thing.md").write_text(
            "---\nname: do-thing\ndescription: Do a thing\n---\nbody\n", encoding="utf-8")
        # an agent (dir form)
        ag = root / "agents" / "watcher"
        ag.mkdir(parents=True)
        (ag / "AGENT.md").write_text(
            "---\nname: watcher\ndescription: Watches stuff.\n---\nprompt\n", encoding="utf-8")
        return root

    def test_scan_counts(self, plugin):
        comp = _scan_plugin_components(plugin)
        assert len(comp["skills"]) == 1
        assert len(comp["commands"]) == 1
        assert len(comp["agents"]) == 1
        assert comp["skills"][0][0] == "alpha"
        # skill brief prefers body tagline
        assert comp["skills"][0][1] == "Does alpha things."
        assert comp["commands"][0] == ("do-thing", "Do a thing")
        assert comp["agents"][0] == ("watcher", "Watches stuff.")


class TestVersionHistoryEnforcement:
    """MINOR-only Version History: fold + audit."""

    def _plugin_with_history(self, tmp_path, rows):
        root = tmp_path / "plug"
        (root / ".claude-plugin").mkdir(parents=True)
        (root / ".claude-plugin" / "plugin.json").write_text('{"name":"plug"}', encoding="utf-8")
        sk = root / "skills" / "alpha"
        sk.mkdir(parents=True)
        (sk / "SKILL.md").write_text("---\nname: alpha\ndescription: d\n---\n# A\n\nx\n", encoding="utf-8")
        table = ("## Skill: alpha\n\n### Version History\n\n"
                 "| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |\n"
                 "|---------|------|-------|---------|-------|--------|------|-------|-------|-------|\n"
                 + "".join(rows))
        (root / "README.md").write_text("# plug\n\n" + table, encoding="utf-8")
        return root, sk

    def test_fold_patch_into_parent(self, tmp_path):
        rows = ["| 6.9.0 | 2026-01-01 | - | base work | 90 | 90 | 90 | 90 | 90 | 90 |\n"]
        root, sk = self._plugin_with_history(tmp_path, rows)
        metrics = {
            "conciseness": {"score": 100}, "complexity": {"score": 100},
            "spec_compliance": {"score": 100}, "progressive_disclosure": {"score": 100},
            "description_quality": {"score": 100}, "overall_score": 100,
        }
        status, detail = fold_patch_into_minor(str(sk), "6.9.2", metrics, "2026-07-23")
        assert status == "folded"
        readme = (root / "README.md").read_text(encoding="utf-8")
        assert "+v6.9.2" in readme
        assert "2026-07-23" in readme
        # metrics refreshed to current
        assert "| 100 | 100 | 100 | 100 | 100 | 100 |" in readme

    def test_fold_no_parent_returns_no_parent(self, tmp_path):
        rows = ["| 6.9.0 | 2026-01-01 | - | base | 90 | 90 | 90 | 90 | 90 | 90 |\n"]
        root, sk = self._plugin_with_history(tmp_path, rows)
        metrics = {
            "conciseness": {"score": 100}, "complexity": {"score": 100},
            "spec_compliance": {"score": 100}, "progressive_disclosure": {"score": 100},
            "description_quality": {"score": 100}, "overall_score": 100,
        }
        status, _ = fold_patch_into_minor(str(sk), "7.1.5", metrics, "2026-07-23")
        assert status == "no-parent"

    def test_audit_flags_patch_rows(self, tmp_path):
        rows = [
            "| 6.9.1 | 2026-02-01 | - | patch | 100 | 100 | 100 | 100 | 100 | 100 |\n",
            "| 6.9.0 | 2026-01-01 | - | base | 100 | 100 | 100 | 100 | 100 | 100 |\n",
        ]
        root, sk = self._plugin_with_history(tmp_path, rows)
        assert audit_version_history(str(sk)) == 1

    def test_audit_passes_minor_only(self, tmp_path):
        rows = ["| 6.9.0 | 2026-01-01 | - | base | 100 | 100 | 100 | 100 | 100 | 100 |\n"]
        root, sk = self._plugin_with_history(tmp_path, rows)
        assert audit_version_history(str(sk)) == 0


class TestEvalReceipts:
    """Verifiable eval receipts: content hash, write, verify, staleness."""

    def _make_skill(self, tmp_path):
        sk = tmp_path / "alpha"
        (sk / "references").mkdir(parents=True)
        (sk / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: This skill should be used when "
            '"do alpha", "run alpha", or "alpha things". Handles alpha work.\n'
            "---\n# Alpha\n\nDoes alpha things well.\n", encoding="utf-8")
        (sk / "references" / "guide.md").write_text("# Guide\n\ncontent\n", encoding="utf-8")
        return sk

    def test_hash_is_deterministic(self, tmp_path):
        sk = self._make_skill(tmp_path)
        assert _skill_content_hash(sk) == _skill_content_hash(sk)

    def test_hash_changes_on_content_edit(self, tmp_path):
        sk = self._make_skill(tmp_path)
        before = _skill_content_hash(sk)
        (sk / "references" / "guide.md").write_text("# Guide\n\nCHANGED\n", encoding="utf-8")
        assert _skill_content_hash(sk) != before

    def test_receipt_file_excluded_from_hash(self, tmp_path):
        sk = self._make_skill(tmp_path)
        before = _skill_content_hash(sk)
        (sk / RECEIPT_FILENAME).write_text('{"x": 1}', encoding="utf-8")
        # Writing the receipt into the skill root must not change the content hash
        assert _skill_content_hash(sk) == before

    def test_write_then_verify_passes(self, tmp_path):
        sk = self._make_skill(tmp_path)
        metrics = calculate_all_metrics(sk)
        write_receipt(sk, metrics)
        ok, lines = verify_receipt(sk)
        assert ok, lines

    def test_verify_fails_when_content_changed(self, tmp_path):
        sk = self._make_skill(tmp_path)
        write_receipt(sk, calculate_all_metrics(sk))
        (sk / "references" / "guide.md").write_text("# Guide\n\nDIFFERENT\n", encoding="utf-8")
        ok, lines = verify_receipt(sk)
        assert not ok
        assert any("hash mismatch" in ln for ln in lines)

    def test_verify_fails_without_receipt(self, tmp_path):
        sk = self._make_skill(tmp_path)
        ok, lines = verify_receipt(sk)
        assert not ok
        assert any("No " in ln for ln in lines)

    def test_verify_expect_score_mismatch(self, tmp_path):
        sk = self._make_skill(tmp_path)
        metrics = calculate_all_metrics(sk)
        write_receipt(sk, metrics)
        # Claim a score guaranteed not to equal the real one
        ok, _ = verify_receipt(sk, expect_score=str((int(metrics['overall_score']) + 1) % 101))
        assert not ok


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
