"""Version consistency check and release ZIP builder for NEOEX."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import tomllib
import zipfile

EXCLUDED_DIR_NAMES = {"__pycache__", ".venv", ".git", "dist", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_FILE_NAMES = {".DS_Store"}


def read_package_version(project_dir: Path) -> str:
    """Read __version__ from neoex/__init__.py without importing external deps."""
    init_file = project_dir / "neoex" / "__init__.py"
    tree = ast.parse(init_file.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__version__":
                    return str(ast.literal_eval(node.value))
    raise ValueError("Não foi possível encontrar __version__ em neoex/__init__.py.")


def short_version(version: str) -> str:
    """Convert semantic X.Y.0 to X.Y for release filenames and Colab titles."""
    parts = version.split(".")
    if len(parts) == 3 and parts[2] == "0":
        return f"{parts[0]}.{parts[1]}"
    return version


def validate_version_sync(project_dir: Path) -> str:
    """Verify that __init__.py, pyproject.toml, and run_colab.ipynb agree."""
    version = read_package_version(project_dir)
    short = short_version(version)
    errors: list[str] = []

    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.is_file():
        errors.append("pyproject.toml não encontrado.")
    else:
        pyproject_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        pyproject_version = pyproject_data.get("project", {}).get("version")
        if pyproject_version != version:
            errors.append(
                f"pyproject.toml tem version={pyproject_version!r}, esperado {version!r}."
            )

    notebook_path = project_dir / "run_colab.ipynb"
    if not notebook_path.is_file():
        errors.append("run_colab.ipynb não encontrado.")
    else:
        nb_text = notebook_path.read_text(encoding="utf-8")
        nb_data = json.loads(nb_text)
        expected_check = f"__version__ != '{version}'"
        if expected_check not in nb_text:
            errors.append(
                f"run_colab.ipynb não verifica {expected_check!r}."
            )
        title = nb_data.get("metadata", {}).get("title", "")
        if f"v{short}" not in title:
            errors.append(
                f"Título de run_colab.ipynb ({title!r}) não contém 'v{short}'."
            )

    if errors:
        raise ValueError("Inconsistências de versão encontradas:\n- " + "\n- ".join(errors))
    return version


def _should_include(path: Path, project_dir: Path) -> bool:
    rel = path.relative_to(project_dir)
    if any(part in EXCLUDED_DIR_NAMES for part in rel.parts):
        return False
    if path.name in EXCLUDED_FILE_NAMES or path.suffix in EXCLUDED_SUFFIXES:
        return False
    return True


def build_zip(project_dir: Path, output_dir: Path | None = None) -> Path:
    """Validate version metadata and package NEOEX into a clean release ZIP."""
    version = validate_version_sync(project_dir)
    short = short_version(version)
    target_dir = output_dir or (project_dir / "dist")
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir / f"NEOEX_v{short}.zip"

    files = sorted(
        path for path in project_dir.rglob("*")
        if path.is_file() and _should_include(path, project_dir)
    )
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            arcname = Path("NEOEX") / file_path.relative_to(project_dir)
            archive.write(file_path, arcname.as_posix())

    with zipfile.ZipFile(zip_path, "r") as archive:
        corrupted = archive.testzip()
        if corrupted is not None:
            raise RuntimeError(f"ZIP gerado está corrompido: {corrupted}")
        names = set(archive.namelist())
        if "NEOEX/app.py" not in names:
            raise RuntimeError("ZIP gerado não contém NEOEX/app.py.")

    return zip_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida versões e gera o ZIP do NEOEX.")
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--check-only", action="store_true", help="Apenas valida a sincronia de versão.")
    args = parser.parse_args(argv)

    project_dir = args.project_dir.resolve()
    version = validate_version_sync(project_dir)
    if args.check_only:
        print(f"Versão sincronizada: {version}")
        return 0
    zip_path = build_zip(project_dir, args.output_dir)
    print(f"Pacote gerado com sucesso: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
