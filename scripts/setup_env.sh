#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "======================================"
echo "多Agent软件工程系统 - 环境初始化"
echo "======================================"

# Check Python version
check_python_version() {
    echo ""
    echo "[1/6] 检查Python版本..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            echo "✓ Python版本: $PYTHON_VERSION (满足要求 >= 3.11)"
            return 0
        else
            echo "✗ Python版本: $PYTHON_VERSION (需要 >= 3.11)"
            return 1
        fi
    else
        echo "✗ Python3未安装"
        return 1
    fi
}

# Create virtual environment
create_venv() {
    echo ""
    echo "[2/6] 创建虚拟环境..."

    if [ -d "venv" ]; then
        echo "  虚拟环境已存在，跳过创建"
    else
        python3 -m venv venv
        echo "✓ 虚拟环境创建成功"
    fi
}

# Activate virtual environment
activate_venv() {
    echo ""
    echo "[3/6] 激活虚拟环境..."

    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✓ 虚拟环境已激活"
    else
        echo "✗ 虚拟环境激活失败"
        return 1
    fi
}

# Install dependencies
install_dependencies() {
    echo ""
    echo "[4/6] 安装依赖包..."

    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r requirements.txt
        echo "✓ 依赖安装完成"
    else
        echo "✗ requirements.txt不存在"
        return 1
    fi
}

# Install dev dependencies
install_dev_dependencies() {
    echo ""
    echo "[5/6] 安装开发依赖..."

    pip install pytest pytest-asyncio pytest-cov mypy ruff pre-commit
    echo "✓ 开发依赖安装完成"
}

# Verify installation
verify_installation() {
    echo ""
    echo "[6/6] 验证安装..."

    modules=("langgraph" "autogen_core" "pydantic" "yaml" "structlog" "pytest")

    for module in "${modules[@]}"; do
        if python -c "import $module" 2>/dev/null; then
            echo "  ✓ $module"
        else
            echo "  ✗ $module (未安装)"
        fi
    done

    echo "✓ 验证完成"
}

# Main execution
main() {
    if check_python_version; then
        create_venv
        activate_venv
        install_dependencies

        read -p "是否安装开发依赖? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_dev_dependencies
        fi

        verify_installation

        echo ""
        echo "======================================"
        echo "环境初始化完成！"
        echo "======================================"
        echo ""
        echo "使用以下命令激活环境："
        echo "  source venv/bin/activate"
        echo ""
        echo "运行测试："
        echo "  pytest"
        echo ""
    else
        echo ""
        echo "环境检查失败，请安装Python 3.11或更高版本"
        exit 1
    fi
}

main "$@"
