set shell := ["bash", "-uc"]

# 安装所有依赖（含 dev 和 docs）
install:
    uv sync --all-groups
    uv run pre-commit install

# 格式化 + 自动修复
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# 只检查，不修改
lint:
    uv run ruff format --check .
    uv run ruff check .
    uv run mypy src

# 跑测试（带覆盖率）
test:
    uv run pytest

# 快速检查：格式 → lint → 测试
check: fmt lint test

# 启动文档本地预览
docs:
    uv run mkdocs serve

# 构建静态文档
docs-build:
    uv run mkdocs build

# 清理缓存
clean:
    rm -rf .venv .pytest_cache .mypy_cache .ruff_cache site .coverage