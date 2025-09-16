# dbt Generic Test Arguments Migration Tool

## Overview

This tool migrates dbt generic test YAML configurations to use the new 'arguments' key format, addressing the deprecation of top-level arguments in generic tests introduced in dbt v1.10+.

## Requirements

### System Requirements
- Python 3.7 or higher
- Access to your dbt project directory structure

### Python Dependencies
This script uses only Python standard library modules:
- `os` - File system operations
- `sys` - System-specific parameters and functions  
- `pathlib` - Object-oriented filesystem paths
- `re` - Regular expression operations
- `yaml` - YAML parsing and generation
- `argparse` - Command-line argument parsing
- `dataclasses` - Data classes for Python 3.7+
- `typing` - Type hints

**Note:** The `pyyaml` package may need to be installed if not already available:
```bash
pip install pyyaml
```

### dbt Project Structure
The script expects a standard dbt project structure:
```
your-dbt-project/
â”œâ”€â”€ dbt_project.yml
â”œâ”€â”€ models/
â”‚   â”œâ”€â”€ *.yml
â”‚   â”œâ”€â”€ *.yaml
â”‚   â””â”€â”€ subdirectories/
â”‚       â”œâ”€â”€ *.yml
â”‚       â””â”€â”€ *.yaml
â””â”€â”€ bin/
    â””â”€â”€ migrate_test_arguments.py
```

## What This Tool Does

### Problem Being Solved
Starting with dbt v1.10+, there's a deprecation warning for generic tests that have arguments specified at the top level. The new format requires test arguments to be nested under an `arguments` key.

**Before (deprecated):**
```yaml
models:
  - name: orders
    columns:
      - name: status
        tests:
          - accepted_values:
              values: ['placed', 'shipped', 'completed']
              config:
                where: "order_date > '2020-01-01'"
```

**After (required format):**
```yaml
models:
  - name: orders
    columns:
      - name: status
        tests:
          - accepted_values:
              arguments:
                values: ['placed', 'shipped', 'completed']
              config:
                where: "order_date > '2020-01-01'"
```

### Generic Tests Covered

The script automatically handles migration for:

**Built-in dbt tests:**
- `unique`
- `not_null`
- `accepted_values`
- `relationships`

**dbt-utils package tests:**
- `dbt_utils.equal_rowcount`
- `dbt_utils.expression_is_true`
- `dbt_utils.unique_combination_of_columns`
- `dbt_utils.relationships_where`
- `dbt_utils.mutually_exclusive_ranges`
- And 15+ other dbt-utils tests

**dbt-expectations package tests:**
- `dbt_expectations.expect_column_values_to_be_unique`
- `dbt_expectations.expect_column_values_to_be_of_type`
- `dbt_expectations.expect_table_row_count_to_equal`
- And 30+ other dbt-expectations tests

**Custom generic tests:**
- Any test following the `package.test_name` format
- Custom tests defined in your project

### File Processing
- Processes all `.yml` and `.yaml` files in the `models/` directory and subdirectories
- Handles tests defined at multiple levels:
  - Model-level tests
  - Column-level tests
  - Source table tests
  - Source column tests
  - Seed tests
  - Snapshot tests
- Preserves existing file formatting as much as possible
- Updates files in-place (with dry-run option available)

## Usage

### Installation
1. Place `migrate_test_arguments.py` in the `bin/` directory of your dbt project
2. Make it executable: `chmod +x bin/migrate_test_arguments.py`

### Running the Migration

**From your dbt project root directory:**

```bash
# Dry run to see what would be changed
python bin/migrate_test_arguments.py --dry-run

# Run the actual migration
python bin/migrate_test_arguments.py

# Specify custom models directory
python bin/migrate_test_arguments.py --models-dir path/to/models

# Get help
python bin/migrate_test_arguments.py --help
```

### Command Line Options

- `--models-dir`: Path to your models directory (default: "models")
- `--dry-run`: Preview changes without modifying files
- `--help`: Show help message

### Output Example

```
Found 15 YAML files to process
Files will be modified in place

Migrated 3 tests in models/marts/finance/finance.yml
Migrated 2 tests in models/marts/marketing/marketing.yml
Migrated 1 tests in models/staging/stripe/stripe.yml

Migration complete!
Files processed: 15
Files migrated: 3
Total test migrations: 6

Migrations performed:
  models/marts/finance/finance.yml: accepted_values, relationships
  models/marts/marketing/marketing.yml: dbt_utils.unique_combination_of_columns
  models/staging/stripe/stripe.yml: not_null
```

## Safety Features

1. **Dry Run Mode**: Test the migration without making changes
2. **Backup Recommendation**: Always commit your changes to git before running
3. **Selective Migration**: Only migrates tests that actually need updating
4. **Error Handling**: Continues processing other files if one file fails
5. **Validation**: Checks for proper dbt project structure

## Troubleshooting

### Common Issues

**"Models directory not found"**
- Ensure you're running the script from your dbt project root
- Check the `--models-dir` path is correct

**"Could not parse YAML"**
- Fix any YAML syntax errors in the reported file
- The script will skip invalid files and continue

**"No migrations needed"**
- Your tests may already be in the correct format
- Run with `--dry-run` to see what the script detects

### Post-Migration Steps

1. **Test your dbt project**: Run `dbt parse` and `dbt test` to ensure everything works
2. **Review changes**: Check the modified files to ensure the migration worked correctly
3. **Commit changes**: Add the migrated files to git
4. **Update dbt version**: Consider updating your `require_generic_test_arguments_property` flag in `dbt_project.yml`

## Limitations

- Only processes files in the models directory and subdirectories
- May not preserve all original YAML formatting (but preserves structure and comments)
- Does not modify `dbt_project.yml` configuration flags
- Custom tests not following standard naming patterns may need manual review

## Version Compatibility

- **Python**: 3.7+
- **dbt**: Works with all versions, designed for v1.10+ deprecation
- **YAML formats**: Handles both `.yml` and `.yaml` files
- **Operating Systems**: Cross-platform (Windows, macOS, Linux)

## Recovery

If you need to revert changes:
1. Use `git checkout` to restore original files
2. The script doesn't create backups automatically - rely on version control