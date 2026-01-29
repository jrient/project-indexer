"""
Heuristic inference for directory purposes.

This module provides automatic detection of directory purposes based on:
- Directory name patterns
- File content patterns
- README.md parsing
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

# Directory name to purpose mapping
DIRECTORY_PURPOSES = {
    # Source directories
    "src": "Source code and core application logic.",
    "source": "Source code and core application logic.",
    "lib": "Library code and shared modules.",
    "pkg": "Package definitions and modules.",
    "internal": "Internal packages (not exported).",

    # Component directories
    "components": "UI components and reusable elements.",
    "views": "View/page components.",
    "pages": "Page-level components or routes.",
    "layouts": "Layout templates and wrappers.",
    "widgets": "Widget components.",

    # Backend directories
    "api": "API endpoint definitions and handlers.",
    "routes": "Route definitions and controllers.",
    "controllers": "Request controllers and handlers.",
    "handlers": "Request/event handlers.",
    "services": "Business logic and service layer.",
    "middleware": "Middleware functions.",

    # Data directories
    "models": "Data models and schemas.",
    "entities": "Entity definitions.",
    "schemas": "Schema definitions.",
    "types": "Type definitions.",
    "interfaces": "Interface definitions.",
    "dto": "Data transfer objects.",

    # Utility directories
    "utils": "Utility functions and helpers.",
    "helpers": "Helper functions.",
    "common": "Common/shared code.",
    "shared": "Shared resources across modules.",
    "core": "Core functionality.",
    "parsers": "Language parsers and code analyzers.",
    "validators": "Input validation and sanitization.",

    # Configuration
    "config": "Configuration files and settings.",
    "settings": "Application settings.",
    "constants": "Constant definitions.",

    # Testing
    "tests": "Unit and integration tests.",
    "test": "Test files.",
    "__tests__": "Jest/React test files.",
    "spec": "Test specifications.",
    "e2e": "End-to-end tests.",
    "fixtures": "Test fixtures and mock data.",
    "mocks": "Mock implementations.",

    # Documentation
    "docs": "Documentation files.",
    "documentation": "Project documentation.",

    # Assets
    "assets": "Static assets (images, fonts, etc.).",
    "static": "Static files served directly.",
    "public": "Public assets accessible from web.",
    "images": "Image files.",
    "icons": "Icon files.",
    "fonts": "Font files.",
    "styles": "Stylesheets (CSS/SCSS).",
    "css": "CSS stylesheets.",

    # Build/Scripts
    "scripts": "Build and utility scripts.",
    "tools": "Development tools.",
    "bin": "Binary/executable scripts.",
    "build": "Build output directory.",
    "dist": "Distribution files.",
    "out": "Output files.",

    # Hooks and state
    "hooks": "Custom hooks (React/Vue).",
    "store": "State management (Redux/Vuex).",
    "stores": "State stores.",
    "state": "State management.",
    "context": "React context providers.",
    "providers": "Provider components.",

    # Infrastructure
    "infra": "Infrastructure code.",
    "deploy": "Deployment configurations.",
    "k8s": "Kubernetes configurations.",
    "docker": "Docker configurations.",
    "terraform": "Terraform configurations.",

    # Database
    "migrations": "Database migrations.",
    "seeds": "Database seed data.",
    "db": "Database related code.",
    "database": "Database configurations.",
    "repositories": "Data repositories.",

    # Localization
    "i18n": "Internationalization files.",
    "locales": "Locale/translation files.",
    "translations": "Translation files.",
}


def infer_directory_purpose(
    rel_path: str,
    filenames: Optional[list[str]] = None,
    root_dir: Optional[Path] = None,
) -> str:
    """
    Infer the purpose of a directory based on its name and contents.

    Args:
        rel_path: Relative path of the directory
        filenames: List of files in the directory (optional)
        root_dir: Project root for reading README (optional)

    Returns:
        Description of the directory's purpose
    """
    if not rel_path:
        return "Project root directory."

    # Get the directory name
    path_parts = rel_path.replace("\\", "/").split("/")
    dir_name = path_parts[-1].lower()

    # Try to read README.md for description
    if root_dir:
        readme_path = root_dir / rel_path / "README.md"
        if readme_path.exists():
            purpose = _extract_readme_purpose(readme_path)
            if purpose:
                return purpose

    # Look up in predefined purposes
    if dir_name in DIRECTORY_PURPOSES:
        return DIRECTORY_PURPOSES[dir_name]

    # Try partial matches
    for pattern, purpose in DIRECTORY_PURPOSES.items():
        if pattern in dir_name or dir_name in pattern:
            return purpose

    # Infer from file patterns
    if filenames:
        purpose = _infer_from_files(filenames)
        if purpose:
            return purpose

    # Default
    return "Project files and modules."


def _extract_readme_purpose(readme_path: Path) -> Optional[str]:
    """Extract purpose from README.md first paragraph."""
    try:
        content = readme_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.strip().split("\n")

        # Skip title lines (starting with #)
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("!"):
                # Return first meaningful paragraph (truncated)
                if len(line) > 100:
                    return line[:97] + "..."
                return line

    except (IOError, UnicodeDecodeError):
        pass

    return None


def _infer_from_files(filenames: list[str]) -> Optional[str]:
    """Infer directory purpose from file patterns."""
    extensions = [Path(f).suffix.lower() for f in filenames]
    names_lower = [f.lower() for f in filenames]

    # Test files
    if any("test" in n or "spec" in n for n in names_lower):
        return "Test files."

    # Configuration files
    config_patterns = ["config", "settings", ".env", ".yaml", ".yml", ".json", ".toml"]
    if any(any(p in n for p in config_patterns) for n in names_lower):
        if all(any(p in n for p in config_patterns) for n in names_lower[:3]):
            return "Configuration files."

    # Component files (React/Vue)
    if ".tsx" in extensions or ".jsx" in extensions or ".vue" in extensions:
        return "UI components."

    # Style files
    if all(ext in [".css", ".scss", ".sass", ".less"] for ext in extensions if ext):
        return "Stylesheets."

    # Type definition files
    if all(ext == ".d.ts" or "type" in n for ext, n in zip(extensions, names_lower)):
        return "Type definitions."

    return None
