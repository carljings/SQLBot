# SQLBot本地启动完整指南

## 📊 当前状态

| 组件 | 状态 |
|------|------|
| Docker Desktop | ✅ 已安装并运行 |
| PostgreSQL容器 | ✅ 已运行（sqlbot-pg） |
| uv（包管理器） | ✅ 已安装 |
| Python依赖 | ✅ 已同步到虚拟环境 |
| sqlbot_xpack | ⚠️ 配置问题（路径权限） |

---

## 🚀 解决方案

### 方案A：修改sqlbot_xpack配置（推荐，无需sudo）

sqlbot_xpack模块尝试创建`/opt/sqlbot/data/file`目录，但Mac上没有权限。

**解决方案**：修改sqlbot_xpack的源码，让它使用本地目录。

**步骤**：

1. **找到sqlbot_xpack的file_utils.py**
   ```bash
   find /Users/guchuan/codespace/SQLBot-ClaudeCode/backend/.venv -name "file_utils.py" | grep sqlbot_xpack
   ```

2. **修改文件（添加本地目录检查）**
   ```python
   # 在os.mkdir(self, mode)之前添加：
   if not os.path.exists(self.parent):
       # 使用本地目录
       import tempfile
       local_dir = tempfile.gettempdir()
       self.parent.mkdir(parents=True, exist_ok=True)
   ```

3. **启动SQLBot**
   ```bash
   cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend
   python3 main.py
   ```

---

### 方案B：创建系统目录（需要sudo）

**手动执行**：
```bash
cd /Users/guchuan/codespace/SQLBot-ClaudeCode
./create-sqlbot-dirs.sh
```

**脚本内容**：
```bash
#!/bin/bash
echo "创建/opt/sqlbot目录..."
sudo mkdir -p /opt/sqlbot/data/file
sudo mkdir -p /opt/sqlbot/data/excel
sudo mkdir -p /opt/sqlbot/images
sudo mkdir -p /opt/sqlbot/app/logs
sudo mkdir -p /opt/sqlbot/models
sudo mkdir -p /opt/sqlbot/scripts

echo "设置权限..."
sudo chown -R $USER:staff /opt/sqlbot
sudo chmod -R 755 /opt/sqlbot

echo "完成！"
```

---

### 方案C：使用环境变量覆盖（推荐）

**创建环境变量文件**：
```bash
cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend
cat > .env.local << 'EOF'
BASE_DIR=/Users/guchuan/codespace/SQLBot-ClaudeCode
SCRIPT_DIR=/Users/guchuan/codespace/SQLBot-ClaudeCode/scripts
UPLOAD_DIR=/Users/guchuan/codespace/SQLBot-ClaudeCode/data/file
MCP_IMAGE_PATH=/Users/guchuan/codespace/SQLBot-ClaudeCode/images
EXCEL_PATH=/Users/guchuan/codespace/SQLBot-ClaudeCode/data/excel
LOCAL_MODEL_PATH=/Users/guchuan/codespace/SQLBot-ClaudeCode/models
EOF
```

**启动SQLBot**：
```bash
cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend
source .env.local
python3 main.py
```

---

## 🎯 我的推荐

**方案C（环境变量覆盖）**最简单：

1. 运行以下命令：
   ```bash
   cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend
   cat > .env.local << 'EOF'
BASE_DIR=/Users/guchuan/codespace/SQLBot-ClaudeCode
SCRIPT_DIR=/Users/guchuan/codespace/SQLBot-ClaudeCode/scripts
UPLOAD_DIR=/Users/guchuan/codespace/SQLBot-ClaudeCode/data/file
MCP_IMAGE_PATH=/Users/guchuan/codespace/SQLBot-ClaudeCode/images
EXCEL_PATH=/Users/guchuan/codespace/SQLBot-ClaudeCode/data/excel
LOCAL_MODEL_PATH=/Users/guchuan/codespace/SQLBot-ClaudeCode/models
EOF
   ```

2. 启动SQLBot：
   ```bash
   python3 main.py
   ```

---

## 📞 下一步

**你想用哪个方案？**

- **方案A**：我帮你修改sqlbot_xpack源码
- **方案B**：你手动执行创建系统目录的脚本（需要sudo密码）
- **方案C**：我帮你创建环境变量文件（推荐）
