set shell := ["bash", "-uc"]

# 格式化代码（自动修复）
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# 静态检查（不修改文件，仅检查）
lint:
    @echo "👉 正在运行 Ruff Check..."
    uv run ruff check .
    @echo "👉 正在运行 Ruff Format Check..."
    uv run ruff format --check .
    @echo "👉 正在运行 Mypy 类型检查..."
    uv run mypy src

# 运行测试
test:
    @echo "👉 正在运行 Pytest 测试与覆盖率..."
    uv run pytest

# 🚀 一键全量检查：执行你要求的所有检查（不改动代码）
check: lint test
    @echo "✅ 所有检查全部通过！可以安全提交。"