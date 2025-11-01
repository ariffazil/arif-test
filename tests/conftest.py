import importlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "platform"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ensure_platform_package() -> None:
    existing = sys.modules.get("platform")
    if existing and getattr(existing, "__file__", "").startswith(str(PACKAGE_ROOT)):
        return

    if existing:
        sys.modules.pop("platform", None)

    spec = importlib.util.spec_from_file_location(
        "platform",
        PACKAGE_ROOT / "__init__.py",
        submodule_search_locations=[str(PACKAGE_ROOT)],
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.__path__ = [str(PACKAGE_ROOT)]
        sys.modules["platform"] = module


_ensure_platform_package()
