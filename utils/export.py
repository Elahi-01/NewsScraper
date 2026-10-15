"""
Export utilities for results data.
"""

import io
import pandas as pd


def results_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Convert a DataFrame to CSV bytes for download.

    Args:
        df: pandas DataFrame with results.

    Returns:
        UTF-8 encoded CSV bytes.
    """
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    return buffer.getvalue()
