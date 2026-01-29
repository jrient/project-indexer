#!/usr/bin/env python3
"""
Agent Setup and CLAUDE.md Generator.

This module analyzes a project and:
1. Detects technology stack and languages used
2. Recommends appropriate sub-agents for the project
3. Generates or updates CLAUDE.md with team configuration
4. Provides integration with Claude Code's Task system

Usage:
    python setup_agent.py [project_path]         # Setup team for project
    python setup_agent.py --list-agents          # List all available agent types
    python setup_agent.py --recommend [project]  # Show recommended agents only
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from index_project import detect_project_type


# Agent definitions with their specializations
AGENT_DEFINITIONS = {
    # Python ecosystem
    "python-expert": {
        "name": "Python 开发专家",
        "tech": ["python", "fastapi", "flask", "django"],
        "description": "Expert Python developer specializing in modern Python 3.12+",
        "subagent_type": "python-expert",
        "capabilities": [
            "Python API development (FastAPI/Flask)",
            "Data processing and scripting",
            "Testing with pytest",
            "Type hints and modern Python patterns",
        ],
    },
    "django-expert": {
        "name": "Django 全栈专家",
        "tech": ["django"],
        "description": "Expert Django developer for full-stack web applications",
        "subagent_type": "django-expert",
        "capabilities": [
            "Django models and migrations",
            "DRF API development",
            "Django admin customization",
            "Celery task queues",
        ],
    },
    "fastapi-expert": {
        "name": "FastAPI 专家",
        "tech": ["fastapi"],
        "description": "Expert in high-performance async APIs with FastAPI",
        "subagent_type": "fastapi-expert",
        "capabilities": [
            "Async API design",
            "Pydantic V2 models",
            "Dependency injection",
            "OpenAPI documentation",
        ],
    },
    "ml-data-expert": {
        "name": "ML/数据科学专家",
        "tech": ["tensorflow", "pytorch", "pandas", "numpy", "scikit-learn"],
        "description": "Machine learning and data science expert",
        "subagent_type": "ml-data-expert",
        "capabilities": [
            "Data analysis with pandas/numpy",
            "ML model development",
            "Data visualization",
            "Feature engineering",
        ],
    },

    # Frontend ecosystem
    "frontend-expert": {
        "name": "前端开发专家",
        "tech": ["react", "vue", "angular", "next.js", "nuxt.js", "svelte", "typescript"],
        "description": "Frontend specialist for modern web applications",
        "subagent_type": "tailwind-frontend-expert",
        "capabilities": [
            "React/Vue/Angular components",
            "State management",
            "CSS/Tailwind styling",
            "Responsive design",
        ],
    },

    # Backend/Infrastructure
    "devops-expert": {
        "name": "DevOps/CI-CD 专家",
        "tech": ["docker", "kubernetes", "terraform", "github-actions"],
        "description": "DevOps and infrastructure automation specialist",
        "subagent_type": "Python DevOps/CI-CD Expert",
        "capabilities": [
            "Docker containerization",
            "CI/CD pipelines",
            "Infrastructure as code",
            "Cloud deployment",
        ],
    },

    # Go
    "go-expert": {
        "name": "Go 语言专家",
        "tech": ["go"],
        "description": "Go language expert for high-performance services",
        "subagent_type": "general-purpose",  # No specific Go agent, use general
        "capabilities": [
            "Concurrent programming",
            "gRPC services",
            "Error handling patterns",
            "Performance optimization",
        ],
    },

    # Testing
    "testing-expert": {
        "name": "测试专家",
        "tech": ["pytest", "jest", "vitest", "cypress"],
        "description": "Testing and QA automation specialist",
        "subagent_type": "Python Testing Expert",
        "capabilities": [
            "Unit and integration testing",
            "Test coverage optimization",
            "E2E testing",
            "TDD/BDD practices",
        ],
    },

    # Security
    "security-expert": {
        "name": "安全专家",
        "tech": [],  # Always recommend for any project
        "description": "Security analysis and secure coding specialist",
        "subagent_type": "Python Security Expert",
        "capabilities": [
            "Security vulnerability assessment",
            "Secure coding practices",
            "Authentication/authorization",
            "OWASP compliance",
        ],
    },
}


def get_recommended_agents(tech_stack: list[str], project_type: str) -> dict:
    """
    Get recommended agents based on detected technology stack.

    Args:
        tech_stack: List of detected technologies
        project_type: Detected project type

    Returns:
        Dict of recommended agent configs
    """
    recommended = {}
    stack_lower = {t.lower() for t in tech_stack}
    stack_lower.add(project_type.lower())

    for agent_id, config in AGENT_DEFINITIONS.items():
        # Check if any of the agent's tech matches the project
        agent_tech = {t.lower() for t in config["tech"]}

        if agent_tech & stack_lower:  # Intersection
            recommended[agent_id] = config
        elif not config["tech"] and len(tech_stack) > 0:
            # Always recommend agents with empty tech (like security)
            pass  # Don't auto-add, let user opt-in

    # Always add a coordinator/architect role
    recommended["architect"] = {
        "name": "架构师/协调员",
        "tech": [],
        "description": "Project architect and task coordinator",
        "subagent_type": "tech-lead-orchestrator",
        "capabilities": [
            "Task decomposition and planning",
            "Architecture decisions",
            "Code review coordination",
            "Cross-team communication",
        ],
    }

    return recommended


def generate_claude_md_content(
    project_name: str,
    project_type: str,
    tech_stack: list[str],
    agents: dict,
    index_path: str = "project-index",
) -> str:
    """Generate CLAUDE.md content for the project."""
    lines = []

    # Header
    lines.append(f"# Project Protocol: {project_name}")
    lines.append("")
    lines.append(f"> Auto-generated by Project Coordinator on {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")

    # Project Info
    lines.append("## Project Information")
    lines.append(f"- **Type**: {project_type}")
    lines.append(f"- **Tech Stack**: {', '.join(tech_stack) if tech_stack else 'Unknown'}")
    lines.append(f"- **Index Location**: `{index_path}/INDEX.md`")
    lines.append("")

    # AI Team Configuration
    lines.append("## AI Team Configuration")
    lines.append("")
    lines.append("主 AI (Coordinator) 负责规划和分发任务，以下 Sub-agents 负责具体实现：")
    lines.append("")

    for agent_id, config in agents.items():
        lines.append(f"### {config['name']} (`{agent_id}`)")
        lines.append(f"- **描述**: {config['description']}")
        lines.append(f"- **Agent Type**: `{config['subagent_type']}`")
        lines.append("- **职责**:")
        for cap in config.get("capabilities", [])[:3]:
            lines.append(f"  - {cap}")
        lines.append("")

    # Development Workflow
    lines.append("## Development Workflow")
    lines.append("")
    lines.append("### 1. 任务开始前")
    lines.append("- 阅读 `project-index/INDEX.md` 了解项目结构")
    lines.append("- 使用 `--search` 定位相关代码")
    lines.append("")
    lines.append("### 2. 代码修改后 (必须执行)")
    lines.append("```bash")
    lines.append("python scripts/index_project.py --update")
    lines.append("```")
    lines.append("")
    lines.append("### 3. 任务完成前")
    lines.append("- 确保索引已更新")
    lines.append("- 运行相关测试")
    lines.append("- 检查代码风格")
    lines.append("")

    # Coding Standards
    lines.append("## Coding Standards")
    lines.append("")

    if "python" in project_type.lower() or any("python" in t.lower() for t in tech_stack):
        lines.append("### Python")
        lines.append("- Follow PEP 8 style guide")
        lines.append("- Use type hints for all functions")
        lines.append("- Write docstrings (Google style)")
        lines.append("")

    if any(t.lower() in ["typescript", "react", "vue", "next.js"] for t in tech_stack):
        lines.append("### TypeScript/JavaScript")
        lines.append("- Use TypeScript for type safety")
        lines.append("- Follow ESLint/Prettier configuration")
        lines.append("- Prefer functional components")
        lines.append("")

    if "go" in project_type.lower():
        lines.append("### Go")
        lines.append("- Follow effective Go guidelines")
        lines.append("- Use gofmt for formatting")
        lines.append("- Handle all errors explicitly")
        lines.append("")

    return "\n".join(lines)


def setup_project_team(root_dir: Path, force: bool = False) -> dict:
    """
    Set up AI team configuration for a project.

    Args:
        root_dir: Project root directory
        force: Overwrite existing CLAUDE.md

    Returns:
        Dict with setup results
    """
    results = {
        "project_type": None,
        "tech_stack": [],
        "agents": {},
        "claude_md_created": False,
        "claude_md_updated": False,
    }

    # Detect project type
    project_type, tech_stack = detect_project_type(root_dir)
    results["project_type"] = project_type
    results["tech_stack"] = tech_stack

    print(f"Project: {root_dir.name}")
    print(f"Detected type: {project_type}")
    print(f"Tech stack: {', '.join(tech_stack) if tech_stack else 'Unknown'}")
    print()

    # Get recommended agents
    agents = get_recommended_agents(tech_stack, project_type)
    results["agents"] = agents

    print("Recommended AI Team:")
    for agent_id, config in agents.items():
        print(f"  - {config['name']} ({agent_id})")
        print(f"    subagent_type: {config['subagent_type']}")
    print()

    # Generate CLAUDE.md
    claude_file = root_dir / "CLAUDE.md"
    content = generate_claude_md_content(
        root_dir.name,
        project_type,
        tech_stack,
        agents,
    )

    if claude_file.exists() and not force:
        existing = claude_file.read_text(encoding="utf-8")

        if "AI Team Configuration" in existing:
            print(f"CLAUDE.md already contains team configuration.")
            print("Use --force to overwrite.")
            return results

        # Append to existing
        new_content = existing + "\n\n---\n\n" + content
        claude_file.write_text(new_content, encoding="utf-8")
        results["claude_md_updated"] = True
        print(f"Updated: {claude_file}")
    else:
        claude_file.write_text(content, encoding="utf-8")
        results["claude_md_created"] = True
        print(f"Created: {claude_file}")

    # Reminder to run indexer
    print()
    print("Next steps:")
    print("  1. Run: python scripts/index_project.py")
    print("  2. Review CLAUDE.md and customize as needed")
    print("  3. Start using the coordinator workflow")

    return results


def list_all_agents():
    """List all available agent types."""
    print("Available Agent Types:\n")
    for agent_id, config in AGENT_DEFINITIONS.items():
        print(f"  {agent_id}")
        print(f"    Name: {config['name']}")
        print(f"    Type: {config['subagent_type']}")
        print(f"    Tech: {', '.join(config['tech']) if config['tech'] else 'Any'}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Set up AI team configuration for a project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing CLAUDE.md team configuration",
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all available agent types",
    )
    parser.add_argument(
        "--recommend",
        action="store_true",
        help="Show recommended agents without creating CLAUDE.md",
    )

    args = parser.parse_args()

    if args.list_agents:
        list_all_agents()
        return

    root_dir = Path(args.project_path).resolve()

    if not root_dir.exists():
        print(f"Error: Directory not found: {root_dir}")
        sys.exit(1)

    if args.recommend:
        project_type, tech_stack = detect_project_type(root_dir)
        agents = get_recommended_agents(tech_stack, project_type)
        print(f"Project: {root_dir.name}")
        print(f"Tech stack: {', '.join(tech_stack) if tech_stack else 'Unknown'}")
        print("\nRecommended agents:")
        for agent_id, config in agents.items():
            print(f"  - {agent_id}: {config['subagent_type']}")
        return

    setup_project_team(root_dir, force=args.force)


if __name__ == "__main__":
    main()
