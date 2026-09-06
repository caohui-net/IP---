# 代码工具说明

**目录**: 文档归档/06_代码工具/  
**文件数**: 7个Python脚本  
**用途**: 项目自动化工具（生成基线、验证编码、冲突检查等）

---

## 📝 工具清单

### 1. baseline_generator.py (19KB)
**功能**: 基线生成器主程序  
**用途**: 从现网配置生成标准化基线表  
**输入**: 现网配置文件  
**输出**: 02_现网事实基线表.xlsx

### 2. config_parser.py (16KB)
**功能**: 配置解析器  
**用途**: 解析锐捷RGOS配置文件  
**输入**: 纯净配置.txt  
**输出**: 解析后的JSON结构

### 3. generate_baseline.py (较小)
**功能**: 基线生成脚本  
**用途**: 快速生成基线表的辅助脚本  
**输入**: 配置文件  
**输出**: CSV/Excel基线表

### 4. improve_baseline.py
**功能**: 基线改进工具  
**用途**: 优化和改进已生成的基线表  
**输入**: 初始基线表  
**输出**: 改进版基线表

### 5. validate_encoding.py
**功能**: 编码验证工具  
**用途**: 验证IP/VLAN编码是否符合编码规则  
**输入**: 目标设计表  
**输出**: 验证报告（符合/不符合）

### 6. check_conflicts_capacity.py (11KB)
**功能**: 冲突容量检查工具  
**用途**: 检查IP/VLAN冲突和容量充足性  
**输入**: 现网基线 + 目标设计  
**输出**: conflict_capacity_check.json

### 7. generate_target_design.py
**功能**: 目标设计生成器  
**用途**: 根据需求和编码规则生成目标设计  
**输入**: 需求、IPAM数据、编码规则  
**输出**: 05_目标设计表.xlsx

---

## 🔧 使用环境

**Python版本**: 3.14  
**依赖包**: pandas, openpyxl, xlrd  
**虚拟环境**: 原位于 `交付成果_20260904/venv/` (133MB)

### 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas openpyxl xlrd
```

---

## 📊 典型工作流

### 工作流1: 生成基线表

```bash
# 1. 解析现网配置
python3 config_parser.py --input 东校区核心_纯净配置.txt

# 2. 生成基线表
python3 baseline_generator.py

# 3. 改进基线表（可选）
python3 improve_baseline.py --input 02_现网事实基线表.xlsx
```

### 工作流2: 生成目标设计

```bash
# 1. 生成目标设计
python3 generate_target_design.py \
  --ipam 04_IPAM源数据表.csv \
  --baseline 02_现网事实基线表.xlsx

# 2. 验证编码
python3 validate_encoding.py --input 05_目标设计表.xlsx

# 3. 检查冲突
python3 check_conflicts_capacity.py \
  --baseline 02_现网事实基线表.xlsx \
  --target 05_目标设计表.xlsx
```

---

## ⚠️ 注意事项

### 1. 这些工具已完成任务

项目交付成果（01_交付成果/）中的所有表格**已由这些工具生成并人工审核通过**。

### 2. 生产环境不需要

- 这些工具用于**设计阶段**
- Phase 8/9部署**只需配置文档**（03_配置文档/）
- 生产环境不需要Python环境

### 3. 仅供参考

如需修改设计，可参考这些工具的逻辑：
- 编码规则实现
- 冲突检查算法
- 基线解析逻辑

---

## 📁 原始位置

**原始目录**: `交付成果_20260904/` (133MB)  
**状态**: 被 `.gitignore` 忽略（包含133MB的venv）  
**归档位置**: `文档归档/06_代码工具/` (仅Python脚本)

---

## ✅ 归档说明

**归档内容**: 仅Python脚本（7个，共约70KB）  
**未归档**: venv虚拟环境（133MB，可重新创建）  
**原因**: 虚拟环境过大，不适合Git管理

如需运行这些工具，重新创建venv即可。

---

**最后更新**: 2026-09-06  
**项目编号**: IP-PLAN-2026-09-04
