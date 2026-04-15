"""
漫AI - 监控和日志服务
Sprint 4: S4-F4 监控日志
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import asyncio
from collections import defaultdict

from app.config import settings


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringService:
    """
    监控和告警服务
    
    功能:
    1. 结构化日志记录
    2. 任务失败告警
    3. 系统指标收集
    4. 告警通知 (预留Webhook接口)
    """
    
    def __init__(self):
        # 配置日志
        self._setup_logging()
        
        # 告警阈值
        self.alert_thresholds = {
            'task_failure_rate': 0.1,  # 10% 失败率告警
            'task_timeout_count': 5,   # 5个超时告警
            'api_error_rate': 0.05,    # 5% API错误率告警
        }
        
        # 指标计数器
        self.metrics = defaultdict(int)
        
        # 告警历史
        self.alert_history: list = []
    
    def _setup_logging(self):
        """配置日志"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 控制台 handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # 文件 handler
        file_handler = logging.FileHandler(settings.LOG_FILE or 'manai.log')
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # 根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        self.logger = logging.getLogger('manai.monitoring')
    
    def log(self, level: LogLevel, message: str, **kwargs):
        """记录日志"""
        extra_data = {
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        log_message = f"{message} | {json.dumps(extra_data)}"
        
        getattr(self.logger, level.value.lower())(log_message)
    
    def log_task_event(
        self,
        task_id: str,
        event: str,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ):
        """记录任务事件"""
        event_data = {
            'event': event,
            'task_id': task_id,
            'user_id': user_id,
            'status': status,
            'error': error,
            'duration_ms': duration_ms,
        }
        
        if error:
            self.log(LogLevel.ERROR, f"Task {event}: {task_id}", **event_data)
        elif status in ['completed', 'success']:
            self.log(LogLevel.INFO, f"Task {event}: {task_id}", **event_data)
        else:
            self.log(LogLevel.INFO, f"Task {event}: {task_id}", **event_data)
        
        # 更新指标
        self.metrics[f'task_{event}'] += 1
        if status:
            self.metrics[f'task_status_{status}'] += 1
    
    def log_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: int,
        user_id: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """记录 API 请求"""
        log_data = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'user_id': user_id,
            'error': error,
        }
        
        if status_code >= 500:
            self.log(LogLevel.ERROR, f"API Error: {method} {endpoint}", **log_data)
        elif status_code >= 400:
            self.log(LogLevel.WARNING, f"API Warning: {method} {endpoint}", **log_data)
        else:
            self.log(LogLevel.DEBUG, f"API Request: {method} {endpoint}", **log_data)
    
    async def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        发送告警
        
        Args:
            level: 告警级别
            title: 告警标题
            message: 告警消息
            metadata: 附加数据
        """
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level.value,
            'title': title,
            'message': message,
            'metadata': metadata or {},
        }
        
        # 记录告警
        self.alert_history.append(alert)
        self.log(
            LogLevel.WARNING if level != AlertLevel.CRITICAL else LogLevel.CRITICAL,
            f"ALERT: {title}",
            **alert
        )
        
        # 触发告警通知 (预留)
        if settings.ALERT_WEBHOOK_URL:
            await self._send_webhook_alert(alert)
        
        # CRITICAL 级别同时打印到 stderr
        if level == AlertLevel.CRITICAL:
            print(f"[CRITICAL ALERT] {title}: {message}", file=__import__('sys').stderr)
    
    async def _send_webhook_alert(self, alert: Dict[str, Any]):
        """发送 Webhook 告警"""
        # TODO: 实现 Webhook 告警
        # import aiohttp
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(settings.ALERT_WEBHOOK_URL, json=alert) as resp:
        #         pass
        pass
    
    async def alert_task_failure(
        self,
        task_id: str,
        user_id: str,
        error_message: str,
        execution_path: str,
    ):
        """告警: 任务失败"""
        await self.send_alert(
            level=AlertLevel.ERROR,
            title=f"视频生成任务失败",
            message=f"任务 {task_id} 执行失败: {error_message}",
            metadata={
                'task_id': task_id,
                'user_id': user_id,
                'execution_path': execution_path,
                'type': 'task_failure'
            }
        )
    
    async def alert_task_timeout(
        self,
        task_id: str,
        user_id: str,
        timeout_seconds: int,
    ):
        """告警: 任务超时"""
        self.metrics['task_timeout'] += 1
        
        # 检查是否达到告警阈值
        if self.metrics['task_timeout'] >= self.alert_thresholds['task_timeout_count']:
            await self.send_alert(
                level=AlertLevel.WARNING,
                title="任务超时数量增加",
                message=f"最近有 {self.metrics['task_timeout']} 个任务超时",
                metadata={
                    'timeout_count': self.metrics['task_timeout'],
                    'threshold': self.alert_thresholds['task_timeout_count'],
                    'type': 'task_timeout'
                }
            )
            # 重置计数器
            self.metrics['task_timeout'] = 0
    
    async def alert_high_failure_rate(self, failure_rate: float, task_count: int):
        """告警: 高失败率"""
        if failure_rate >= self.alert_thresholds['task_failure_rate']:
            await self.send_alert(
                level=AlertLevel.ERROR,
                title="任务失败率过高",
                message=f"当前失败率: {failure_rate:.1%}, 最近任务数: {task_count}",
                metadata={
                    'failure_rate': failure_rate,
                    'task_count': task_count,
                    'threshold': self.alert_thresholds['task_failure_rate'],
                    'type': 'high_failure_rate'
                }
            )
    
    def get_metrics(self) -> Dict[str, int]:
        """获取当前指标"""
        return dict(self.metrics)
    
    def get_recent_alerts(self, limit: int = 10) -> list:
        """获取最近的告警"""
        return self.alert_history[-limit:]


# 全局单例
monitoring_service = MonitoringService()
