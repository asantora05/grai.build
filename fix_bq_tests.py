#!/usr/bin/env python3
"""
Script to fix BigQuery loader tests by updating the pattern for mocking.

Changes:
1. Remove nested `with patch(...)` contexts
2. Set extractor.client directly instead of calling connect()
3. Use MagicMock for iterables
"""

from pathlib import Path

test_file = Path("tests/test_bigquery_loader.py")
content = test_file.read_text()

# Pattern 1: Remove nested patch contexts for extraction tests
# Replace:
#   with patch("google.cloud.bigquery.Client") as mock_client_class:
#       ...
#       extractor = BigQueryExtractor(bigquery_connection)
#       extractor.connect()
# With:
#       ...
#       extractor = BigQueryExtractor(bigquery_connection)
#       extractor.client = mock_client

patterns_to_fix = [
    "test_extract_table_with_columns",
    "test_extract_table_with_where_clause",
    "test_extract_table_with_limit",
    "test_extract_table_batching",
    "test_extract_table_with_dataset_prefix",
    "test_extract_table_fully_qualified",
    "test_extract_query",
    "test_get_table_schema",
    "test_extractor_close",
    "test_connect_bigquery",
    "test_extract_data",
]

print(f"Test file has {len(content)} characters")
print("Ready to apply fixes manually...")
