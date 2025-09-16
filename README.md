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

1. **Copy the migration script to your dbt repo:**
   ```bash
   cp migrate_test_arguments.py /path/to/your-dbt-project/bin/
   ```
2. **Run a dry-run first (recommended):**
   ```bash
   python bin/migrate_test_arguments.py --dry-run
   ```
3. **Review the output, then migrate for real:**
   ```bash
   python bin/migrate_test_arguments.py
   ```

##### Optional Arguments

- `--models-dir [path]` – specify an alternate models folder
- `--dry-run` – only preview changes, do not write files
- See full help: `python bin/migrate_test_arguments.py --help`

## Example

**Before (deprecated):**
```yaml
tests:
  - accepted_values:
      values: ['active', 'inactive']
      config:
        where: "created_at > '2020-01-01'"
```

**After (migrated):**
```yaml
tests:
  - accepted_values:
      arguments:
        values: ['active', 'inactive']
      config:
        where: "created_at > '2020-01-01'"
```

## Automated Testing

This repo includes a complete pytest suite:
- Ensures both dry-run and in-place migration produces correct results
- Validates the migration handles built-in and plugin tests

**Run tests with:**
```bash
pytest
```
Tests live in `tests/test_migration.py`.

## Documentation

See [requirements.md](requirements.md) for full technical documentation, usage notes, error handling, and recovery strategies.

## Safety Notes

- Always commit to git before running the migration!
- The script is read/write and will update your YAML files in-place (unless in `--dry-run`)
- Handles parse errors gracefully and skips malformed YAML files

## License

MIT

## Maintainers

- Tony Johnson (primary author)
- Contributions welcomed!

## Feedback & Issues

Open an issue in GitHub or [contact](mailto:youremail@domain.com) for feature requests and bug reports.

***

This README provides context for data engineering teams, highlights migration rationale, and gives everything needed for setup, use, and validation.

Sources
