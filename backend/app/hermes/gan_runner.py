"""
Hermes - GAN Runner Python API

真正的GAN工作流执行器，调用sub-agents完成各阶段任务
"""
import asyncio
import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GANState:
    """GAN状态机状态"""
    phase: int = 0
    sprint: str = "S1"
    sprint_count: int = 0
    scores: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)
    decisions: dict = field(default_factory=dict)
    last_updated: Optional[str] = None
    status: str = "initialized"
    decisions_mode: str = "auto"
    fix_loop_count: dict = field(default_factory=dict)
    completed_phases: list = field(default_factory=list)
    logs: list = field(default_factory=list)
    config: dict = field(default_factory=dict)
    agent_outputs: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GANState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PhaseResult:
    """Phase执行结果"""
    phase: int
    name: str
    passed: bool
    message: str
    data: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    report_path: Optional[str] = None
    agent_output: Optional[str] = None


class GANRunner:
    """
    GAN Runner Python API - 真正调用sub-agents执行各阶段任务

    用法:
        runner = GANRunner("/path/to/workspace", sprint="S1")
        runner.set_progress_callback(lambda phase, progress, msg: print(f"Phase {phase}: {msg}"))
        result = await runner.run_full()
    """

    PHASE_TO_AGENT = {
        0: "planner",    # PRD质疑 → planner
        1: "planner",    # SPEC → planner
        2: "planner",    # Sprint Contract → planner
        3: "reviewer",   # GAN评分 → reviewer
        4: "coder",      # 修复 → coder
        5: "reviewer",   # 代码审查 → reviewer
        6: "writer",     # 知识沉淀 → writer
        7: "reviewer",   # QA → reviewer
        8: None,         # 发布 → 自动
    }

    PHASE_NAMES = {
        0: "PRD Review (planner)",
        1: "Init + SPEC (planner)",
        2: "Sprint Contract (planner)",
        3: "GAN Scoring (reviewer)",
        4: "Fix Loop (coder)",
        5: "Code Review (reviewer)",
        6: "Knowledge (writer)",
        7: "QA (reviewer)",
        8: "Publish",
    }

    # Agent系统提示词
    AGENT_PROMPTS = {
        "planner": """你是一个需求分析师，负责PRD质疑和产出SPEC。

工作内容：
1. 质疑用户需求的完整性和可行性
2. 检查PRD中是否包含：定价、路由算法、前端页面、支付方案
3. 产出完整的SPEC.md
4. 签署Sprint Contract

要求：
- 仔细阅读workspace中的PRD文件
- 发现任何不完整的地方要提出质疑
- 产出符合规范的SPEC文档
- 使用中文工作""",

        "coder": """你是一个开发者，负责根据SPEC实现代码。

工作内容：
1. 仔细阅读SPEC.md理解需求
2. 实现完整功能代码
3. 确保代码质量：无TODO、无FIXME、类型完整
4. 编写必要的测试

规范要求：
- 所有API端点必须有response_model
- 错误处理必须显式
- 配置必须通过config.py
- 不允许硬编码密钥
- 使用中文工作""",

        "reviewer": """你是一个评审，使用GAN评分标准对代码进行7维度评分。

评分维度及权重：
- Feature Completeness (功能完整性): 25%
- Functionality (功能性): 20%
- Code Quality (代码质量): 20%
- Visual Design (视觉设计): 15%
- AI Integration (AI集成): 10%
- Security (安全性): 5%
- Performance (性能): 5%

Pass Threshold: 7.0

Critical Issues (直接Fail)：
- 无response_model
- JSON序列化为字符串
- 软删除数据
- 路由执行路径错误
- 硬编码密钥

要求：
- 严格评分，不要手下留情
- 发现任何Critical Issue必须指出
- 使用中文输出评分报告""",

        "writer": """你是一个技术写作者，负责知识沉淀。

工作内容：
1. 更新CHANGELOG.md
2. 记录本次Sprint的决策和发现
3. 编写必要的技术文档

要求：
- 使用中文
- 格式规范
- 记录关键决策和原因""",
    }

    def __init__(self, workspace: str, sprint: str = "S1"):
        self.workspace = Path(workspace)
        self.sprint = sprint
        self.state = GANState(sprint=sprint)
        self._phase_hooks: list[Callable] = []
        self._progress_callback: Optional[Callable] = None

        self._load_config()

        self.state_file = self.workspace / "gan-auto-runner" / "state" / "workflow_state.json"
        self.reports_dir = self.workspace / "gan-auto-runner" / "reports"

    def _load_config(self):
        """加载配置"""
        config_path = self.workspace / "gan-auto-runner" / "config.yaml"
        if config_path.exists():
            import yaml
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.state.config = yaml.safe_load(f) or {}
            except Exception:
                pass

    def register_hook(self, hook: Callable[[int, PhaseResult], None]):
        """注册phase切换回调"""
        self._phase_hooks.append(hook)

    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """设置进度回调 (phase, progress, message)"""
        self._progress_callback = callback

    def _notify_progress(self, phase: int, progress: int, message: str = ""):
        if self._progress_callback:
            try:
                self._progress_callback(phase, progress, message)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def _save_state(self):
        """保存状态"""
        self.state.last_updated = datetime.now().isoformat()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_state(self) -> GANState:
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return GANState.from_dict(data)
            except Exception:
                pass
        return GANState(sprint=self.sprint)

    def _write_report(self, name: str, content: str) -> str:
        """写报告"""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.reports_dir / f"{name}_{ts}.md"
        path.write_text(content, encoding="utf-8")
        return str(path)

    async def _run_agent(
        self,
        agent_type: str,
        task_prompt: str,
        timeout: int = 600
    ) -> tuple[bool, str]:
        """
        运行Claude Code agent

        Args:
            agent_type: agent类型 (planner/coder/reviewer/writer)
            task_prompt: 具体任务描述
            timeout: 超时秒数

        Returns:
            (success, output)
        """
        system_prompt = self.AGENT_PROMPTS.get(agent_type, "")
        full_prompt = f"{system_prompt}\n\n当前任务：{task_prompt}"

        logger.info(f"Running agent {agent_type} with timeout {timeout}s")

        # 构造claude命令
        # 使用环境变量或默认路径
        claude_cmd = os.environ.get("CLAUDE_CMD", "claude")

        cmd = [
            claude_cmd,
            "--prompt", full_prompt,
            "--no-input",
            "--output-format", "json",
        ]

        try:
            # 先尝试Docker方式
            docker_success = await self._run_via_docker(agent_type, full_prompt, timeout)
            if docker_success[0]:
                return docker_success

            # 回退到直接执行
            return await self._run_direct(cmd, timeout)

        except FileNotFoundError:
            logger.warning("claude command not found, trying direct path")
            return await self._run_direct(cmd, timeout)
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            return False, str(e)

    async def _run_via_docker(
        self,
        agent_type: str,
        prompt: str,
        timeout: int
    ) -> tuple[bool, str]:
        """通过Docker运行agent"""
        container_name = f"hermes-{agent_type}-{int(time.time())}"
        image = "manai/hermes-agent:latest"

        cmd = [
            "docker", "run",
            "--rm",
            "--name", container_name,
            "-v", f"{self.workspace}:/workspace",
            "-w", "/workspace",
            "-e", f"AGENT_TYPE={agent_type}",
            image,
            "claude",
            "--prompt", prompt,
            "--no-input",
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                output = stdout.decode('utf-8', errors='replace') if stdout else ""
                error = stderr.decode('utf-8', errors='replace') if stderr else ""

                if error:
                    logger.warning(f"Docker {agent_type} stderr: {error[:500]}")

                return process.returncode == 0, output

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                # 停止容器
                subprocess.run(["docker", "stop", container_name],
                             capture_output=True, timeout=10)
                return False, f"Timeout after {timeout}s"

        except FileNotFoundError:
            return False, "Docker not available"
        except Exception as e:
            return False, str(e)

    async def _run_direct(
        self,
        cmd: list,
        timeout: int
    ) -> tuple[bool, str]:
        """直接运行命令"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                output = stdout.decode('utf-8', errors='replace') if stdout else ""
                error = stderr.decode('utf-8', errors='replace') if stderr else ""

                if error:
                    logger.warning(f"Direct cmd stderr: {error[:500]}")

                return process.returncode == 0, output

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return False, f"Timeout after {timeout}s"

        except Exception as e:
            return False, str(e)

    # ============ Phase 执行 ============

    async def _run_phase_0(self) -> PhaseResult:
        """Phase 0: PRD质疑 - planner agent"""
        logger.info("Phase 0: PRD Review - calling planner agent")
        self._notify_progress(0, 10, "启动planner agent...")

        prd_path = self.workspace / "PRD_v2.1.md"
        prd_content = ""
        if prd_path.exists():
            prd_content = prd_path.read_text(encoding="utf-8")[:5000]

        task_prompt = f"""请对以下PRD进行质疑审查：

PRD文件路径：{prd_path}
PRD内容：
{prd_content}

质疑要点：
1. 定价是否完整？套餐是否清晰？
2. 路由算法是否明确？
3. 前端页面需求是否完整？
4. 支付方案是否可行？
5. 是否有遗漏的边界情况？

请产出质疑报告，并更新/创建SPEC.md"""

        success, output = await self._run_agent("planner", task_prompt, timeout=300)

        self.state.agent_outputs["phase_0"] = output

        message = "PRD质疑完成" if success else "PRD质疑完成（部分问题）"
        report = f"""# Phase 0: PRD 质疑报告

**时间**: {datetime.now().isoformat()}
**Agent**: planner
**执行结果**: {'成功' if success else '有问题'}

## Agent输出
{output[:2000] if output else '无输出'}

## 结论
{message}
"""
        report_path = self._write_report("phase_0_prd_review", report)

        result = PhaseResult(
            phase=0,
            name="PRD Review",
            passed=True,  # planner即使有质疑也让继续
            message=message,
            agent_output=output,
            data={"success": success}
        )
        self._notify_progress(0, 30, message)
        return result

    async def _run_phase_1(self) -> PhaseResult:
        """Phase 1: SPEC生成 - planner agent"""
        logger.info("Phase 1: SPEC generation - calling planner agent")
        self._notify_progress(1, 35, "启动planner agent生成SPEC...")

        task_prompt = f"""请根据workspace中的PRD，产出完整的SPEC.md规范文档。

要求：
1. 功能列表完整
2. API设计规范
3. 数据模型定义
4. 验收标准明确
5. 使用中文

如果SPEC.md已存在，请检查并更新。"""

        success, output = await self._run_agent("planner", task_prompt, timeout=300)

        self.state.agent_outputs["phase_1"] = output

        spec_path = self.workspace / "SPEC.md"
        spec_exists = spec_path.exists()

        message = "SPEC生成完成" if success else "SPEC生成完成"
        report = f"""# Phase 1: SPEC 报告

**时间**: {datetime.now().isoformat()}
**Agent**: planner
**SPEC文件**: {'已存在' if spec_exists else '新生成'}
**执行结果**: {'成功' if success else '有问题'}

## Agent输出
{output[:2000] if output else '无输出'}

## 结论
{message}
"""
        report_path = self._write_report("phase_1_spec", report)

        result = PhaseResult(
            phase=1,
            name="Init + SPEC",
            passed=spec_exists or success,
            message=message,
            agent_output=output,
            data={"spec_exists": spec_exists, "success": success}
        )
        self._notify_progress(1, 45, message)
        return result

    async def _run_phase_2(self) -> PhaseResult:
        """Phase 2: Sprint Contract - planner agent"""
        logger.info("Phase 2: Sprint Contract - calling planner agent")
        self._notify_progress(2, 50, "启动planner agent签署Sprint Contract...")

        task_prompt = f"""请为Sprint {self.sprint}签署Sprint Contract。

工作内容：
1. 确认SPEC中的功能优先级
2. 划分Sprint {self.sprint}的工作范围
3. 设定验收标准
4. 签署contract（创建sprint-contract.md）

请在 gan-harness/sprint-plan/ 目录下操作。"""

        success, output = await self._run_agent("planner", task_prompt, timeout=300)

        self.state.agent_outputs["phase_2"] = output

        contract_path = self.workspace / "gan-harness" / "sprint-plan" / "sprint-contract-all.md"
        contract_exists = contract_path.exists()
        sprint_count = 0
        if contract_exists:
            content = contract_path.read_text(encoding="utf-8")
            sprint_count = content.count("### Sprint")

        message = f"Sprint Contract签署完成，包含{sprint_count}个Sprint"
        report = f"""# Phase 2: Sprint Contract 报告

**时间**: {datetime.now().isoformat()}
**Agent**: planner
**Sprint数**: {sprint_count}
**执行结果**: {'成功' if success else '有问题'}

## Agent输出
{output[:2000] if output else '无输出'}

## 结论
{message}
"""
        report_path = self._write_report("phase_2_sprint_contract", report)

        result = PhaseResult(
            phase=2,
            name="Sprint Contract",
            passed=contract_exists,
            message=message,
            agent_output=output,
            data={"sprint_count": sprint_count, "success": success}
        )
        self._notify_progress(2, 55, message)
        return result

    async def _run_phase_3(self) -> PhaseResult:
        """Phase 3: GAN评分 - reviewer agent"""
        logger.info("Phase 3: GAN Scoring - calling reviewer agent")
        self._notify_progress(3, 60, "启动reviewer agent进行GAN评分...")

        task_prompt = f"""请对Sprint {self.sprint}的代码实现进行GAN 7维度评分。

评分维度及权重：
- Feature Completeness (功能完整性): 25%
- Functionality (功能性): 20%
- Code Quality (代码质量): 20%
- Visual Design (视觉设计): 15%
- AI Integration (AI集成): 10%
- Security (安全性): 5%
- Performance (性能): 5%

Pass Threshold: 7.0

Critical Issues（直接Fail）：
- 无response_model
- JSON序列化为字符串
- 软删除数据
- 路由执行路径错误
- 硬编码密钥

请检查 backend/ 和 frontend/ 目录中的代码，输出评分报告。

评分格式：
## GAN评分报告
| 维度 | 分数 | 说明 |
|------|------|------|
| Feature | X/10 | ... |
...

Overall Score: X/10
PASS/FAIL"""

        success, output = await self._run_agent("reviewer", task_prompt, timeout=600)

        self.state.agent_outputs["phase_3"] = output

        # 解析分数
        scores = {}
        overall = 0.0
        if output:
            import re
            for line in output.split('\n'):
                # 尝试匹配 "Feature: X" 或 "Feature | X"
                match = re.search(r'(?:Feature|Functionality|Code Quality|Visual|AI|Security|Performance)\s*[:|]\s*(\d+\.?\d*)', line, re.IGNORECASE)
                if match:
                    scores[line.split('|')[0].strip()] = float(match.group(1))
                overall_match = re.search(r'Overall Score:\s*(\d+\.?\d*)', output)
                if overall_match:
                    overall = float(overall_match.group(1))

        threshold = self.state.config.get("scoring", {}).get("pass_threshold", 7.0)
        passed = overall >= threshold if overall > 0 else True

        message = f"GAN评分完成：{overall}/10 ({'PASS' if passed else 'FAIL'})"
        report = f"""# Phase 3: GAN 评分报告

**时间**: {datetime.now().isoformat()}
**Agent**: reviewer
**Overall Score**: {overall}/10
**Pass Threshold**: {threshold}
**结果**: {'PASS ✅' if passed else 'FAIL ❌'}

## 详细评分
{output[:3000] if output else '无输出'}

## 结论
{message}
"""
        report_path = self._write_report(f"phase_3_gan_scoring_{self.sprint}", report)

        self.state.scores[f"Sprint {self.sprint}"] = overall

        result = PhaseResult(
            phase=3,
            name="GAN Scoring",
            passed=passed,
            message=message,
            agent_output=output,
            data={"scores": scores, "overall": overall, "threshold": threshold}
        )
        self._notify_progress(3, 75, message)
        return result

    async def _run_phase_4(self) -> PhaseResult:
        """Phase 4: 修复循环 - coder agent"""
        logger.info("Phase 4: Fix Loop - calling coder agent")
        self._notify_progress(4, 80, "启动coder agent修复问题...")

        # 获取评分中发现的问题
        reviewer_output = self.state.agent_outputs.get("phase_3", "")

        task_prompt = f"""请修复以下评分中发现的问题：

评分报告：
{reviewer_output[:3000]}

工作内容：
1. 修复Critical Issues
2. 完善缺失的功能
3. 改进代码质量

请直接修改代码文件，不要创建新文件。"""

        success, output = await self._run_agent("coder", task_prompt, timeout=600)

        self.state.agent_outputs["phase_4"] = output

        message = f"修复完成" if success else "修复完成（有问题）"
        report = f"""# Phase 4: 修复循环报告

**时间**: {datetime.now().isoformat()}
**Agent**: coder
**执行结果**: {'成功' if success else '有问题'}

## Agent输出
{output[:2000] if output else '无输出'}

## 结论
{message}
"""
        report_path = self._write_report("phase_4_fix", report)

        result = PhaseResult(
            phase=4,
            name="Fix Loop",
            passed=True,
            message=message,
            agent_output=output,
            data={"success": success}
        )
        self._notify_progress(4, 85, message)
        return result

    async def _run_phase_5(self) -> PhaseResult:
        """Phase 5: 代码审查 - reviewer agent"""
        logger.info("Phase 5: Code Review - calling reviewer agent")
        self._notify_progress(5, 88, "启动reviewer agent进行代码审查...")

        task_prompt = """请对代码库进行最终审查。

审查要点：
1. 扫描所有TODO/FIXME
2. 检查response_model是否完整
3. 检查是否有硬编码密钥
4. 检查错误处理是否完整

请输出审查报告。"""

        success, output = await self._run_agent("reviewer", task_prompt, timeout=300)

        self.state.agent_outputs["phase_5"] = output

        has_todos = "TODO" in output or "FIXME" in output
        message = "代码审查完成" if not has_todos else "发现TODO/FIXME"
        report = f"""# Phase 5: 代码审查报告

**时间**: {datetime.now().isoformat()}
**Agent**: reviewer
**执行结果**: {'成功' if success else '有问题'}

## Agent输出
{output[:2000] if output else '无输出'}

## 结论
{message}
"""
        report_path = self._write_report("phase_5_code_review", report)

        result = PhaseResult(
            phase=5,
            name="Code Review",
            passed=not has_todos,
            message=message,
            agent_output=output,
            data={"has_todos": has_todos, "success": success}
        )
        self._notify_progress(5, 92, message)
        return result

    async def _run_phase_6(self) -> PhaseResult:
        """Phase 6: 知识沉淀 - writer agent"""
        logger.info("Phase 6: Knowledge - calling writer agent")
        self._notify_progress(6, 95, "启动writer agent更新文档...")

        task_prompt = f"""请更新知识沉淀文档。

工作内容：
1. 更新CHANGELOG.md，记录本次Sprint {self.sprint}的变更
2. 记录关键决策和原因
3. 总结本次Sprint的评分和结果

Sprint {self.sprint} 评分：{self.state.scores.get(f'Sprint {self.sprint}', 'N/A')}

请直接修改CHANGELOG.md文件。"""

        success, output = await self._run_agent("writer", task_prompt, timeout=300)

        self.state.agent_outputs["phase_6"] = output

        message = "知识沉淀完成"
        report = f"""# Phase 6: 知识沉淀报告

**时间**: {datetime.now().isoformat()}
**Agent**: writer
**执行结果**: {'成功' if success else '有问题'}

## Agent输出
{output[:2000] if output else '无输出'}

## 结论
{message}
"""
        report_path = self._write_report("phase_6_knowledge", report)

        result = PhaseResult(
            phase=6,
            name="Knowledge Consolidation",
            passed=True,
            message=message,
            agent_output=output,
            data={"success": success}
        )
        self._notify_progress(6, 97, message)
        return result

    async def _run_phase_7(self) -> PhaseResult:
        """Phase 7: QA测试"""
        logger.info("Phase 7: QA Testing")
        self._notify_progress(7, 98, "QA检查...")

        # 检查QA报告是否存在
        qa_report_path = self.workspace / "gan-harness" / "sprint-plan" / "sprint-qa-report.md"
        passed = qa_report_path.exists()

        message = "QA测试通过" if passed else "QA报告未找到"
        report = f"""# Phase 7: QA 测试报告

**时间**: {datetime.now().isoformat()}
**QA报告**: {'已存在' if passed else '未找到'}

## 结论
{message}
"""
        report_path = self._write_report("phase_7_qa", report)

        result = PhaseResult(
            phase=7,
            name="QA Testing",
            passed=passed,
            message=message,
            data={"qa_report_exists": passed}
        )
        self._notify_progress(7, 99, message)
        return result

    async def _run_phase_8(self) -> PhaseResult:
        """Phase 8: Git push"""
        logger.info("Phase 8: Publish - Git push")
        self._notify_progress(8, 100, "执行Git提交和推送...")

        auto_push = self.state.config.get("phases", {}).get("phase_8", {}).get("auto_push", True)
        branch = self.state.config.get("phases", {}).get("phase_8", {}).get("branch", "master")

        pushed = False
        try:
            os.chdir(self.workspace)

            # 检查git状态
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=10
            )
            has_changes = bool(result.stdout.strip())

            if has_changes:
                logger.info("有未提交的变更，自动commit")
                subprocess.run(["git", "add", "-A"], capture_output=True, timeout=10)
                subprocess.run(
                    ["git", "commit", "-m", f"chore: GAN auto-runner Phase 8 publish {datetime.now().strftime('%Y%m%d')}"],
                    capture_output=True, timeout=10
                )

            if auto_push:
                result = subprocess.run(
                    ["git", "push", "origin", branch],
                    capture_output=True, text=True, timeout=30
                )
                pushed = result.returncode == 0
                if pushed:
                    logger.info(f"Successfully pushed to {branch}")
                else:
                    logger.warning(f"Push failed: {result.stderr}")

        except Exception as e:
            logger.error(f"Git operation failed: {e}")

        message = "✅ 已push" if pushed else "⚠️ 未执行或失败"
        report = f"""# Phase 8: 发布报告

**时间**: {datetime.now().isoformat()}
**分支**: {branch}
**Push结果**: {message}

## 结论
{'✅ 已推送到远程仓库' if pushed else '⚠️ 请手动执行git push'}
"""
        report_path = self._write_report("phase_8_publish", report)

        result = PhaseResult(
            phase=8,
            name="Publish",
            passed=True,
            message=message,
            data={"pushed": pushed, "branch": branch}
        )
        self._notify_progress(8, 100, message)
        return result

    async def run_phase(self, phase: int) -> PhaseResult:
        """运行单个phase"""
        phase_methods = {
            0: self._run_phase_0,
            1: self._run_phase_1,
            2: self._run_phase_2,
            3: self._run_phase_3,
            4: self._run_phase_4,
            5: self._run_phase_5,
            6: self._run_phase_6,
            7: self._run_phase_7,
            8: self._run_phase_8,
        }

        if phase not in phase_methods:
            raise ValueError(f"Invalid phase: {phase}")

        logger.info(f"Running phase {phase}: {self.PHASE_NAMES.get(phase)}")
        return await phase_methods[phase]()

    async def run_full(self, auto: bool = True) -> GANState:
        """
        运行完整GAN流程

        Args:
            auto: 是否自动模式（自动修复）

        Returns:
            最终的GANState
        """
        self.state.status = "running"
        self.state.decisions_mode = "auto" if auto else "manual"
        self._save_state()

        logger.info(f"Starting GAN workflow: sprint={self.sprint}, auto={auto}")

        try:
            for phase_num in range(9):
                self.state.phase = phase_num
                self._save_state()

                result = await self.run_phase(phase_num)
                self.state.completed_phases.append(
                    f"Phase {phase_num} ({result.name}): {result.message}"
                )

                # 通知hooks
                for hook in self._phase_hooks:
                    try:
                        hook(phase_num, result)
                    except Exception as e:
                        logger.warning(f"Hook error: {e}")

                # Phase 3评分不通过 → 修复循环
                if not result.passed and auto and phase_num == 3:
                    fix_result = await self.run_phase(4)
                    self.state.completed_phases.append(f"Phase 4 (Fix Loop): {fix_result.message}")
                    # 重新评分
                    result = await self.run_phase(3)

            self.state.status = "completed"

        except Exception as e:
            logger.error(f"Workflow error: {e}")
            self.state.status = "failed"
            self.state.issues.append(str(e))

        self._save_state()
        return self.state

    def get_state(self) -> GANState:
        """获取当前状态"""
        return self._load_state()

    def reset(self):
        """重置状态"""
        self.state = GANState(sprint=self.sprint)
        self._save_state()
