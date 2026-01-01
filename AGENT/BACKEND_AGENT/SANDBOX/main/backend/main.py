import uvicorn
import os
import sys

# 将当前目录添加到 python path，确保能找到 src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("Starting backend server...")
    # 在开发模式下运行
    uvicorn.run(
        "src.controller.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
