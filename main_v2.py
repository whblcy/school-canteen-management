"""
学校食堂食材管理系统 v2.0 - 重构版入口
原 main.py 已迁移至 school_canteen 包，采用分层架构
"""
import sys
from school_canteen.app import main

if __name__ == "__main__":
    sys.exit(main())
