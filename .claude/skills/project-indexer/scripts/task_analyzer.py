#!/usr/bin/env python3
"""
Task Analyzer and Dispatcher.

This module analyzes development tasks and:
1. Parses task descriptions to identify keywords
2. Searches the index to locate relevant files
3. Generates structured task packages for sub-agents
4. Provides context summaries without requiring full file reads

Usage:
    python task_analyzer.py --task "Add user authentication"
    python task_analyzer.py --task "Fix bug in payment" --detail
    python task_analyzer.py --locate "UserService"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils import MetaManager, infer_directory_purpose


@dataclass
class TaskContext:
    """Context package for a sub-task."""
    task_id: str
    description: str
    assigned_agent: str
    relevant_files: list[str]
    relevant_symbols: list[str]
    directory_context: str
    style_hints: list[str]
    dependencies: list[str]


@dataclass
class TaskPlan:
    """Complete task plan with sub-tasks."""
    original_task: str
    analysis_summary: str
    sub_tasks: list[TaskContext]
    execution_order: list[str]
    post_actions: list[str]


# Keyword to domain mapping for task classification
TASK_KEYWORDS = {
    "frontend": [
        "ui", "component", "style", "css", "button", "form", "page", "view",
        "modal", "dialog", "layout", "responsive", "animation", "theme",
        "react", "vue", "angular", "html", "jsx", "tsx", "frontend",
    ],
    "backend": [
        "api", "endpoint", "controller", "service", "model", "database", "db",
        "query", "migration", "schema", "rest", "graphql", "auth", "token",
        "session", "middleware", "route", "handler", "backend", "server",
    ],
    "data": [
        "data", "pandas", "numpy", "analysis", "ml", "model", "train",
        "predict", "dataset", "feature", "pipeline", "etl", "transform",
    ],
    "testing": [
        "test", "spec", "mock", "fixture", "coverage", "assert", "expect",
        "e2e", "integration", "unit", "pytest", "jest", "vitest",
    ],
    "devops": [
        "deploy", "ci", "cd", "docker", "kubernetes", "k8s", "pipeline",
        "build", "release", "config", "env", "infrastructure",
    ],
    "security": [
        "security", "auth", "permission", "role", "encrypt", "hash",
        "vulnerability", "xss", "csrf", "injection", "sanitize",
    ],
}


def classify_task(task_description: str) -> list[str]:
    """
    Classify a task into domains based on keywords.

    Args:
        task_description: Natural language task description

    Returns:
        List of relevant domains
    """
    task_lower = task_description.lower()
    domains = []

    for domain, keywords in TASK_KEYWORDS.items():
        if any(kw in task_lower for kw in keywords):
            domains.append(domain)

    return domains if domains else ["general"]


def extract_search_terms(task_description: str) -> list[str]:
    """
    Extract potential search terms from task description.

    Args:
        task_description: Natural language task description

    Returns:
        List of search terms
    """
    # Remove common words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "to", "of",
        "in", "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "and", "or", "but", "if", "then", "else", "when", "where", "why", "how",
        "all", "each", "every", "both", "few", "more", "most", "other", "some",
        "such", "no", "not", "only", "own", "same", "so", "than", "too", "very",
        "add", "create", "make", "update", "modify", "change", "fix", "implement",
        "remove", "delete", "get", "set", "new", "old", "please", "want", "need",
    }

    # Extract words
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', task_description)

    # Filter and deduplicate
    terms = []
    seen = set()
    for word in words:
        lower = word.lower()
        if lower not in stop_words and lower not in seen and len(word) > 2:
            terms.append(word)
            seen.add(lower)

    # Also look for CamelCase or snake_case patterns (likely class/function names)
    camel_case = re.findall(r'\b[A-Z][a-zA-Z0-9]+\b', task_description)
    snake_case = re.findall(r'\b[a-z]+_[a-z_]+\b', task_description)

    for term in camel_case + snake_case:
        if term not in seen:
            terms.insert(0, term)  # Prioritize these
            seen.add(term.lower())

    return terms[:10]  # Limit to 10 most relevant


def locate_relevant_files(
    index_dir: Path,
    search_terms: list[str],
    limit: int = 20,
) -> list[tuple[str, str, str]]:
    """
    Search the index for files relevant to the task.

    Args:
        index_dir: Path to project-index directory
        search_terms: Terms to search for
        limit: Maximum results

    Returns:
        List of (file_path, symbol, context) tuples
    """
    meta = MetaManager(index_dir)
    all_results = []
    seen_files = set()

    for term in search_terms:
        results = meta.search(term, limit=limit // len(search_terms) + 1)
        for path, symbol, context in results:
            if path not in seen_files:
                all_results.append((path, symbol, context))
                seen_files.add(path)

    return all_results[:limit]


def get_agent_for_domain(domain: str) -> str:
    """Map domain to recommended agent type."""
    domain_to_agent = {
        "frontend": "tailwind-frontend-expert",
        "backend": "python-expert",
        "data": "ml-data-expert",
        "testing": "Python Testing Expert",
        "devops": "Python DevOps/CI-CD Expert",
        "security": "Python Security Expert",
        "general": "general-purpose",
    }
    return domain_to_agent.get(domain, "general-purpose")


def analyze_task(
    task_description: str,
    index_dir: Path,
    detail: bool = False,
) -> TaskPlan:
    """
    Analyze a task and generate an execution plan.

    Args:
        task_description: Natural language task description
        index_dir: Path to project-index directory
        detail: Include detailed context

    Returns:
        TaskPlan with sub-tasks
    """
    # Classify task
    domains = classify_task(task_description)

    # Extract search terms
    search_terms = extract_search_terms(task_description)

    # Locate relevant files
    relevant_files = locate_relevant_files(index_dir, search_terms)

    # Group files by domain/directory
    file_groups = {}
    for path, symbol, context in relevant_files:
        # Infer domain from path
        path_lower = path.lower()
        assigned_domain = "general"
        for domain in domains:
            domain_indicators = TASK_KEYWORDS.get(domain, [])
            if any(ind in path_lower for ind in domain_indicators):
                assigned_domain = domain
                break

        if assigned_domain not in file_groups:
            file_groups[assigned_domain] = []
        file_groups[assigned_domain].append((path, symbol, context))

    # Generate sub-tasks
    sub_tasks = []
    for i, (domain, files) in enumerate(file_groups.items(), 1):
        task_context = TaskContext(
            task_id=f"task_{i}",
            description=f"{domain.title()} changes for: {task_description}",
            assigned_agent=get_agent_for_domain(domain),
            relevant_files=[f[0] for f in files],
            relevant_symbols=[f[1] for f in files],
            directory_context=infer_directory_purpose(
                str(Path(files[0][0]).parent) if files else "",
                []
            ),
            style_hints=[],
            dependencies=[],
        )
        sub_tasks.append(task_context)

    # Determine execution order
    execution_order = [t.task_id for t in sub_tasks]

    # Standard post-actions
    post_actions = [
        "python scripts/index_project.py --update",
        "Run relevant tests",
        "Review changes",
    ]

    # Analysis summary
    summary_lines = [
        f"Task domains: {', '.join(domains)}",
        f"Search terms: {', '.join(search_terms[:5])}",
        f"Relevant files found: {len(relevant_files)}",
        f"Sub-tasks generated: {len(sub_tasks)}",
    ]

    return TaskPlan(
        original_task=task_description,
        analysis_summary="\n".join(summary_lines),
        sub_tasks=sub_tasks,
        execution_order=execution_order,
        post_actions=post_actions,
    )


def format_task_plan(plan: TaskPlan, format: str = "text") -> str:
    """Format task plan for output."""
    if format == "json":
        return json.dumps(asdict(plan), indent=2, ensure_ascii=False)

    lines = []
    lines.append("=" * 60)
    lines.append("TASK ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Original Task: {plan.original_task}")
    lines.append("")
    lines.append("Analysis Summary:")
    for line in plan.analysis_summary.split("\n"):
        lines.append(f"  {line}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("SUB-TASKS")
    lines.append("-" * 60)

    for task in plan.sub_tasks:
        lines.append("")
        lines.append(f"[{task.task_id}] {task.description}")
        lines.append(f"  Agent: {task.assigned_agent}")
        lines.append(f"  Files ({len(task.relevant_files)}):")
        for f in task.relevant_files[:5]:
            lines.append(f"    - {Path(f).name}")
        if len(task.relevant_files) > 5:
            lines.append(f"    ... and {len(task.relevant_files) - 5} more")
        lines.append(f"  Symbols: {', '.join(task.relevant_symbols[:3])}")

    lines.append("")
    lines.append("-" * 60)
    lines.append("EXECUTION ORDER")
    lines.append("-" * 60)
    for i, task_id in enumerate(plan.execution_order, 1):
        lines.append(f"  {i}. {task_id}")

    lines.append("")
    lines.append("-" * 60)
    lines.append("POST-ACTIONS (Required)")
    lines.append("-" * 60)
    for action in plan.post_actions:
        lines.append(f"  - {action}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def generate_dispatch_prompt(task: TaskContext) -> str:
    """
    Generate a prompt for dispatching a task to a sub-agent.

    Args:
        task: TaskContext to dispatch

    Returns:
        Formatted prompt string
    """
    lines = []
    lines.append(f"## Task: {task.description}")
    lines.append("")
    lines.append("### Context")
    lines.append(f"- Directory Purpose: {task.directory_context}")
    lines.append("")
    lines.append("### Files to Modify")
    for f in task.relevant_files:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("### Relevant Symbols")
    for s in task.relevant_symbols:
        lines.append(f"- `{s}`")
    lines.append("")
    lines.append("### Instructions")
    lines.append("1. Read the specified files")
    lines.append("2. Implement the required changes")
    lines.append("3. Maintain existing code style")
    lines.append("4. Add tests if applicable")
    lines.append("")
    lines.append("### After Completion")
    lines.append("Run: `python scripts/index_project.py --update`")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze tasks and generate execution plans",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--task", "-t",
        help="Task description to analyze",
        required=False,
    )
    parser.add_argument(
        "--locate", "-l",
        help="Locate files related to a symbol/keyword",
    )
    parser.add_argument(
        "--index-dir", "-i",
        default="project-index",
        help="Path to project-index directory",
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Include detailed context",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--dispatch",
        action="store_true",
        help="Generate dispatch prompts for each sub-task",
    )

    args = parser.parse_args()

    index_dir = Path(args.index_dir)
    if not index_dir.exists():
        print(f"Error: Index not found at {index_dir}")
        print("Run: python scripts/index_project.py first")
        sys.exit(1)

    if args.locate:
        meta = MetaManager(index_dir)
        results = meta.search(args.locate)
        if not results:
            print(f"No results for: {args.locate}")
        else:
            print(f"Found {len(results)} matches for '{args.locate}':\n")
            for path, symbol, context in results:
                print(f"  {Path(path).name}")
                print(f"    -> {context}")
                print()
        return

    if args.task:
        plan = analyze_task(args.task, index_dir, detail=args.detail)
        format_type = "json" if args.json else "text"
        print(format_task_plan(plan, format_type))

        if args.dispatch:
            print("\n" + "=" * 60)
            print("DISPATCH PROMPTS")
            print("=" * 60)
            for task in plan.sub_tasks:
                print(f"\n### For {task.assigned_agent}:")
                print(generate_dispatch_prompt(task))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
