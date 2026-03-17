"""
统计信息收集器

提供@with_metrics装饰器，自动收集Tool执行的统计信息：
- 执行次数
- 成功率
- 平均执行时间
- 错误信息

Usage:
    from framework.tools.metrics import with_metrics, metrics
    
    @with_metrics
    def web_search(params: SearchParams) -> SearchOutput:
        # Implementation
        pass
    
    # 查看统计
    stats = metrics.get_stats('web_search')
    print(f"成功率: {stats['success_rate']}")
"""

import time
import json
from pathlib import Path
from functools import wraps
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ToolMetrics:
    """Tool统计信息收集器"""
    
    def __init__(self, storage_path: str = "metrics/tools.json"):
        """
        初始化统计收集器
        
        Args:
            storage_path: 统计信息存储路径
        """
        self.storage_path = Path(storage_path)
        self.metrics: Dict[str, Any] = {}
        self._load()
    
    def record(
        self,
        tool_id: str,
        execution_time_ms: float,
        success: bool,
        error: Optional[str] = None,
        params_hash: Optional[str] = None
    ):
        """
        记录一次Tool执行
        
        Args:
            tool_id: Tool标识符
            execution_time_ms: 执行时间（毫秒）
            success: 是否成功
            error: 错误信息（可选）
            params_hash: 参数哈希（可选，用于缓存分析）
        """
        if tool_id not in self.metrics:
            self.metrics[tool_id] = {
                'total_calls': 0,
                'success_count': 0,
                'total_time_ms': 0.0,
                'errors': [],
                'params_hashes': [],
                'first_call': None,
                'last_call': None,
                'last_updated': None
            }
        
        stats = self.metrics[tool_id]
        stats['total_calls'] += 1
        stats['success_count'] += 1 if success else 0
        stats['total_time_ms'] += execution_time_ms
        stats['last_call'] = datetime.now().isoformat()
        stats['last_updated'] = datetime.now().isoformat()
        
        if stats['first_call'] is None:
            stats['first_call'] = stats['last_call']
        
        if error:
            stats['errors'].append({
                'time': datetime.now().isoformat(),
                'error': error,
                'execution_time_ms': execution_time_ms
            })
            # 只保留最近100个错误
            stats['errors'] = stats['errors'][-100:]
        
        if params_hash:
            stats['params_hashes'].append(params_hash)
            # 只保留最近1000个哈希
            stats['params_hashes'] = stats['params_hashes'][-1000:]
        
        self._save()
    
    def get_stats(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        获取Tool统计信息
        
        Args:
            tool_id: Tool标识符
        
        Returns:
            统计信息字典，包含：
            - total_calls: 总调用次数
            - success_count: 成功次数
            - success_rate: 成功率
            - avg_execution_time_ms: 平均执行时间
            - total_time_ms: 总执行时间
            - recent_errors: 最近错误（最多10个）
            - first_call: 首次调用时间
            - last_call: 最后调用时间
        """
        stats = self.metrics.get(tool_id)
        if not stats:
            return None
        
        total_calls = stats['total_calls']
        success_count = stats['success_count']
        
        return {
            'tool_id': tool_id,
            'total_calls': total_calls,
            'success_count': success_count,
            'success_rate': success_count / total_calls if total_calls > 0 else 0.0,
            'avg_execution_time_ms': stats['total_time_ms'] / total_calls if total_calls > 0 else 0.0,
            'total_time_ms': stats['total_time_ms'],
            'recent_errors': stats['errors'][-10:],
            'first_call': stats['first_call'],
            'last_call': stats['last_call']
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Tool的统计信息"""
        return {
            tool_id: self.get_stats(tool_id)
            for tool_id in self.metrics.keys()
        }
    
    def reset_stats(self, tool_id: Optional[str] = None):
        """
        重置统计信息
        
        Args:
            tool_id: Tool标识符，如果为None则重置所有
        """
        if tool_id:
            if tool_id in self.metrics:
                del self.metrics[tool_id]
        else:
            self.metrics = {}
        
        self._save()
    
    def export_stats(self, export_path: str):
        """
        导出统计信息到文件
        
        Args:
            export_path: 导出路径
        """
        export_data = {
            'export_time': datetime.now().isoformat(),
            'tools': self.get_all_stats()
        }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _save(self):
        """持久化统计信息"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)
    
    def _load(self):
        """加载持久化的统计信息"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.metrics = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metrics: {e}")
                self.metrics = {}


# 全局统计收集器实例
metrics = ToolMetrics()


def with_metrics(tool_func: Callable) -> Callable:
    """
    自动收集统计信息的装饰器
    
    自动记录：
    - 执行时间
    - 成功/失败
    - 错误信息
    
    Args:
        tool_func: Tool函数
    
    Returns:
        包装后的函数
    
    Example:
        @with_metrics
        def web_search(params: SearchParams) -> SearchOutput:
            # Implementation
            pass
        
        # 查看统计
        stats = metrics.get_stats('web_search')
    """
    @wraps(tool_func)
    def wrapper(*args, **kwargs):
        tool_id = tool_func.__name__
        start_time = time.time()
        
        try:
            # 执行Tool
            result = tool_func(*args, **kwargs)
            
            # 记录成功
            execution_time_ms = (time.time() - start_time) * 1000
            metrics.record(tool_id, execution_time_ms, success=True)
            
            # 更新结果的execution_time_ms
            if hasattr(result, 'execution_time_ms'):
                result.execution_time_ms = execution_time_ms
            
            logger.debug(
                f"Tool {tool_id} succeeded in {execution_time_ms:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            # 记录失败
            execution_time_ms = (time.time() - start_time) * 1000
            metrics.record(
                tool_id, 
                execution_time_ms, 
                success=False, 
                error=str(e)
            )
            
            logger.error(
                f"Tool {tool_id} failed after {execution_time_ms:.2f}ms: {e}"
            )
            
            raise
    
    return wrapper


def get_tool_stats(tool_id: str) -> Optional[Dict[str, Any]]:
    """
    获取Tool统计信息的便捷函数
    
    Args:
        tool_id: Tool标识符
    
    Returns:
        统计信息字典
    """
    return metrics.get_stats(tool_id)


def get_all_tool_stats() -> Dict[str, Dict[str, Any]]:
    """获取所有Tool统计信息的便捷函数"""
    return metrics.get_all_stats()


__all__ = [
    'ToolMetrics',
    'metrics',
    'with_metrics',
    'get_tool_stats',
    'get_all_tool_stats'
]
