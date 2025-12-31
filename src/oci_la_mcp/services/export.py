"""Export service for query results."""

import csv
import io
import json
from typing import Dict, Any, Literal

import pandas as pd


class ExportService:
    """Service for exporting query results to various formats."""

    def export(
        self,
        data: Dict[str, Any],
        format: Literal["csv", "json"],
        include_metadata: bool = False,
    ) -> str:
        """Export query results to specified format.

        Args:
            data: Query result data with columns and rows.
            format: Export format ('csv' or 'json').
            include_metadata: Whether to include metadata in export.

        Returns:
            Exported data as string.

        Raises:
            ValueError: If unsupported format specified.
        """
        if format == "csv":
            return self._export_csv(data, include_metadata)
        elif format == "json":
            return self._export_json(data, include_metadata)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_csv(self, data: Dict[str, Any], include_metadata: bool) -> str:
        """Export to CSV format.

        Args:
            data: Query result data.
            include_metadata: Whether to include metadata.

        Returns:
            CSV string.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Get column names
        columns = [col.get("name", f"col_{i}") for i, col in enumerate(data.get("columns", []))]
        rows = data.get("rows", [])

        if not columns and rows:
            first_row = self._materialize_row(rows[0]) if rows else []
            columns = [f"col_{i}" for i in range(len(first_row))]

        # Write header
        writer.writerow(columns)

        # Write rows - ensure each row is properly materialized
        for row in rows:
            materialized = self._materialize_row(row)
            writer.writerow(materialized)

        return output.getvalue()

    def _materialize_row(self, row):
        """Ensure a row is a proper list of values.

        Args:
            row: Row data (may be list, tuple, dict, dict_values, or callable).

        Returns:
            List of values.
        """
        if row is None:
            return []
        elif callable(row):
            return list(row())
        elif hasattr(row, '__iter__') and not isinstance(row, (str, dict)):
            return list(row)
        elif isinstance(row, dict):
            return list(row.values())
        else:
            return [row]

    def _export_json(self, data: Dict[str, Any], include_metadata: bool) -> str:
        """Export to JSON format.

        Args:
            data: Query result data.
            include_metadata: Whether to include metadata.

        Returns:
            JSON string.
        """
        columns = [col.get("name", f"col_{i}") for i, col in enumerate(data.get("columns", []))]
        rows = data.get("rows", [])

        if not columns and rows:
            first_row = self._materialize_row(rows[0]) if rows else []
            columns = [f"col_{i}" for i in range(len(first_row))]

        # Convert to list of dictionaries
        records = []
        for row in rows:
            materialized = self._materialize_row(row)
            record = dict(zip(columns, materialized))
            records.append(record)

        if include_metadata:
            result = {
                "metadata": {
                    "total_count": data.get("total_count", len(records)),
                    "is_partial": data.get("is_partial", False),
                    "columns": data.get("columns", []),
                },
                "data": records,
            }
        else:
            result = records

        return json.dumps(result, indent=2, default=str)

    def to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Convert query results to pandas DataFrame.

        Args:
            data: Query result data.

        Returns:
            Pandas DataFrame.
        """
        columns = [col.get("name", f"col_{i}") for i, col in enumerate(data.get("columns", []))]
        rows = data.get("rows", [])

        if not columns and rows:
            columns = [f"col_{i}" for i in range(len(rows[0]))]

        return pd.DataFrame(rows, columns=columns)
