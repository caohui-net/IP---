#!/bin/bash

# 进度监控脚本
echo "=== IP地址规划项目 Phase 2/4 执行监控 ==="
echo "启动时间: $(date)"
echo ""

# 检查输出目录
OUTPUT_DIR="/home/caohui/projects/IP地址规划/交付成果_20260904"

check_files() {
  echo "📊 检查成果文件..."

  # 成果#2: 现网事实基线表
  if [ -f "$OUTPUT_DIR/01_现网事实基线表.xlsx" ]; then
    echo "✓ 成果#2 (现网事实基线表): $(wc -l < "$OUTPUT_DIR/01_现网事实基线表.xlsx") 行"
  else
    echo "⏳ 成果#2: 生成中..."
  fi

  # 成果#3: 现网问题清单
  if [ -f "$OUTPUT_DIR/02_现网问题清单_P0_P1_P2.md" ]; then
    echo "✓ 成果#3 (现网问题清单): $(wc -l < "$OUTPUT_DIR/02_现网问题清单_P0_P1_P2.md") 行"
  else
    echo "⏳ 成果#3: 生成中..."
  fi

  # 成果#4: IPAM源数据表
  if [ -f "$OUTPUT_DIR/04_IPAM源数据表.csv" ]; then
    echo "✓ 成果#4 (IPAM源表): $(wc -l < "$OUTPUT_DIR/04_IPAM源数据表.csv") 行"
  elif [ -f "$OUTPUT_DIR/04_IPAM源数据表.xlsx" ]; then
    echo "✓ 成果#4 (IPAM源表): Excel文件已生成"
  else
    echo "⏳ 成果#4: 等待ipam-builder数据..."
  fi

  echo ""
}

# 主循环
for i in {1..10}; do
  check_files
  if [ $i -lt 10 ]; then
    echo "下次检查: $(date) + 30秒"
    sleep 30
    echo ""
  fi
done

echo "监控结束: $(date)"
