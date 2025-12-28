"""Visualization engine for generating charts from query results."""

import io
import base64
from typing import Optional, Dict, Any
from enum import Enum

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd


class ChartType(Enum):
    """Supported chart types."""

    PIE = "pie"
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    TABLE = "table"
    TILE = "tile"
    BUBBLE = "bubble"
    TREEMAP = "treemap"
    GEO_MAP = "geo_map"


class VisualizationEngine:
    """Generates visualizations from query results."""

    def __init__(self):
        """Initialize visualization engine."""
        self._setup_style()

    def _setup_style(self) -> None:
        """Configure matplotlib style."""
        try:
            plt.style.use("seaborn-v0_8-whitegrid")
        except OSError:
            # Fall back to default if seaborn style not available
            plt.style.use("default")
        plt.rcParams["figure.figsize"] = (10, 6)
        plt.rcParams["figure.dpi"] = 100

    def generate(
        self,
        data: Dict[str, Any],
        chart_type: ChartType,
        title: Optional[str] = None,
        options: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Generate visualization and return image + data.

        Args:
            data: Query result data with columns and rows.
            chart_type: Type of chart to generate.
            title: Optional chart title.
            options: Additional chart options.

        Returns:
            Dictionary with image_base64, image_format, raw_data, chart_type.
        """
        options = options or {}
        df = self._to_dataframe(data)

        if df.empty:
            return self._generate_empty_chart(title)

        chart_generators = {
            ChartType.PIE: self._generate_pie,
            ChartType.BAR: self._generate_bar,
            ChartType.LINE: self._generate_line,
            ChartType.AREA: self._generate_area,
            ChartType.TABLE: self._generate_table,
            ChartType.TILE: self._generate_tile,
            ChartType.TREEMAP: self._generate_treemap,
        }

        generator = chart_generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        image = generator(df, title, options)

        return {
            "image_base64": image,
            "image_format": "png",
            "raw_data": df.to_dict(orient="records"),
            "chart_type": chart_type.value,
        }

    def _to_dataframe(self, data: Dict) -> pd.DataFrame:
        """Convert query result to DataFrame.

        Args:
            data: Query result with columns and rows.

        Returns:
            Pandas DataFrame.
        """
        columns = [
            col.get("name", f"col_{i}") for i, col in enumerate(data.get("columns", []))
        ]
        rows = data.get("rows", [])

        if not columns and rows:
            # If no column info, create default column names
            if rows:
                columns = [f"col_{i}" for i in range(len(rows[0]))]

        return pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame()

    def _generate_empty_chart(self, title: Optional[str]) -> Dict[str, Any]:
        """Generate an empty chart placeholder.

        Args:
            title: Chart title.

        Returns:
            Chart result dictionary.
        """
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center",
            fontsize=16,
            color="gray",
        )
        ax.axis("off")
        if title:
            ax.set_title(title)

        return {
            "image_base64": self._fig_to_base64(fig),
            "image_format": "png",
            "raw_data": [],
            "chart_type": "empty",
        }

    def _generate_pie(
        self, df: pd.DataFrame, title: Optional[str], options: Dict
    ) -> str:
        """Generate pie chart.

        Args:
            df: Data as DataFrame.
            title: Chart title.
            options: Chart options.

        Returns:
            Base64 encoded PNG image.
        """
        fig, ax = plt.subplots()

        label_col = df.columns[0]
        value_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # Handle numeric conversion
        values = pd.to_numeric(df[value_col], errors="coerce").fillna(0)

        ax.pie(values, labels=df[label_col], autopct="%1.1f%%", startangle=90)
        ax.set_title(title or f"Distribution by {label_col}")

        return self._fig_to_base64(fig)

    def _generate_bar(
        self, df: pd.DataFrame, title: Optional[str], options: Dict
    ) -> str:
        """Generate bar chart.

        Args:
            df: Data as DataFrame.
            title: Chart title.
            options: Chart options.

        Returns:
            Base64 encoded PNG image.
        """
        fig, ax = plt.subplots()

        label_col = df.columns[0]
        value_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # Handle numeric conversion
        values = pd.to_numeric(df[value_col], errors="coerce").fillna(0)

        ax.barh(df[label_col].astype(str), values)
        ax.set_xlabel(value_col)
        ax.set_ylabel(label_col)
        ax.set_title(title or f"{value_col} by {label_col}")

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _generate_line(
        self, df: pd.DataFrame, title: Optional[str], options: Dict
    ) -> str:
        """Generate line chart.

        Args:
            df: Data as DataFrame.
            title: Chart title.
            options: Chart options.

        Returns:
            Base64 encoded PNG image.
        """
        fig, ax = plt.subplots()

        x_col = df.columns[0]

        for col in df.columns[1:]:
            values = pd.to_numeric(df[col], errors="coerce").fillna(0)
            ax.plot(df[x_col], values, label=col, marker="o")

        ax.set_xlabel(x_col)
        ax.set_title(title or "Trend Over Time")
        ax.legend()

        plt.xticks(rotation=45)
        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _generate_area(
        self, df: pd.DataFrame, title: Optional[str], options: Dict
    ) -> str:
        """Generate area chart.

        Args:
            df: Data as DataFrame.
            title: Chart title.
            options: Chart options.

        Returns:
            Base64 encoded PNG image.
        """
        fig, ax = plt.subplots()

        x_col = df.columns[0]
        y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        values = pd.to_numeric(df[y_col], errors="coerce").fillna(0)

        ax.fill_between(df[x_col], values, alpha=0.5)
        ax.plot(df[x_col], values)

        ax.set_xlabel(x_col)
        ax.set_title(title or "Volume Over Time")

        plt.xticks(rotation=45)
        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _generate_table(
        self, df: pd.DataFrame, title: Optional[str], options: Dict
    ) -> str:
        """Generate table visualization.

        Args:
            df: Data as DataFrame.
            title: Chart title.
            options: Chart options.

        Returns:
            Base64 encoded PNG image.
        """
        # Limit rows for display
        display_df = df.head(20)

        fig, ax = plt.subplots(figsize=(12, len(display_df) * 0.5 + 2))
        ax.axis("off")

        table = ax.table(
            cellText=display_df.values,
            colLabels=display_df.columns,
            cellLoc="center",
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)

        if title:
            ax.set_title(title, pad=20)

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _generate_tile(
        self, df: pd.DataFrame, title: Optional[str], options: Dict
    ) -> str:
        """Generate single-value tile.

        Args:
            df: Data as DataFrame.
            title: Chart title.
            options: Chart options.

        Returns:
            Base64 encoded PNG image.
        """
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.axis("off")

        value = df.iloc[0, 0] if len(df) > 0 else "N/A"

        ax.text(
            0.5,
            0.5,
            str(value),
            ha="center",
            va="center",
            fontsize=48,
            fontweight="bold",
        )

        if title:
            ax.text(0.5, 0.15, title, ha="center", va="center", fontsize=14)

        return self._fig_to_base64(fig)

    def _generate_treemap(
        self, df: pd.DataFrame, title: Optional[str], options: Dict
    ) -> str:
        """Generate treemap (simplified as nested bar).

        Args:
            df: Data as DataFrame.
            title: Chart title.
            options: Chart options.

        Returns:
            Base64 encoded PNG image.
        """
        # Simplified treemap as horizontal bar chart
        return self._generate_bar(df, title or "Treemap", options)

    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 PNG.

        Args:
            fig: Matplotlib figure.

        Returns:
            Base64 encoded string.
        """
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
