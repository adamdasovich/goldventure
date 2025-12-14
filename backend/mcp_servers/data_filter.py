"""
In-Environment Data Filtering
Implements filtering and aggregation of data before returning to Claude.

Key principle from Anthropic's article:
"Process large datasets within the execution environment before returning
results to the model... performing aggregations and joins without passing
raw data through the context window."

This module provides utilities to:
1. Filter large result sets to relevant rows
2. Aggregate data to reduce token usage
3. Extract only requested fields
4. Summarize large datasets
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from functools import wraps
import json


@dataclass
class FilterConfig:
    """Configuration for data filtering"""
    max_items: int = 50           # Max items to return
    max_string_length: int = 500  # Max length for string fields
    include_fields: List[str] = None  # Only include these fields
    exclude_fields: List[str] = None  # Exclude these fields
    summarize_lists: bool = True  # Summarize long lists instead of returning all
    summarize_threshold: int = 20  # Summarize if more than this many items


class DataFilter:
    """
    Filter and transform tool results before returning to Claude.

    This reduces token usage by:
    - Limiting result set sizes
    - Truncating long strings
    - Extracting only relevant fields
    - Summarizing large datasets
    """

    @staticmethod
    def filter_result(data: Any, config: FilterConfig = None) -> Any:
        """
        Filter a tool result based on configuration.

        Args:
            data: The raw tool result
            config: Filter configuration

        Returns:
            Filtered data optimized for token efficiency
        """
        if config is None:
            config = FilterConfig()

        if isinstance(data, dict):
            return DataFilter._filter_dict(data, config)
        elif isinstance(data, list):
            return DataFilter._filter_list(data, config)
        elif isinstance(data, str):
            return DataFilter._filter_string(data, config)
        else:
            return data

    @staticmethod
    def _filter_dict(data: Dict, config: FilterConfig) -> Dict:
        """Filter a dictionary result"""
        result = {}

        for key, value in data.items():
            # Skip excluded fields
            if config.exclude_fields and key in config.exclude_fields:
                continue

            # Only include specified fields
            if config.include_fields and key not in config.include_fields:
                continue

            # Recursively filter nested structures
            if isinstance(value, dict):
                result[key] = DataFilter._filter_dict(value, config)
            elif isinstance(value, list):
                result[key] = DataFilter._filter_list(value, config)
            elif isinstance(value, str):
                result[key] = DataFilter._filter_string(value, config)
            else:
                result[key] = value

        return result

    @staticmethod
    def _filter_list(data: List, config: FilterConfig) -> Any:
        """Filter a list result"""
        total_count = len(data)

        # If list is small enough, filter each item
        if total_count <= config.max_items:
            return [DataFilter.filter_result(item, config) for item in data]

        # For large lists, summarize or truncate
        if config.summarize_lists and total_count > config.summarize_threshold:
            # Return summary with sample items
            sample_items = [DataFilter.filter_result(item, config)
                          for item in data[:5]]  # First 5 items
            return {
                "_summary": True,
                "total_count": total_count,
                "showing": len(sample_items),
                "sample_items": sample_items,
                "note": f"Showing first {len(sample_items)} of {total_count} items. Use pagination or more specific filters for full results."
            }

        # Otherwise, truncate to max_items
        truncated = [DataFilter.filter_result(item, config)
                    for item in data[:config.max_items]]
        if total_count > config.max_items:
            truncated.append({
                "_truncated": True,
                "omitted_count": total_count - config.max_items
            })
        return truncated

    @staticmethod
    def _filter_string(data: str, config: FilterConfig) -> str:
        """Filter a string result"""
        if len(data) <= config.max_string_length:
            return data
        return data[:config.max_string_length] + f"... [truncated, {len(data) - config.max_string_length} more chars]"


class ResultAggregator:
    """
    Aggregate results from multiple tool calls or large datasets.

    This enables "in-environment" aggregation as recommended by Anthropic,
    reducing what needs to pass through the context window.
    """

    @staticmethod
    def aggregate_companies(companies: List[Dict]) -> Dict:
        """Aggregate company list into summary statistics"""
        if not companies:
            return {"count": 0, "companies": []}

        return {
            "total_companies": len(companies),
            "by_exchange": ResultAggregator._group_and_count(companies, "exchange"),
            "by_status": ResultAggregator._group_and_count(companies, "status"),
            "total_projects": sum(c.get("number_of_projects", 0) for c in companies),
            "companies": companies[:10] if len(companies) > 10 else companies,
            "_note": f"Showing {min(10, len(companies))} of {len(companies)}" if len(companies) > 10 else None
        }

    @staticmethod
    def aggregate_projects(projects: List[Dict]) -> Dict:
        """Aggregate project list into summary statistics"""
        if not projects:
            return {"count": 0, "projects": []}

        return {
            "total_projects": len(projects),
            "by_stage": ResultAggregator._group_and_count(projects, "stage"),
            "by_country": ResultAggregator._group_and_count(projects, "country"),
            "by_commodity": ResultAggregator._group_and_count(projects, "commodity"),
            "flagship_count": sum(1 for p in projects if p.get("is_flagship")),
            "total_gold_oz": sum(p.get("total_gold_ounces", 0) or 0 for p in projects),
            "projects": projects[:10] if len(projects) > 10 else projects,
            "_note": f"Showing {min(10, len(projects))} of {len(projects)}" if len(projects) > 10 else None
        }

    @staticmethod
    def aggregate_financings(financings: List[Dict]) -> Dict:
        """Aggregate financing list into summary statistics"""
        if not financings:
            return {"count": 0, "financings": []}

        total_raised = sum(f.get("amount_raised", 0) or 0 for f in financings)

        return {
            "total_financings": len(financings),
            "total_raised": total_raised,
            "average_raise": total_raised / len(financings) if financings else 0,
            "by_type": ResultAggregator._group_and_count(financings, "financing_type"),
            "recent_financings": financings[:5],  # Most recent 5
            "_note": f"Showing 5 most recent of {len(financings)} financings" if len(financings) > 5 else None
        }

    @staticmethod
    def aggregate_market_data(data_points: List[Dict]) -> Dict:
        """Aggregate market data into summary"""
        if not data_points:
            return {"count": 0, "data": []}

        prices = [d.get("close", 0) for d in data_points if d.get("close")]
        volumes = [d.get("volume", 0) for d in data_points if d.get("volume")]

        return {
            "data_points": len(data_points),
            "date_range": {
                "start": data_points[-1].get("date") if data_points else None,
                "end": data_points[0].get("date") if data_points else None
            },
            "price_summary": {
                "high": max(prices) if prices else None,
                "low": min(prices) if prices else None,
                "average": sum(prices) / len(prices) if prices else None,
                "latest": prices[0] if prices else None
            },
            "volume_summary": {
                "total": sum(volumes),
                "average": sum(volumes) / len(volumes) if volumes else None
            },
            "latest_data": data_points[0] if data_points else None,
            "_note": f"Summary of {len(data_points)} data points" if len(data_points) > 1 else None
        }

    @staticmethod
    def _group_and_count(items: List[Dict], field: str) -> Dict[str, int]:
        """Group items by a field and count occurrences"""
        counts = {}
        for item in items:
            value = item.get(field, "Unknown")
            if value:
                counts[value] = counts.get(value, 0) + 1
        return counts


def filtered_tool(config: FilterConfig = None):
    """
    Decorator to automatically filter tool results.

    Usage:
        @filtered_tool(FilterConfig(max_items=20))
        def my_tool_handler(self, **params):
            return large_result
    """
    if config is None:
        config = FilterConfig()

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return DataFilter.filter_result(result, config)
        return wrapper
    return decorator


def smart_aggregate(data_type: str):
    """
    Decorator to automatically aggregate results based on data type.

    Usage:
        @smart_aggregate("companies")
        def list_companies(self):
            return {"companies": [...]}
    """
    aggregators = {
        "companies": ResultAggregator.aggregate_companies,
        "projects": ResultAggregator.aggregate_projects,
        "financings": ResultAggregator.aggregate_financings,
        "market_data": ResultAggregator.aggregate_market_data,
    }

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Find the list to aggregate
            if isinstance(result, dict):
                for key in [data_type, f"{data_type}_list", "items", "results"]:
                    if key in result and isinstance(result[key], list):
                        aggregator = aggregators.get(data_type)
                        if aggregator and len(result[key]) > 10:
                            result[key] = aggregator(result[key])
                        break

            return result
        return wrapper
    return decorator


class TokenEstimator:
    """
    Estimate token usage for results.
    Helps decide when to apply filtering/aggregation.
    """

    @staticmethod
    def estimate_tokens(data: Any) -> int:
        """
        Rough estimate of tokens for a data structure.

        Rule of thumb: ~4 characters per token for JSON.
        """
        if data is None:
            return 1

        json_str = json.dumps(data, default=str)
        return len(json_str) // 4

    @staticmethod
    def should_filter(data: Any, max_tokens: int = 2000) -> bool:
        """Check if data should be filtered based on estimated tokens"""
        return TokenEstimator.estimate_tokens(data) > max_tokens
