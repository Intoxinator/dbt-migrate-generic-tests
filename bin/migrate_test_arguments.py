#!/usr/bin/env python3
"""
dbt Generic Test Arguments Migration Script

This script migrates dbt generic test YAML configurations to use the new 'arguments' key format,
addressing the deprecation of top-level arguments in generic tests.

Usage:
    python migrate_test_arguments.py

The script will:
1. Find all .yml and .yaml files in the models directory and subdirectories
2. Parse each file and identify generic tests
3. Move test arguments under the 'arguments' key
4. Update files in place while preserving formatting as much as possible
"""

import os
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import argparse
from dataclasses import dataclass


# Known generic tests from various sources
BUILTIN_GENERIC_TESTS = {
    'unique', 'not_null', 'accepted_values', 'relationships'
}

# Common tests from dbt-utils package
DBT_UTILS_TESTS = {
    'dbt_utils.equal_rowcount', 'dbt_utils.fewer_rows_than', 'dbt_utils.greater_rows_than',
    'dbt_utils.expression_is_true', 'dbt_utils.recency', 'dbt_utils.at_least_one',
    'dbt_utils.not_accepted_values', 'dbt_utils.relationships_where',
    'dbt_utils.mutually_exclusive_ranges', 'dbt_utils.sequential_values',
    'dbt_utils.unique_combination_of_columns', 'dbt_utils.cardinality_equality',
    'dbt_utils.equality', 'dbt_utils.not_null_proportion', 'dbt_utils.not_constant',
    'dbt_utils.accepted_range', 'dbt_utils.not_empty_string'
}

# Common tests from dbt-expectations package
DBT_EXPECTATIONS_TESTS = {
    'dbt_expectations.expect_column_values_to_be_unique',
    'dbt_expectations.expect_column_values_to_not_be_null',
    'dbt_expectations.expect_column_values_to_be_of_type',
    'dbt_expectations.expect_column_values_to_be_in_type_list',
    'dbt_expectations.expect_column_values_to_be_in_set',
    'dbt_expectations.expect_column_values_to_not_be_in_set',
    'dbt_expectations.expect_column_values_to_be_between',
    'dbt_expectations.expect_column_values_to_be_increasing',
    'dbt_expectations.expect_column_values_to_be_decreasing',
    'dbt_expectations.expect_column_value_lengths_to_be_between',
    'dbt_expectations.expect_column_value_lengths_to_equal',
    'dbt_expectations.expect_column_values_to_match_regex',
    'dbt_expectations.expect_column_values_to_not_match_regex',
    'dbt_expectations.expect_column_values_to_match_like_pattern',
    'dbt_expectations.expect_column_values_to_not_match_like_pattern',
    'dbt_expectations.expect_table_row_count_to_be_between',
    'dbt_expectations.expect_table_row_count_to_equal',
    'dbt_expectations.expect_table_column_count_to_be_between',
    'dbt_expectations.expect_table_column_count_to_equal',
    'dbt_expectations.expect_table_columns_to_match_ordered_list',
    'dbt_expectations.expect_table_columns_to_match_set',
    'dbt_expectations.expect_column_distinct_count_to_be_greater_than',
    'dbt_expectations.expect_column_distinct_count_to_equal',
    'dbt_expectations.expect_column_mean_to_be_between',
    'dbt_expectations.expect_column_median_to_be_between',
    'dbt_expectations.expect_column_quantile_values_to_be_between',
    'dbt_expectations.expect_column_stdev_to_be_between',
    'dbt_expectations.expect_column_sum_to_be_between',
    'dbt_expectations.expect_column_max_to_be_between',
    'dbt_expectations.expect_column_min_to_be_between'
}

# Combine all known generic tests
ALL_GENERIC_TESTS = BUILTIN_GENERIC_TESTS | DBT_UTILS_TESTS | DBT_EXPECTATIONS_TESTS


@dataclass
class TestMigration:
    """Tracks a test migration that was performed"""
    file_path: str
    test_name: str
    arguments_moved: List[str]
    line_number: Optional[int] = None


class GenericTestMigrator:
    """Handles migration of generic test arguments to the new format"""

    def __init__(self, models_dir: str = "models", dry_run: bool = False):
        self.models_dir = Path(models_dir)
        self.dry_run = dry_run
        self.migrations_performed: List[TestMigration] = []

    def find_yaml_files(self) -> List[Path]:
        """Find all .yml and .yaml files in the models directory"""
        yaml_files = []
        for pattern in ['**/*.yml', '**/*.yaml']:
            yaml_files.extend(self.models_dir.glob(pattern))
        return yaml_files

    def is_generic_test(self, test_key: str) -> bool:
        """Check if a test key represents a known generic test"""
        # Direct match
        if test_key in ALL_GENERIC_TESTS:
            return True

        # Check for custom tests that might follow package.test_name format
        if '.' in test_key:
            return True

        # Check if it looks like a custom generic test (not a config)
        config_keys = {'config', 'name', 'description', 'tags', 'meta', 'arguments'}
        return test_key not in config_keys

    def needs_migration(self, test_dict: Dict[str, Any]) -> bool:
        """Check if a test dictionary needs migration"""
        if not isinstance(test_dict, dict):
            return False

        # Already has arguments key - no migration needed
        if 'arguments' in test_dict:
            return False

        # Check if it has any keys that should be moved to arguments
        reserved_keys = {'config', 'name', 'description', 'tags', 'meta', 'test_name'}

        for key in test_dict.keys():
            if key not in reserved_keys:
                return True

        return False

    def migrate_test_dict(self, test_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate a single test dictionary to use arguments key"""
        if not self.needs_migration(test_dict):
            return test_dict

        new_dict = {}
        arguments = {}
        reserved_keys = {'config', 'name', 'description', 'tags', 'meta', 'test_name'}

        for key, value in test_dict.items():
            if key in reserved_keys:
                new_dict[key] = value
            else:
                arguments[key] = value

        if arguments:
            new_dict['arguments'] = arguments

        return new_dict

    def process_test_list(self, tests_list: List[Any]) -> tuple[List[Any], List[str]]:
        """Process a list of tests and return migrated list plus list of migrated test names"""
        migrated_tests = []
        migrated_test_names = []

        for test in tests_list:
            if isinstance(test, str):
                # Simple test name, no migration needed
                migrated_tests.append(test)
            elif isinstance(test, dict):
                # Test with configuration
                if len(test) == 1:
                    # Format: - test_name: {...}
                    test_name, test_config = next(iter(test.items()))
                    if self.is_generic_test(test_name) and isinstance(test_config, dict):
                        if self.needs_migration(test_config):
                            migrated_config = self.migrate_test_dict(test_config)
                            migrated_tests.append({test_name: migrated_config})
                            migrated_test_names.append(test_name)
                        else:
                            migrated_tests.append(test)
                    else:
                        migrated_tests.append(test)
                else:
                    # Format with test_name key or other format
                    if 'test_name' in test:
                        test_name = test['test_name']
                        if self.is_generic_test(test_name):
                            if self.needs_migration(test):
                                migrated_test = self.migrate_test_dict(test)
                                migrated_tests.append(migrated_test)
                                migrated_test_names.append(test_name)
                            else:
                                migrated_tests.append(test)
                        else:
                            migrated_tests.append(test)
                    else:
                        migrated_tests.append(test)
            else:
                migrated_tests.append(test)

        return migrated_tests, migrated_test_names

    def process_yaml_content(self, content: Dict[str, Any], file_path: str) -> tuple[Dict[str, Any], List[str]]:
        """Process YAML content and migrate tests"""
        all_migrated_tests = []

        # Process different resource types that can have tests
        for resource_type in ['models', 'sources', 'seeds', 'snapshots']:
            if resource_type in content:
                for resource in content[resource_type]:
                    # Tests at resource level
                    if 'tests' in resource or 'data_tests' in resource:
                        for test_key in ['tests', 'data_tests']:
                            if test_key in resource and isinstance(resource[test_key], list):
                                migrated_tests, migrated_names = self.process_test_list(resource[test_key])
                                resource[test_key] = migrated_tests
                                all_migrated_tests.extend(migrated_names)

                    # Tests at column level
                    if 'columns' in resource and isinstance(resource['columns'], list):
                        for column in resource['columns']:
                            if 'tests' in column or 'data_tests' in column:
                                for test_key in ['tests', 'data_tests']:
                                    if test_key in column and isinstance(column[test_key], list):
                                        migrated_tests, migrated_names = self.process_test_list(column[test_key])
                                        column[test_key] = migrated_tests
                                        all_migrated_tests.extend(migrated_names)

                    # Handle sources with tables
                    if resource_type == 'sources' and 'tables' in resource:
                        for table in resource['tables']:
                            # Tests at table level
                            if 'tests' in table or 'data_tests' in table:
                                for test_key in ['tests', 'data_tests']:
                                    if test_key in table and isinstance(table[test_key], list):
                                        migrated_tests, migrated_names = self.process_test_list(table[test_key])
                                        table[test_key] = migrated_tests
                                        all_migrated_tests.extend(migrated_names)

                            # Tests at column level within tables
                            if 'columns' in table and isinstance(table['columns'], list):
                                for column in table['columns']:
                                    if 'tests' in column or 'data_tests' in column:
                                        for test_key in ['tests', 'data_tests']:
                                            if test_key in column and isinstance(column[test_key], list):
                                                migrated_tests, migrated_names = self.process_test_list(column[test_key])
                                                column[test_key] = migrated_tests
                                                all_migrated_tests.extend(migrated_names)

        return content, all_migrated_tests

    def migrate_file(self, file_path: Path) -> bool:
        """Migrate a single YAML file"""
        try:
            # Read the original file content as string to preserve formatting
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Parse YAML
            try:
                yaml_content = yaml.safe_load(original_content)
            except yaml.YAMLError as e:
                print(f"Warning: Could not parse YAML in {file_path}: {e}")
                return False

            if not yaml_content:
                return False

            # Process the content
            migrated_content, migrated_tests = self.process_yaml_content(yaml_content, str(file_path))

            if not migrated_tests:
                # No migrations needed
                return False

            # Convert back to YAML with preserved style as much as possible
            migrated_yaml = yaml.dump(migrated_content,
                                    default_flow_style=False,
                                    sort_keys=False,
                                    allow_unicode=True,
                                    indent=2)

            # Record the migration
            migration = TestMigration(
                file_path=str(file_path),
                test_name=", ".join(set(migrated_tests)),
                arguments_moved=migrated_tests
            )
            self.migrations_performed.append(migration)

            if not self.dry_run:
                # Write the migrated content back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(migrated_yaml)

            print(f"{'[DRY RUN] ' if self.dry_run else ''}Migrated {len(migrated_tests)} tests in {file_path}")
            return True

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False

    def run_migration(self) -> None:
        """Run the migration on all YAML files"""
        yaml_files = self.find_yaml_files()

        if not yaml_files:
            print(f"No YAML files found in {self.models_dir}")
            return

        print(f"Found {len(yaml_files)} YAML files to process")
        print(f"{'Running in DRY RUN mode - no files will be modified' if self.dry_run else 'Files will be modified in place'}")
        print()

        migrated_count = 0
        for yaml_file in yaml_files:
            if self.migrate_file(yaml_file):
                migrated_count += 1

        print()
        print(f"Migration complete!")
        print(f"Files processed: {len(yaml_files)}")
        print(f"Files migrated: {migrated_count}")
        print(f"Total test migrations: {len(self.migrations_performed)}")

        if self.migrations_performed:
            print("\nMigrations performed:")
            for migration in self.migrations_performed:
                print(f"  {migration.file_path}: {migration.test_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate dbt generic test arguments to use the new 'arguments' key format"
    )
    parser.add_argument(
        "--models-dir",
        default="models",
        help="Path to the models directory (default: models)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )

    args = parser.parse_args()

    # Validate that we're in a dbt project directory
    if not Path(args.models_dir).exists():
        print(f"Error: Models directory '{args.models_dir}' not found")
        print("Make sure you're running this script from your dbt project root")
        sys.exit(1)

    migrator = GenericTestMigrator(models_dir=args.models_dir, dry_run=args.dry_run)
    migrator.run_migration()


if __name__ == "__main__":
    main()
