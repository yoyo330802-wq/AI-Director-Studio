"""
Hermes - 任务路由器

根据用户指令关键词，路由到合适的Agent类型
"""
import re
from typing import Literal
from pathlib import Path
import yaml


class TaskRouter:
    """
    任务路由器

    根据关键词匹配，决定任务类型：
    - engineer: 开发、代码、搭建、实现、系统、网站
    - researcher: 调研、研究、分析、竞品、资料、数据
    - creator: 方案、文案、脚本、撰写、创作
    """

    # Agent类型关键词
    ENGINEER_KEYWORDS = [
        "开发", "代码", "搭建", "实现", "系统", "网站", "写", "coding",
        "program", "build", "create", "功能", "feature", "bug", "修复",
        "添加", "修改", "优化", "性能", "安全", "测试", "部署"
    ]

    RESEARCHER_KEYWORDS = [
        "调研", "研究", "分析", "竞品", "资料", "数据", "市场", "用户",
        "research", "analyze", "survey", "investigate", "compare",
        "报告", "recommend", "建议", "评估"
    ]

    CREATOR_KEYWORDS = [
        "方案", "文案", "脚本", "撰写", "创作", "写", "文章", "内容",
        "plan", "write", "content", "script", "draft", "proposal",
        "文档", "说明", "指南"
    ]

    def __init__(self, config_path: str = None):
        self.config = {}
        if config_path:
            self._load_config(config_path)

    def _load_config(self, config_path: str):
        """从YAML加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        except Exception:
            pass

    def route(self, command: str) -> Literal["engineer", "researcher", "creator"]:
        """
        根据指令路由到合适的Agent

        Args:
            command: 用户指令

        Returns:
            Agent类型: engineer | researcher | creator
        """
        command_lower = command.lower()

        # 优先检查明确指令
        engineer_score = self._calculate_score(command_lower, self.ENGINEER_KEYWORDS)
        researcher_score = self._calculate_score(command_lower, self.RESEARCHER_KEYWORDS)
        creator_score = self._calculate_score(command_lower, self.CREATOR_KEYWORDS)

        scores = {
            "engineer": engineer_score,
            "researcher": researcher_score,
            "creator": creator_score,
        }

        # 返回得分最高的类型
        return max(scores, key=scores.get)

    def _calculate_score(self, text: str, keywords: list[str]) -> int:
        """计算文本与关键词的匹配得分"""
        score = 0
        for keyword in keywords:
            # 精确匹配或单词边界匹配
            if keyword.lower() in text:
                score += 1
            # 正则匹配更长的词组
            if re.search(rf'\b{re.escape(keyword)}\b', text, re.IGNORECASE):
                score += 2
        return score

    def is_engineer_task(self, command: str) -> bool:
        """判断是否为Engineering任务（走GAN流程）"""
        return self.route(command) == "engineer"

    def get_sprint_from_command(self, command: str) -> str:
        """从指令中提取Sprint编号"""
        # 匹配 S1, S2, Sprint1, Sprint2 等
        match = re.search(r'(?:Sprint?\s*)(\d+)', command, re.IGNORECASE)
        if match:
            return f"S{match.group(1)}"
        return "S1"


# 全局单例
task_router = TaskRouter()
