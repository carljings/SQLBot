# Tools 目录

此目录包含开发和维护 SQLBot 时使用的各种工具脚本。

## 目录结构

```
tools/
├── dev-scripts/     # 开发和重启脚本
├── db-scripts/      # 数据库相关脚本（重置密码、备份等）
├── test-scripts/    # 测试脚本
└── README.md        # 本文件
```

## dev-scripts/

开发和调试脚本，用于启动、停止、重启开发环境。

| 脚本 | 说明 |
|------|------|
| `start-dev.bat` | Windows 批处理：启动开发环境（后端 + 前端） |
| `start-dev.ps1` | PowerShell：启动开发环境 |
| `stop-dev.ps1` | PowerShell：停止开发环境 |
| `restart-dev.bat` | Windows 批处理：重启开发环境 |
| `restart-dev.ps1` | PowerShell：重启开发环境 |
| `restart-backend.bat` | Windows 批处理：仅重启后端服务 |
| `quick-restart.bat` | Windows 批处理：快速重启 |

## db-scripts/

数据库管理脚本，用于重置管理员密码、数据库备份等。

| 脚本 | 说明 |
|------|------|
| `reset_admin_password.py` | 重置管理员密码（需要数据库连接） |
| `reset_admin_pwd.py` | 独立脚本：重置管理员密码 |
| `reset_password_standalone.py` | 独立脚本：重置密码（无需依赖） |
| `reset_pwd.py` | 简单密码重置脚本 |
| `reset_pwd_simple.py` | 最简单的密码重置脚本 |
| `en_backup.db` | 数据库备份文件 |

## test-scripts/

测试脚本，用于测试 API 和功能。

| 脚本 | 说明 |
|------|------|
| `test_dimension.py` | 测试维度值功能 |
| `test_dimension_api.py` | 测试维度值 API |
| `test_moonshot.py` | 测试 Moonshot AI 集成 |

## 使用方法

### 启动开发环境

**Windows (批处理)**:
```batch
tools\dev-scripts\start-dev.bat
```

**Windows (PowerShell)**:
```powershell
.\tools\dev-scripts\start-dev.ps1
```

### 重置管理员密码

```bash
cd tools/db-scripts
python reset_admin_pwd.py
```

### 运行测试

```bash
cd tools/test-scripts
python test_dimension.py
```

## 注意事项

- 这些脚本主要用于开发环境，生产环境请使用其他部署方式
- 运行数据库脚本前请确保已备份数据
- 部分脚本需要 Python 3.11+ 环境
