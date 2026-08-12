"""使用 Cython 将 http_api_plugin 包内所有 .py 就地编译为 .pyd，并清理源文件。"""

import shutil
import sys
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, setup

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "http_api_plugin"
BUILD_DIR = ROOT / "build" / "pyd"


def make_module_name(rel: Path) -> str:
    """把相对 http_api_plugin 的文件路径转换为 Extension 名。

    __init__.py 的 Extension 名使用 pkg.__init__，这样 build_ext --inplace
    会把产物放回包目录中（如 http_api_plugin/__init__.cp311-win_amd64.pyd）。
    """
    parts = rel.with_suffix("").parts
    if parts[-1] == "__init__":
        parent = ".".join(parts[:-1])
        return "http_api_plugin" + ("." + parent if parent else "") + ".__init__"
    return "http_api_plugin." + ".".join(parts)


def discover() -> list[tuple[str, Path]]:
    modules = []
    for py in sorted(PKG.rglob("*.py")):
        rel = py.relative_to(PKG)
        modules.append((make_module_name(rel), py))
    return modules


def main() -> None:
    modules = discover()
    if not modules:
        print("未找到需要编译的 .py 文件", file=sys.stderr)
        raise SystemExit(1)

    extensions = [Extension(name, [str(path)]) for name, path in modules]
    print(f"待编译模块: {len(extensions)}")
    for name, _ in modules:
        print(f"  - {name}")

    # build_dir 让生成的 .c 落在 build/ 下，避免污染包目录
    ext_modules = cythonize(
        extensions,
        language_level=3,
        build_dir=str(BUILD_DIR),
        compiler_directives={"always_allow_keywords": True},
    )

    sys.argv = ["build_pyd.py", "build_ext", "--inplace"]
    setup(name="http_api_plugin", ext_modules=ext_modules)

    # 清理源文件与缓存
    for py in PKG.rglob("*.py"):
        py.unlink(missing_ok=True)
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    for cache in PKG.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)

    pyd_files = list(PKG.rglob("*.pyd"))
    print(f"编译完成，共生成 {len(pyd_files)} 个 .pyd 文件：")


if __name__ == "__main__":
    main()