# 阿里云DDNS更新工具

一个高性能、可靠的阿里云DNS动态域名解析工具，能够自动检测公网IP变化并更新相应的DNS记录，适用于家庭宽带、云服务器等动态IP环境。

## 功能特性

- 📁 **灵活配置**：支持通过JSON配置文件或环境变量进行配置
- 🔄 **智能IP检测**：使用多个IP检测服务作为备用，提高可靠性
- 💾 **本地缓存优化**：保存当前IP记录，避免不必要的API调用
- 📝 **完善的日志系统**：详细记录运行状态和错误信息
- ⚡ **高效执行**：优化的代码结构，保证快速响应
- 🔒 **安全可靠**：完善的错误处理机制
- 🐍 **版本兼容**：支持Python 3.7+，特别优化了Python 3.12兼容性

## 环境要求

- Python 3.7 或更高版本
- 阿里云账号及访问密钥
- 可访问互联网的网络环境

## 安装指南

### 1. 克隆项目

```bash
git clone https://your-repo-url/ddns.git
cd ddns
```

### 2. 创建虚拟环境（推荐）

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/MacOS
# 或在Windows上：venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 配置详解

### 方法一：配置文件

复制配置示例文件：

```bash
cp config_example.json config.json
```

编辑`config.json`，填写必要信息：

```json
{
  "access_key_id": "your_access_key_id",
  "access_key_secret": "your_access_key_secret",
  "domain_name": "example.com",
  "rr": "@",
  "record_type": "A",
  "ttl": 600,
  "ip_file": "/tmp/ddns_current_ip.txt",
  "log_level": "INFO"
}
```

配置参数说明：

| 配置项 | 说明 | 默认值 | 是否必填 |
|-------|------|-------|----------|
| access_key_id | 阿里云访问密钥ID | - | ✓ 是 |
| access_key_secret | 阿里云访问密钥Secret | - | ✓ 是 |
| domain_name | 域名（如example.com） | - | ✓ 是 |
| rr | 主机记录（如@、www、blog等） | @ | 否 |
| record_type | 记录类型（通常为A记录） | A | 否 |
| ttl | 记录生存时间(秒) | 600 | 否 |
| ip_file | IP记录保存文件路径 | /tmp/ddns_current_ip.txt | 否 |
| log_level | 日志级别 | INFO | 否 |

### 方法二：环境变量

设置以下环境变量（环境变量优先级高于配置文件）：

```bash
# 必需环境变量
export ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
export DDNS_DOMAIN_NAME=example.com

# 可选环境变量
export DDNS_RR=@
export DDNS_RECORD_TYPE=A
export DDNS_TTL=600
export DDNS_LOG_LEVEL=INFO
```

## 使用方法

### 方式一：使用配置文件运行

```bash
# 激活虚拟环境（如果使用）
source venv/bin/activate

# 运行脚本
python src/ddns.py config.json
```

### 方式二：使用环境变量运行

```bash
# 设置环境变量
export ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
export DDNS_DOMAIN_NAME=example.com

# 运行脚本
python src/ddns.py
```

## 定时运行设置

### Linux/MacOS (使用crontab)

设置每5分钟运行一次：

```bash
# 编辑crontab
crontab -e

# 添加以下行（注意修改路径）
*/5 * * * * cd /path/to/ddns && source venv/bin/activate && python src/ddns.py config.json >> /var/log/ddns.log 2>&1
```

### Windows (使用任务计划程序)

1. 打开任务计划程序
2. 创建基本任务
3. 设置触发器为每5分钟运行一次
4. 操作选择启动程序
5. 程序/脚本设置为Python解释器路径
6. 添加参数：`src\ddns.py config.json`
7. 起始于：设置为项目根目录

## 日志说明

日志包含以下信息：

- 任务启动时间和基本信息
- 获取到的当前公网IP
- IP变化检测结果
- DNS记录更新状态
- 错误信息（如有）

日志级别可通过配置文件或环境变量设置，可选值：DEBUG、INFO、WARNING、ERROR。

## 故障排除

### 常见问题

1. **阿里云访问凭证无效**
   - 检查AccessKey ID和AccessKey Secret是否正确
   - 确保账号有DNS管理权限

2. **未找到域名记录**
   - 确保域名已在阿里云DNS中添加
   - 确保主机记录（RR）已存在对应的DNS记录

3. **IP检测失败**
   - 检查网络连接是否正常
   - 确保能访问外部IP检测服务

4. **Python版本兼容性问题**
   - 当前版本已移除异步功能以支持Python 3.12
   - 确保Python版本≥3.7

### 调试建议

- 将日志级别设置为DEBUG以获取更详细的信息
- 检查网络连接和防火墙设置
- 验证阿里云账号权限和DNS记录是否正确

## 安全提示

1. 请勿在代码或配置文件中硬编码敏感信息
2. 建议使用RAM子账号并限制权限范围
3. 定期更新访问密钥
4. 妥善保管访问凭证，避免泄露

## 示例输出

成功更新时的输出示例：

```
尝试从 https://api.ipify.org 获取IP...
成功获取IP: 192.0.2.1
2023-11-28 22:00:00,123 - INFO - 开始DDNS更新任务 - 域名: example.com, 主机记录: @
2023-11-28 22:00:00,124 - INFO - 获取到当前公网IP: 192.0.2.1
2023-11-28 22:00:00,567 - INFO - IP已变化，准备更新DNS记录 - 从 192.0.2.0 到 192.0.2.1
2023-11-28 22:00:01,234 - INFO - DNS记录更新成功 - @.example.com -> 192.0.2.1
```

IP未变化时的输出示例：

```
尝试从 https://api.ipify.org 获取IP...
成功获取IP: 192.0.2.1
2023-11-28 22:05:00,123 - INFO - 开始DDNS更新任务 - 域名: example.com, 主机记录: @
2023-11-28 22:05:00,124 - INFO - 获取到当前公网IP: 192.0.2.1
2023-11-28 22:05:00,125 - INFO - IP未变化（与本地记录相同），无需更新DNS记录 (192.0.2.1)
```

## 许可证

MIT License

## 更新日志

- v1.0: 初始版本，基础DDNS功能
- v1.1: 添加多IP服务支持和错误处理优化
- v1.2: 优化Python 3.12兼容性，移除异步功能
