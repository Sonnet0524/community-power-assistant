"""
Tools层基础设施

提供统一的Tool开发基础设施

Usage:
    from framework.tools import (
        BaseParams, BaseOutput,
        with_metrics, metrics,
        ToolError, NetworkError, ValidationError
    )
    
    class SearchParams(BaseParams):
        query: str = Field(..., min_length=1)
    
    class SearchOutput(BaseOutput):
        results: List[SearchResult]
    
    @with_metrics
    def web_search(params: SearchParams) -> SearchOutput:
        try:
            # Implementation
            pass
        except NetworkError:
            raise
        except Exception as e:
            raise ToolError("SearchError", str(e))
"""

from .base import (
    BaseParams,
    BaseOutput,
    SearchResult,
    ListOutput,
    create_error_output,
    validate_positive_int,
    validate_non_empty_string
)

from .metrics import (
    ToolMetrics,
    metrics,
    with_metrics,
    get_tool_stats,
    get_all_tool_stats
)

from .errors import (
    ToolError,
    NetworkError,
    QuotaExceededError,
    ValidationError,
    TimeoutError,
    ResourceExhaustedError,
    NotFoundError,
    PermissionDeniedError
)

__all__ = [
    # Base classes
    'BaseParams',
    'BaseOutput',
    'SearchResult',
    'ListOutput',
    
    # Metrics
    'ToolMetrics',
    'metrics',
    'with_metrics',
    'get_tool_stats',
    'get_all_tool_stats',
    
    # Errors
    'ToolError',
    'NetworkError',
    'QuotaExceededError',
    'ValidationError',
    'TimeoutError',
    'ResourceExhaustedError',
    'NotFoundError',
    'PermissionDeniedError',
    
    # Utilities
    'create_error_output',
    'validate_positive_int',
    'validate_non_empty_string'
]
