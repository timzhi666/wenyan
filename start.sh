#!/bin/bash
# 文言文实词测试 - 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
PYTHON="/Users/zhifangzhu/.workbuddy/binaries/python/envs/wenyan/bin/python"
PORT=5001

echo "=================================="
echo "  文言文实词测试 - 启动中..."
echo "=================================="

# 检查Python环境
if [ ! -f "$PYTHON" ]; then
    echo "错误：Python环境未找到，请先运行安装步骤"
    exit 1
fi

# 停止已有进程
pkill -f "python.*app.py" 2>/dev/null

# 进入后端目录
cd "$BACKEND_DIR"

# 初始化数据（如果数据库不存在）
if [ ! -f "wenyan.db" ]; then
    echo "正在初始化数据库..."
    "$PYTHON" init_data.py
fi

# 启动服务器
echo "正在启动服务器 http://localhost:$PORT ..."
"$PYTHON" app.py &
SERVER_PID=$!

sleep 2

echo ""
echo "✅ 服务器已启动！"
echo "📖 请在浏览器中打开: http://localhost:$PORT"
echo ""
echo "按 Ctrl+C 停止服务器"

# 等待服务器
wait $SERVER_PID
