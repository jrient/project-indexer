# scripts

> Build and utility scripts.

## Files

### index_project.py
**Path**: `scripts\index_project.py`
**Language**: Python

> Project Indexer - Generate hierarchical index for large codebases.

**Exports**:
- `def detect_project_type(root_dir) -> tuple[str, list[str]]`
- `def collect_files(root_dir, ignore_patterns) -> dict[str, list[Path]]`
- `def generate_directory_index(rel_dir, files, root_dir, high_density) -> tuple[str, list[str]]`
- `def write_chunked_index(content, output_dir, base_name) -> list[str]`
- `def generate_main_index(root_dir, index_dir, project_type, tech_stack, ignore_patterns, stats) -> None`
- `def search_index(index_dir, query) -> None`
- `def main()`

**Dependencies**: `__future__`, `argparse`, `collections`, `datetime`, `os`
  _(+5 more)_

---

### setup_agent.py
**Path**: `scripts\setup_agent.py`
**Language**: Python

> Agent Setup and CLAUDE.md Generator.

**Exports**:
- `def get_recommended_agents(tech_stack, project_type) -> dict`
- `def generate_claude_md_content(project_name, project_type, tech_stack, agents, index_path) -> str`
- `def setup_project_team(root_dir, force) -> dict`
- `def list_all_agents()`
- `def main()`

**Dependencies**: `__future__`, `argparse`, `datetime`, `index_project`, `pathlib`
  _(+2 more)_

---

### task_analyzer.py
**Path**: `scripts\task_analyzer.py`
**Language**: Python

> Task Analyzer and Dispatcher.

**Exports**:
- `@dataclass class TaskContext`
- `@dataclass class TaskPlan`
- `def classify_task(task_description) -> list[str]`
- `def extract_search_terms(task_description) -> list[str]`
- `def locate_relevant_files(index_dir, search_terms, limit) -> list[tuple[str, str, str]]`
- `def get_agent_for_domain(domain) -> str`
- `def analyze_task(task_description, index_dir, detail) -> TaskPlan`
- `def format_task_plan(plan, format) -> str`
- `def generate_dispatch_prompt(task) -> str`
- `def main()`

**Dependencies**: `__future__`, `argparse`, `dataclasses`, `json`, `pathlib`
  _(+4 more)_

---
