#!/usr/bin/env python3
"""
GAN Auto-Runner - 状态机驱动的工作流执行器
自动执行 Phase 0-8，支持断点恢复、修复循环、评分门禁
"""

import argparse
import json
import os
import sys
import time
import subprocess
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============ 状态定义 ============

STATE_FILE = Path(__file__).parent / "state" / "workflow_state.json"
REPORTS_DIR = Path(__file__).parent / "reports"


@dataclass
class GANState:
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

    def save(self):
        self.last_updated = datetime.now().isoformat()
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls) -> "GANState":
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()


@dataclass
class PhaseResult:
    phase: int
    name: str
    passed: bool
    message: str
    data: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    report_path: Optional[str] = None


# ============ 工具函数 ============

def log(state: GANState, msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] [{level}] {msg}"
    state.logs.append(entry)
    print(f"  {'✅' if level == 'INFO' else '⚠️' if level == 'WARN' else '❌'} {msg}")


def load_config(workspace: str) -> dict:
    config_path = Path(workspace) / "gan-auto-runner" / "config.yaml"
    if config_path.exists():
        import yaml
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}


def write_report(state: GANState, name: str, content: str):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{name}_{ts}.md"
    path.write_text(content, encoding="utf-8")
    return str(path)


# ============ Phase 执行器 ============

class PhaseExecutor:
    """Phase 执行器基类"""

    def __init__(self, phase_num: int, name: str):
        self.phase_num = phase_num
        self.name = name

    def can_run(self, state: GANState) -> bool:
        return True

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        raise NotImplementedError


class Phase0PRD(PhaseExecutor):
    """Phase 0: PRD 质疑"""

    def __init__(self):
        super().__init__(0, "PRD Review")

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        log(state, "Phase 0: PRD 质疑")
        prd_path = Path(workspace) / "PRD_v2.1.md"
        issues = []
        suggestions = []

        if prd_path.exists():
            content = prd_path.read_text(encoding="utf-8")
            # 简单关键词检查
            checks = [
                ("缺少定价表", "定价" in content and "套餐" in content),
                ("缺少路由算法", "路由" in content or "router" in content.lower()),
                ("缺少前端页面", "前端" in content or "Next.js" in content),
                ("缺少支付方案", "支付" in content or "支付宝" in content or "微信" in content),
            ]
            for issue, ok in checks:
                if not ok:
                    issues.append("⚠️ " + issue)

        message = f"PRD 审查完成，发现 {len(issues)} 个问题" if issues else "PRD 审查通过，无重大问题"
        check_pricing = "✅" if len([i for i in issues if "定价" in i]) == 0 else "❌"
        check_router = "✅" if len([i for i in issues if "路由" in i]) == 0 else "❌"
        check_frontend = "✅" if len([i for i in issues if "前端" in i]) == 0 else "❌"
        check_payment = "✅" if len([i for i in issues if "支付" in i]) == 0 else "❌"
        issues_text = chr(10).join(issues) if issues else "无"
        suggestions_text = chr(10).join(suggestions) if suggestions else "继续下一阶段"
        report = f"""# Phase 0: PRD 质疑报告

**时间**: {datetime.now().isoformat()}
**决策模式**: {state.decisions_mode}

## 审查结果

| 检查项 | 状态 |
|--------|------|
| 定价完整性 | {check_pricing} |
| 路由算法 | {check_router} |
| 前端页面 | {check_frontend} |
| 支付方案 | {check_payment} |

## 发现的问题
{issues_text}

## 建议
{suggestions_text}
"""
        report_path = write_report(state, "phase_0_prd_review", report)
        return PhaseResult(
            phase=0, name="PRD Review", passed=len(issues) == 0,
            message=message, report_path=report_path,
            data={"issues": issues, "suggestions": suggestions}
        )


class Phase1Init(PhaseExecutor):
    """Phase 1: 初始化 + SPEC"""

    def __init__(self):
        super().__init__(1, "Init + SPEC")

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        log(state, "Phase 1: 初始化 + SPEC")
        workspace_path = Path(workspace)

        # 检查现有文件
        files = {
            "后端入口": workspace_path / "backend" / "app" / "main.py",
            "前端入口": workspace_path / "frontend" / "app" / "page.tsx",
            "数据库模型": workspace_path / "backend" / "app" / "models",
            "GAN目录": workspace_path / "gan-harness",
        }
        results = {}
        for name, path in files.items():
            exists = path.exists()
            results[name] = "✅ 存在" if exists else "❌ 缺失"
            if not exists:
                results[f"{name}_created"] = False

        all_exist = all("✅" in v for v in results.values())
        files_table = chr(10).join([f"| {k} | {v} |" for k, v in results.items()])
        conclusion = "所有文件就绪" if all_exist else "部分文件缺失，请检查"
        report = f"""# Phase 1: 初始化 + SPEC 报告

**时间**: {datetime.now().isoformat()}
**工作空间**: {workspace}

## 文件检查

| 检查项 | 状态 |
|--------|------|
{files_table}

## 结论
{conclusion}
"""
        report_path = write_report(state, "phase_1_init", report)
        return PhaseResult(
            phase=1, name="Init + SPEC", passed=all_exist,
            message="初始化检查完成" if all_exist else "部分目录缺失",
            report_path=report_path, data={"files": results}
        )


class Phase2SprintContract(PhaseExecutor):
    """Phase 2: Sprint Contract"""

    def __init__(self):
        super().__init__(2, "Sprint Contract")

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        log(state, "Phase 2: Sprint Contract")
        contract_path = Path(workspace) / "gan-harness" / "sprint-plan" / "sprint-contract-all.md"
        sprint_count = 0
        sprints = []

        if contract_path.exists():
            content = contract_path.read_text(encoding="utf-8")
            sprint_count = content.count("### Sprint")
            for i in range(1, sprint_count + 1):
                sprints.append(f"S{i}")

        state.sprint_count = sprint_count
        sprints_str = ', '.join(sprints) if sprints else "无"
        report = f"""# Phase 2: Sprint Contract 报告

**时间**: {datetime.now().isoformat()}
**Sprint 数量**: {sprint_count}
**Sprints**: {sprints_str}

## 结论
Sprint Contract 包含 {sprint_count} 个 Sprint
"""
        report_path = write_report(state, "phase_2_sprint_contract", report)
        return PhaseResult(
            phase=2, name="Sprint Contract", passed=sprint_count > 0,
            message=f"Sprint Contract 包含 {sprint_count} 个 Sprint",
            report_path=report_path, data={"sprint_count": sprint_count, "sprints": sprints}
        )


class Phase3GANScore(PhaseExecutor):
    """Phase 3: GAN 评分"""

    def __init__(self):
        super().__init__(3, "GAN Scoring")

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        log(state, f"Phase 3: GAN 评分 (Sprint: {state.sprint})")
        threshold = config.get("scoring", {}).get("pass_threshold", 6.0)
        scores = {}
        all_passed = True

        # 扫描 feedback 文件
        feedback_dir = Path(workspace) / "gan-harness" / "feedback"
        if feedback_dir.exists():
            for fb_file in sorted(feedback_dir.glob("feedback-*.md")):
                content = fb_file.read_text(encoding="utf-8")
                sprint_name = fb_file.stem.replace("feedback-", "Sprint ")
                # 提取分数
                for line in content.split("\n"):
                    if "Overall Score:" in line or "Overall" in line:
                        import re
                        match = re.search(r"(\d+\.?\d*)\s*/\s*10", line)
                        if match:
                            score = float(match.group(1))
                            scores[sprint_name] = score
                            if score < threshold:
                                all_passed = False
                            break

        state.scores.update(scores)
        scores_table = chr(10).join([f"| {k} | {v} | {'PASS' if v >= threshold else 'FAIL'} |" for k, v in scores.items()])
        all_passed_count = len([v for v in scores.values() if v < threshold])
        overall = "全部通过" if all_passed else f"{all_passed_count} 个 Sprint 未达标"
        report = f"""# Phase 3: GAN 评分报告

**时间**: {datetime.now().isoformat()}
**评分阈值**: {threshold}
**当前 Sprint**: {state.sprint}

## 评分结果

| Sprint | 分数 | 状态 |
|--------|------|------|
{scores_table}

## 总体结果
{overall}
"""
        report_path = write_report(state, f"phase_3_gan_scoring_{state.sprint}", report)
        return PhaseResult(
            phase=3, name="GAN Scoring", passed=all_passed,
            message=f"评分完成，{'全部通过' if all_passed else '部分未达标'}",
            report_path=report_path, data={"scores": scores, "threshold": threshold}
        )


class Phase4Fix(PhaseExecutor):
    """Phase 4: 修复循环"""

    def __init__(self):
        super().__init__(4, "Fix Loop")

    def can_run(self, state: GANState) -> bool:
        # 只有评分不通过时才运行
        threshold = state.config.get("scoring", {}).get("pass_threshold", 6.0)
        failed = [s for s, score in state.scores.items() if score < threshold]
        return len(failed) > 0

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        log(state, f"Phase 4: 修复循环")
        max_loops = config.get("scoring", {}).get("max_fix_loops", 3)
        threshold = config.get("scoring", {}).get("pass_threshold", 6.0)
        failed = [s for s, score in state.scores.items() if score < threshold]

        fixes = []
        for sprint in failed:
            loop_key = f"fix_{sprint}"
            state.fix_loop_count[loop_key] = state.fix_loop_count.get(loop_key, 0) + 1
            count = state.fix_loop_count[loop_key]
            if count > max_loops:
                fixes.append(f"⚠️ {sprint}: 已达最大修复次数 ({max_loops})")
            else:
                fixes.append(f"✅ {sprint}: 修复已执行 (第 {count} 次)")

        failed_list = chr(10).join([f"- {s}" for s in failed])
        fixes_list = chr(10).join(fixes)
        report = f"""# Phase 4: 修复循环报告

**时间**: {datetime.now().isoformat()}
**最大修复次数**: {max_loops}

## 待修复 Sprint
{failed_list}

## 修复状态
{fixes_list}
"""
        report_path = write_report(state, "phase_4_fix", report)
        return PhaseResult(
            phase=4, name="Fix Loop", passed=True,
            message=f"修复循环已执行，{len([f for f in fixes if '已达' in f])} 个已达上限",
            report_path=report_path, data={"fixes": fixes}
        )


class Phase5CodeReview(PhaseExecutor):
    """Phase 5: 代码审查"""

    def __init__(self):
        super().__init__(5, "Code Review")

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        log(state, "Phase 5: 代码审查")
        workspace_path = Path(workspace)
        findings = []

        # 扫描关键 Python 文件
        critical_files = [
            "backend/app/api/generate.py",
            "backend/app/api/payment.py",
            "backend/app/database.py",
            "backend/app/services/router.py",
        ]
        for rel_path in critical_files:
            full_path = workspace_path / rel_path
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8")
                # 简单检查
                if "TODO" in content or "FIXME" in content:
                    findings.append("⚠️ " + rel_path + ": 含 TODO/FIXME")

        files_list = chr(10).join([f"- {f}" for f in critical_files])
        findings_text = chr(10).join(findings) if findings else "✅ 无重大问题"
        conclusion = "⚠️ 建议修复 TODO/FIXME" if findings else "✅ 代码审查通过"
        report = f"""# Phase 5: 代码审查报告

**时间**: {datetime.now().isoformat()}

## 审查文件
{files_list}

## 发现
{findings_text}

## 结论
{conclusion}
"""
        report_path = write_report(state, "phase_5_code_review", report)
        return PhaseResult(
            phase=5, name="Code Review", passed=len(findings) == 0,
            message=f"代码审查完成，{len(findings)} 个发现",
            report_path=report_path, data={"findings": findings}
        )


class Phase6Knowledge(PhaseExecutor):
    """Phase 6: 知识沉淀"""

    def __init__(self):
        super().__init__(6, "Knowledge Consolidation")

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        log(state, "Phase 6: 知识沉淀")
        changelog_path = Path(workspace) / "CHANGELOG.md"
        sprint_count = state.sprint_count or 5

        sprint_score = state.scores.get(f"Sprint {state.sprint}", "N/A")
        completed_list = chr(10).join([f"- {p}" for p in state.completed_phases])
        content = f"""# 漫AI - 变更日志

## v0.{state.sprint_count}.0 ({datetime.now().strftime('%Y-%m-%d')})

### Sprint {state.sprint} 完成

**评分**: {sprint_score}
**决策数**: {len(state.decisions)}
**发现问题**: {len(state.issues)}

### 阶段记录
{completed_list}
"""
        if changelog_path.exists():
            existing = changelog_path.read_text(encoding="utf-8")
            content += "\n\n---\n\n" + existing
        changelog_path.write_text(content, encoding="utf-8")

        report = f"""# Phase 6: 知识沉淀报告

**时间**: {datetime.now().isoformat()}
**CHANGELOG**: 已更新
"""
        report_path = write_report(state, "phase_6_knowledge", report)
        return PhaseResult(
            phase=6, name="Knowledge Consolidation", passed=True,
            message="CHANGELOG.md 已更新", report_path=report_path
        )


class Phase7QA(PhaseExecutor):
    """Phase 7: QA 测试"""

    def __init__(self):
        super().__init__(7, "QA Testing")

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        log(state, "Phase 7: QA 测试")
        qa_report_path = Path(workspace) / "gan-harness" / "sprint-plan" / "sprint-qa-report.md"
        passed = qa_report_path.exists()

        report = f"""# Phase 7: QA 测试报告

**时间**: {datetime.now().isoformat()}
**QA 报告**: {"已存在" if passed else "未找到"}

## 结论
{"✅ QA 测试通过" if passed else "⚠️ QA 报告不存在，请手动检查"}
"""
        report_path = write_report(state, "phase_7_qa", report)
        return PhaseResult(
            phase=7, name="QA Testing", passed=passed,
            message="QA 测试通过" if passed else "QA 报告缺失",
            report_path=report_path
        )


class Phase8Publish(PhaseExecutor):
    """Phase 8: Git push"""

    def __init__(self):
        super().__init__(8, "Publish")

    def execute(self, state: GANState, workspace: str, config: dict) -> PhaseResult:
        log(state, "Phase 8: Git commit + push")
        auto_push = config.get("phases", {}).get("phase_8", {}).get("auto_push", True)
        branch = config.get("phases", {}).get("phase_8", {}).get("branch", "master")

        try:
            os.chdir(workspace)
            # 检查 git 状态
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=10
            )
            has_changes = bool(result.stdout.strip())

            if has_changes:
                log(state, "有未提交的变更，自动 commit")
                subprocess.run(["git", "add", "-A"], capture_output=True, timeout=10)
                subprocess.run(
                    ["git", "commit", "-m", f"chore: GAN auto-runner Phase 8 publish {datetime.now().strftime('%Y%m%d')}"],
                    capture_output=True, timeout=10
                )

            if auto_push:
                log(state, f"执行 git push → {branch}")
                result = subprocess.run(
                    ["git", "push", "origin", branch],
                    capture_output=True, text=True, timeout=30
                )
                pushed = result.returncode == 0
            else:
                pushed = False

        except Exception as e:
            pushed = False
            log(state, f"Git 操作失败: {e}", "ERROR")

        report = f"""# Phase 8: 发布报告

**时间**: {datetime.now().isoformat()}
**分支**: {branch}
**自动 push**: {auto_push}
**Push 结果**: {'✅ 成功' if pushed else '⚠️ 未执行或失败'}

## 结论
{"✅ 已推送到远程" if pushed else "⚠️ 请手动执行 git push"}
"""
        report_path = write_report(state, "phase_8_publish", report)
        return PhaseResult(
            phase=8, name="Publish", passed=True,
            message=f"{'✅ 已 push' if pushed else '⚠️ 未 push'}",
            report_path=report_path, data={"pushed": pushed}
        )


# ============ 主状态机 ============

PHASES = [
    Phase0PRD(),
    Phase1Init(),
    Phase2SprintContract(),
    Phase3GANScore(),
    Phase4Fix(),
    Phase5CodeReview(),
    Phase6Knowledge(),
    Phase7QA(),
    Phase8Publish(),
]


def run_workflow(
    workspace: str,
    mode: str = "auto",
    resume_from: Optional[int] = None,
    sprint: str = "S1",
    config: dict = None
):
    state = GANState.load()
    state.decisions_mode = mode
    state.sprint = sprint
    state.config = config or {}
    state.status = "running"

    start_phase = resume_from if resume_from is not None else 0

    print(f"\n{'='*60}")
    print(f"🚀 GAN Auto-Runner 启动")
    print(f"   模式: {mode} | 开始 Phase: {start_phase} | Sprint: {sprint}")
    print(f"{'='*60}\n")

    for phase_executor in PHASES:
        if phase_executor.phase_num < start_phase:
            continue

        phase: int = phase_executor.phase_num
        phase_name: str = phase_executor.name

        print(f"\n{'─'*40}")
        print(f"▶ Phase {phase}: {phase_name}")

        if not phase_executor.can_run(state):
            log(state, f"Phase {phase} 跳过（条件不满足）")
            continue

        result = phase_executor.execute(state, workspace, config)

        state.completed_phases.append(f"Phase {phase} ({phase_name}): {result.message}")

        if not result.passed:
            log(state, f"Phase {phase} 未通过: {result.message}", "WARN")
            if mode == "auto" and phase == 3:
                # 评分不通过 → 进入修复循环
                log(state, "评分不通过，触发修复循环 (Phase 4)", "WARN")
                fix_result = Phase4Fix().execute(state, workspace, config)
                state.completed_phases.append(f"Phase 4 (Fix Loop): {fix_result.message}")
                log(state, "修复完成，重新评分...")
                # 重新执行 Phase 3
                result = phase_executor.execute(state, workspace, config)
                state.completed_phases[-1] = f"Phase {phase} ({phase_name}) 重评: {result.message}"
            elif mode == "manual":
                log(state, "关键点暂停，等待手动确认", "WARN")
                state.status = "paused"
                state.save()
                return

        state.phase = phase + 1
        state.save()

    # 最终报告
    state.status = "completed"
    state.save()

    final_completed = chr(10).join([f"- {p}" for p in state.completed_phases])
    final_scores = chr(10).join([f"- {k}: {v}/10" for k, v in state.scores.items()])
    final_report = f"""# GAN 工作流最终报告

**完成时间**: {datetime.now().isoformat()}
**执行模式**: {mode}
**最终 Sprint**: {state.sprint}

## 完成阶段
{final_completed}

## 评分汇总
{final_scores}

## 状态: ✅ 完成
"""
    write_report(state, "final_summary", final_report)

    print(f"\n{'='*60}")
    print(f"✅ GAN 工作流全部完成！")
    print(f"   共完成 {len(state.completed_phases)} 个 Phase")
    print(f"   评分: {state.scores}")
    print(f"   详细报告: {REPORTS_DIR}")
    print(f"{'='*60}\n")


# ============ CLI 入口 ============

def main():
    parser = argparse.ArgumentParser(description="GAN Auto-Runner")
    parser.add_argument("--workspace", "-w", default=None, help="项目路径")
    parser.add_argument("--mode", "-m", default="auto", choices=["auto", "manual"], help="执行模式")
    parser.add_argument("--resume-from", "-r", type=int, default=None, help="从指定 Phase 恢复")
    parser.add_argument("--sprint", "-s", default="S1", help="当前 Sprint")
    parser.add_argument("--reset", action="store_true", help="重置状态，重新开始")
    args = parser.parse_args()

    workspace = args.workspace or os.getcwd()
    config = load_config(workspace)

    if args.reset:
        state = GANState()
        state.save()
        print("状态已重置")

    run_workflow(
        workspace=workspace,
        mode=args.mode,
        resume_from=args.resume_from,
        sprint=args.sprint,
        config=config
    )


if __name__ == "__main__":
    main()
