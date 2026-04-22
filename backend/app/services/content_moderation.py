"""
漫AI - 内容审核服务
Sprint 4: S4-F2 内容审核
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from app.config import settings


class ModerationLevel(Enum):
    """审核级别"""
    SAFE = "safe"
    WARNING = "warning"
    BLOCK = "block"


@dataclass
class ModerationResult:
    """审核结果"""
    level: ModerationLevel
    reason: Optional[str]
    flagged_terms: List[str]
    score: float  # 0-1, 越高越危险


class ContentModerationService:
    """
    内容审核服务
    
    支持多种审核策略:
    1. 本地关键词过滤 (默认启用)
    2. 阿里云内容安全 API (可选)
    3. 自定义规则
    """
    
    # 敏感词分类
    PROHIBITED_TERMS = {
        # 色情低俗
        'porn', 'nude', 'naked', 'sex', 'sexual', 'erotic',
        '色情', '裸体', '性感', '色情内容',
        # 暴力血腥
        'violence', 'violent', 'blood', 'gore', 'kill', 'murder',
        '暴力', '血腥', '杀人', '谋杀',
        # 政治敏感
        'politics', 'political', 'government', 'president', 'politician',
        '政治', '政府', '领导人', '敏感人物',
        # 违法内容
        'drug', 'drugs', 'weapon', 'weapons', 'explosive',
        '毒品', '药物', '武器', '炸弹', '赌博',
        # 欺诈
        'scam', 'fraud', 'phishing', 'fake',
        '诈骗', '欺诈', '钓鱼',
    }
    
    # 警告词 (轻微违规但可以生成)
    WARNING_TERMS = {
        'gun', 'knife', 'blood', 'scar', 'wound',
        '恐怖', '惊悚', '黑暗', '阴暗',
        'smoke', 'fire', 'flame',
    }
    
    # 提示词违规正则模式
    PROHIBITED_PATTERNS = [
        r'\b(nsfw|explicit|18\+|xxx)\b',
        r'\b(kill yourself|suicide|self-harm)\b',
        r'\b(hitler|nazi|terrorism)\b',
    ]
    
    def __init__(self):
        self.enabled = True
        # 阿里云内容安全 API (可选)
        self.aliyun_enabled = bool(settings.ALIYUN_ACCESS_KEY_ID)
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则模式"""
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.PROHIBITED_PATTERNS
        ]
    
    def check_text(self, text: str) -> ModerationResult:
        """
        审核文本内容
        
        Args:
            text: 待审核文本
            
        Returns:
            ModerationResult: 审核结果
        """
        text_lower = text.lower()
        flagged_terms = []
        score = 0.0
        
        # 1. 检查禁止词
        for term in self.PROHIBITED_TERMS:
            if term in text_lower:
                flagged_terms.append(term)
                score += 0.3
        
        # 2. 检查警告词
        for term in self.WARNING_TERMS:
            if term in text_lower:
                flagged_terms.append(term)
                score += 0.15
        
        # 3. 检查正则模式
        for pattern in self._compiled_patterns:
            match = pattern.search(text)
            if match:
                flagged_terms.append(match.group())
                score += 0.4
        
        # 4. 限制分数
        score = min(score, 1.0)
        
        # 5. 判断级别
        if score >= 0.6 or any(term in self.PROHIBITED_TERMS for term in flagged_terms):
            return ModerationResult(
                level=ModerationLevel.BLOCK,
                reason="内容包含违规信息，请修改后重试",
                flagged_terms=flagged_terms,
                score=score
            )
        elif score >= 0.2 or any(term in self.WARNING_TERMS for term in flagged_terms):
            return ModerationResult(
                level=ModerationLevel.WARNING,
                reason="内容可能包含敏感信息，请注意",
                flagged_terms=flagged_terms,
                score=score
            )
        else:
            return ModerationResult(
                level=ModerationLevel.SAFE,
                reason=None,
                flagged_terms=[],
                score=score
            )
    
    def check_prompt(self, prompt: str, negative_prompt: Optional[str] = None) -> ModerationResult:
        """
        审核视频生成提示词
        
        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            
        Returns:
            ModerationResult: 审核结果
        """
        # 合并检查
        combined_text = prompt
        if negative_prompt:
            combined_text += " " + negative_prompt
        
        result = self.check_text(combined_text)
        
        # 如果负向提示词单独有严重问题，给出警告
        if negative_prompt:
            neg_result = self.check_text(negative_prompt)
            if neg_result.level == ModerationLevel.BLOCK and result.level != ModerationLevel.BLOCK:
                return ModerationResult(
                    level=ModerationLevel.WARNING,
                    reason="负向提示词可能包含敏感信息",
                    flagged_terms=neg_result.flagged_terms,
                    score=max(result.score, neg_result.score * 0.5)
                )
        
        return result
    
    async def check_image_url(self, image_url: str) -> ModerationResult:
        """
        审核图片URL (预留接口)
        
        Args:
            image_url: 图片URL
            
        Returns:
            ModerationResult: 审核结果
        """
        # TODO: 实现图片审核
        # 可以使用阿里云内容安全 API 审核图片
        if self.aliyun_enabled:
            pass  # 调用阿里云 API
        
        # 默认通过
        return ModerationResult(
            level=ModerationLevel.SAFE,
            reason=None,
            flagged_terms=[],
            score=0.0
        )


# 全局单例
content_moderation_service = ContentModerationService()
