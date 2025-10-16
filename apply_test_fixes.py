#!/usr/bin/env python3
"""Bulk fix extraction tests to bypass connect() and set client directly."""

from pathlib import Path

test_file = Path("tests/test_bigquery_loader.py")
content = test_file.read_text()

# Pattern: Tests that use nested patch and need fixing
# Find test functions between specific markers

fixes = [
    # test_extract_table_with_columns
    {
        "old": """def test_extract_table_with_columns(bigquery_connection, mock_bigquery):
    \"\"\"Test extracting specific columns from a table.\"\"\"
    with patch("google.cloud.bigquery.Client") as mock_client_class:
        mock_job = MagicMock()
        mock_job.__iter__.return_value = iter([])
        mock_client = Mock()
        mock_client.query.return_value = mock_job
        mock_client_class.return_value = mock_client

        extractor = BigQueryExtractor(bigquery_connection)
        extractor.connect()""",
        "new": """def test_extract_table_with_columns(bigquery_connection, mock_bigquery):
    \"\"\"Test extracting specific columns from a table.\"\"\"
    mock_job = MagicMock()
    mock_job.__iter__.return_value = iter([])
    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client""",
    },
]

for fix in fixes:
    if fix["old"] in content:
        content = content.replace(fix["old"], fix["new"])
        print("✓ Applied fix")
    else:
        print("✗ Pattern not found")

test_file.write_text(content)
print(f"\\nUpdated {test_file}")
