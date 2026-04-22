"""
Hermes - Agent Executor

使用Docker容器启动和管理sub-agents
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class AgentConfig:
    """Agent配置"""
    def __init__(
        self,
        name: str,
        prompt: str,
        model: str = "claude-opus-4-6",
        timeout: int = 300,
        docker_image: str = "manai/hermes-agent:latest"
    ):
        self.name = name
        self.prompt = prompt
        self.model = model
        self.timeout = timeout
        self.docker_image = docker_image


# Agent定义
AGENT_CONFIGS = {
    "planner": AgentConfig(
        name="planner",
        prompt="你是一个需求分析师，负责PRD质疑和产出spec。分析用户需求的完整性和可行性。",
        model="claude-opus-4-6",
        timeout=300,
    ),
    "coder": AgentConfig(
        name="coder",
        prompt="你是一个开发者，按照spec实现代码。确保代码完整、可运行、符合规范。",
        model="claude-sonnet-4-6",
        timeout=1800,
    ),
    "reviewer": AgentConfig(
        name="reviewer",
        prompt="你是一个评审，使用GAN评分标准对代码进行7维度评分。评分标准：Feature 25%, Functionality 20%, Code Quality 20%, Visual 15%, AI Integration 10%, Security 5%, Performance 5%。",
        model="claude-opus-4-6",
        timeout=600,
    ),
    "writer": AgentConfig(
        name="writer",
        prompt="你是一个技术写作者，负责知识沉淀。更新CHANGELOG、编写技术文档。",
        model="claude-haiku-4-5",
        timeout=300,
    ),
}


class DockerAgentExecutor:
    """
    Docker容器化Agent执行器

    每个sub-agent运行在独立Docker容器中
    """

    def __init__(self, workspace: str):
        self.workspace = workspace
        self._running_containers: dict[str, asyncio.subprocess.Process] = {}

    async def execute_agent(
        self,
        agent_type: str,
        command: str,
        on_output: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """
        执行Agent

        Args:
            agent_type: Agent类型 (planner/coder/reviewer/writer)
            command: 要执行的指令
            on_output: 输出回调
            on_error: 错误回调

        Returns:
            {"success": bool, "output": str, "error": str}
        """
        if agent_type not in AGENT_CONFIGS:
            return {"success": False, "output": "", "error": f"Unknown agent type: {agent_type}"}

        config = AGENT_CONFIGS[agent_type]
        container_name = f"hermes-{agent_type}-{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting agent {agent_type} in container {container_name}")

        try:
            # 构建claude CLI命令
            cmd = [
                "docker", "run",
                "--rm",
                "--name", container_name,
                "-v", f"{self.workspace}:/workspace",
                "-w", "/workspace",
                "-e", f"AGENT_TYPE={agent_type}",
                "-e", f"CLAUDE_MODEL={config.model}",
                config.docker_image,
                "claude",
                "--prompt", f"{config.prompt}\n\n用户指令: {command}",
                "--output-format", "json",
            ]

            # 启动容器
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self._running_containers[container_name] = process

            # 收集输出
            output_lines = []
            error_lines = []

            # 读取stdout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=config.timeout
                )

                if stdout:
                    output = stdout.decode('utf-8', errors='replace')
                    output_lines.append(output)
                    if on_output:
                        on_output(output)

                if stderr:
                    error_lines.append(stderr.decode('utf-8', errors='replace'))

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                error_msg = f"Agent {agent_type} timed out after {config.timeout}s"
                logger.error(error_msg)
                if on_error:
                    on_error(error_msg)
                return {"success": False, "output": "\n".join(output_lines), "error": error_msg}

            # 清理容器引用
            self._running_containers.pop(container_name, None)

            success = process.returncode == 0
            result = {
                "success": success,
                "output": "\n".join(output_lines),
                "error": "\n".join(error_lines) if error_lines else None,
                "returncode": process.returncode,
            }

            logger.info(f"Agent {agent_type} completed with returncode {process.returncode}")
            return result

        except FileNotFoundError:
            error_msg = "Docker not found. Please install Docker."
            logger.error(error_msg)
            # Docker不可用时，回退到直接执行
            return await self._execute_fallback(agent_type, command, on_output, on_error)

        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            logger.error(error_msg)
            if on_error:
                on_error(error_msg)
            return {"success": False, "output": "", "error": error_msg}

    async def _execute_fallback(
        self,
        agent_type: str,
        command: str,
        on_output: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """
        Docker不可用时的回退执行

        直接使用claude CLI（需要本地安装）
        """
        logger.warning(f"Docker unavailable, using fallback execution for {agent_type}")

        if agent_type not in AGENT_CONFIGS:
            return {"success": False, "output": "", "error": f"Unknown agent type: {agent_type}"}

        config = AGENT_CONFIGS[agent_type]

        try:
            cmd = [
                "claude",
                "--prompt", f"{config.prompt}\n\n用户指令: {command}",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=config.timeout
                )

                output = stdout.decode('utf-8', errors='replace') if stdout else ""
                error = stderr.decode('utf-8', errors='replace') if stderr else None

                if on_output and output:
                    on_output(output)
                if on_error and error:
                    on_error(error)

                return {
                    "success": process.returncode == 0,
                    "output": output,
                    "error": error,
                    "returncode": process.returncode,
                }

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                error_msg = f"Agent {agent_type} timed out"
                if on_error:
                    on_error(error_msg)
                return {"success": False, "output": "", "error": error_msg}

        except Exception as e:
            error_msg = f"Fallback execution failed: {str(e)}"
            logger.error(error_msg)
            if on_error:
                on_error(error_msg)
            return {"success": False, "output": "", "error": error_msg}

    async def stop_agent(self, container_name: str):
        """停止运行中的容器"""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "stop", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            self._running_containers.pop(container_name, None)
            logger.info(f"Stopped container {container_name}")
        except Exception as e:
            logger.error(f"Failed to stop container {container_name}: {e}")

    async def stop_all(self):
        """停止所有运行中的容器"""
        for container_name in list(self._running_containers.keys()):
            await self.stop_agent(container_name)


# 全局执行器实例
_executor: Optional[DockerAgentExecutor] = None


def get_executor(workspace: str = None) -> DockerAgentExecutor:
    """获取全局执行器实例"""
    global _executor
    if _executor is None:
        if workspace is None:
            # 默认使用项目根目录
            from pathlib import Path
            workspace = str(Path(__file__).parent.parent.parent.parent)
        _executor = DockerAgentExecutor(workspace)
    return _executor
