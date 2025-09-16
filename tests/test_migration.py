import os
import tempfile
import shutil
import yaml
from pathlib import Path
import subprocess
import sys
import pytest

@pytest.fixture(scope="function")
def test_project():
    """Create a temp dbt project and cleanup after test."""
    test_dir = tempfile.mkdtemp(prefix="dbt_test_migration_")
    models_dir = Path(test_dir) / "models"
    models_dir.mkdir()
    test_yaml = (
        "version: 2\n"
        "models:\n"
        "  - name: test_model\n"
        "    tests:\n"
        "      - dbt_utils.expression_is_true:\n"
        "          expression: \"amount > 0\"\n"
        "          config:\n"
        "            severity: warn\n"
        "    columns:\n"
        "      - name: id\n"
        "        tests:\n"
        "          - unique\n"
        "          - not_null\n"
        "      - name: status\n"
        "        tests:\n"
        "          - accepted_values:\n"
        "              values: ['active', 'inactive']\n"
        "              config:\n"
        "                where: \"created_at > '2020-01-01'\"\n"
        "      - name: parent_id\n"
        "        tests:\n"
        "          - relationships:\n"
        "              to: ref('parent_table')\n"
        "              field: id\n"
        "sources:\n"
        "  - name: test_source\n"
        "    tables:\n"
        "      - name: raw_data\n"
        "        columns:\n"
        "          - name: combo_key\n"
        "            tests:\n"
        "              - dbt_utils.unique_combination_of_columns:\n"
        "                  combination_of_columns: ['col1', 'col2']\n"
    )
    with open(models_dir / "test_schema.yml", "w") as f:
        f.write(test_yaml)
    yield test_dir
    shutil.rmtree(test_dir)

def find_test(test_list, test_name):
    """
    Searches a list (such as model['tests']) for a dict with the given test_name (string) key.
    Returns the inner dict or None.
    """
    for item in test_list:
        if isinstance(item, dict) and test_name in item:
            return item[test_name]
    return None

@pytest.mark.parametrize("dry_run", [True, False])
def test_migration_script(test_project, dry_run):
    # Adjust the script path if needed
    script_path = Path("src") / "migrate_test_arguments.py"
    models_dir = Path(test_project) / "models"
    file_path = models_dir / "test_schema.yml"
    assert script_path.exists(), "Migration script not found in src/ directory"

    args = [sys.executable, str(script_path), "--models-dir", str(models_dir)]
    if dry_run:
        args.append("--dry-run")

    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

    with open(file_path) as f:
        content = f.read()
    if dry_run:
        assert "arguments:" not in content
    else:
        assert "arguments:" in content
        migrated_yaml = yaml.safe_load(content)
        # Validate model-level tests
        model = migrated_yaml["models"][0]
        expr_test = find_test(model.get("tests", []), "dbt_utils.expression_is_true")
        assert expr_test is not None, "expression_is_true test not found"
        assert isinstance(expr_test, dict), "expression test must be a dict"
        assert "arguments" in expr_test and "expression" in expr_test["arguments"]

        # Validate accepted_values in columns
        status_column = next(
            c for c in model.get("columns", [])
            if c.get("name") == "status"
        )
        accepted_test = find_test(status_column.get("tests", []), "accepted_values")
        assert accepted_test is not None, "accepted_values test not found"
        assert "arguments" in accepted_test and "values" in accepted_test["arguments"]

        # Validate relationships in columns
        parent_column = next(
            c for c in model.get("columns", [])
            if c.get("name") == "parent_id"
        )
        relationships_test = find_test(parent_column.get("tests", []), "relationships")
        assert relationships_test is not None, "relationships test not found"
        assert "arguments" in relationships_test and "to" in relationships_test["arguments"]

        # Validate combo test in sources
        sources = migrated_yaml.get("sources", [])
        assert sources, "sources missing from YAML"
        tables = sources[0].get("tables", [])
        assert tables, "tables missing from sources"
        combo_column = tables[0].get("columns", [])[0]
        combo_test = find_test(combo_column.get("tests", []), "dbt_utils.unique_combination_of_columns")
        assert combo_test is not None, "unique_combination_of_columns test not found"
        assert "arguments" in combo_test and "combination_of_columns" in combo_test["arguments"]
