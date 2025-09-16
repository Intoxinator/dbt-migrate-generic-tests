# dbt-migrate-generic-tests

Migrate all generic dbt tests in your YAML resource files to the new `arguments:` key format—required for dbt v1.10+ and recommended best practices. This script updates your test definitions in-place across all YAML files in your models directory and supports dry-run validation and automated testing.

## Why You Need This

Recent dbt releases ([v1.10+](https://docs.getdbt.com/docs/dbt-versions/core-upgrade/upgrading-to-v1.8)) have **deprecated** the old style of specifying test arguments as top-level keys for generic tests. The new format requires all arguments be nested under the `arguments:` key, or dbt will throw warnings or errors. This migration tool automates the process across an entire repo, reducing manual error and wasted time.

## Supported Test Types

- **Built-in dbt tests:** `unique`, `not_null`, `accepted_values`, `relationships`
- **dbt-utils tests:** `expression_is_true`, `unique_combination_of_columns`, `equal_rowcount`, ...and many more
- **dbt-expectations tests:** All standard expectation-form tests (`expect_*`)
- **Custom tests:** Any generic test following dbt's conventions

## Features

- **Bulk migration:** Updates `.yml` and `.yaml` throughout `models` and subdirectories in-place  
- **Selective:** Only migrates tests that actually require the new `arguments` structure  
- **Dry-run mode:** Preview all changes before applying  
- **Type-safe:** Written for reliability and auditability
- **Automated test suite:** Full pytest coverage ensures future proofing

## Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/dbt-migrate-generic-tests.git
cd dbt-migrate-generic-tests

# (Optional) Create a Python virtualenv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Or for dev/testing:
pip install pytest pyyaml
```

## Usage

Run the migration script and provide the path to the root of the dbt repository you want to update:

```bash
python src/migrate_test_arguments.py /path/to/dbt-project
```

By default the script inspects the `models` directory inside the specified repository root. You can point it at a different models directory (relative to the repository root or an absolute path) with `--models-dir`:

```bash
python src/migrate_test_arguments.py /path/to/dbt-project --models-dir data_warehouse/models
```

Add `--dry-run` to preview the changes without rewriting your files.
