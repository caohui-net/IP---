#!/bin/bash

# IP地址规划项目 - 自动化流程控制脚本
# 功能: 监控agents进度，自动触发下一阶段

PROJECT_DIR="/home/caohui/projects/IP地址规划"
OUTPUT_DIR="$PROJECT_DIR/交付成果_20260904"
LOCK_DIR="/tmp/ip-planning-locks"

mkdir -p "$LOCK_DIR"

# 日志函数
log_event() {
    local msg="$1"
    local ts=$(date '+%H:%M:%S')
    echo "[$ts] $msg" >> "$OUTPUT_DIR/流程控制日志.txt"
    echo "[$ts] $msg"
}

# 检查文件是否存在且大小 > 最小值
check_file() {
    local file="$1"
    local min_size="${2:-1000}"
    if [ -f "$file" ] && [ $(stat -f%z "$file" 2>/dev/null || stat -c%s "$file") -gt $min_size ]; then
        return 0
    fi
    return 1
}

# 主循环
log_event "=== 启动IP地址规划自动化流程控制 ==="
log_event "目标: 生成10份交付成果"
log_event "运行agents: baseline-finalizer, design-architect, diff-generator, deployment-writer"

ITERATION=0
MAX_ITERATIONS=30  # 最多循环30次（每次30秒，共15分钟）

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))

    # 检查成果文件
    echo ""
    log_event "━━ 检查周期 #$ITERATION ━━"

    # 成果#2: 现网基线表
    if check_file "$OUTPUT_DIR/02_现网事实基线表.xlsx" 50000; then
        if [ ! -f "$LOCK_DIR/artifact2_done" ]; then
            log_event "✓ 成果#2完成: 现网事实基线表"
            touch "$LOCK_DIR/artifact2_done"
        fi
    fi

    # 成果#3: 现网问题清单
    if check_file "$OUTPUT_DIR/03_现网问题清单.md" 10000; then
        if [ ! -f "$LOCK_DIR/artifact3_done" ]; then
            log_event "✓ 成果#3完成: 现网问题清单"
            touch "$LOCK_DIR/artifact3_done"
        fi
    fi

    # 成果#5: 目标设计表
    if check_file "$OUTPUT_DIR/05_目标设计表.xlsx" 50000; then
        if [ ! -f "$LOCK_DIR/artifact5_done" ]; then
            log_event "✓ 成果#5完成: 目标IP/VLAN设计"
            touch "$LOCK_DIR/artifact5_done"
        fi
    fi

    # 成果#6: 差异矩阵
    if check_file "$OUTPUT_DIR/06_差异矩阵.xlsx" 30000; then
        if [ ! -f "$LOCK_DIR/artifact6_done" ]; then
            log_event "✓ 成果#6完成: 差异矩阵"
            touch "$LOCK_DIR/artifact6_done"
        fi
    fi

    # 成果#10: 部署文档
    if check_file "$OUTPUT_DIR/10_部署实施文档.md" 50000; then
        if [ ! -f "$LOCK_DIR/artifact10_done" ]; then
            log_event "✓ 成果#10完成: 部署实施文档"
            touch "$LOCK_DIR/artifact10_done"
        fi
    fi

    # 检查是否所有关键成果都完成
    if [ -f "$LOCK_DIR/artifact2_done" ] && \
       [ -f "$LOCK_DIR/artifact3_done" ] && \
       [ -f "$LOCK_DIR/artifact5_done" ] && \
       [ -f "$LOCK_DIR/artifact6_done" ] && \
       [ -f "$LOCK_DIR/artifact10_done" ]; then

        log_event "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_event "✓✓✓ 所有关键成果已完成！"
        log_event "━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        # 统计文件
        log_event ""
        log_event "【成果统计】"
        ls -lh "$OUTPUT_DIR"/*.xlsx "$OUTPUT_DIR"/*.md "$OUTPUT_DIR"/*.csv 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

        log_event ""
        log_event "【下一步】"
        log_event "成果已就绪，可以："
        log_event "1. 进行成果验收和质量检查"
        log_event "2. 启动实验验证环节"
        log_event "3. 安排生产部署"

        break
    fi

    # 等待后再继续
    if [ $ITERATION -lt $MAX_ITERATIONS ]; then
        log_event "等待中... ($ITERATION/$MAX_ITERATIONS)"
        sleep 30
    fi
done

if [ $ITERATION -eq $MAX_ITERATIONS ]; then
    log_event "⚠ 达到最大等待时间(15分钟)，流程控制停止"
    log_event "请检查agents的运行状态:"
    log_event "  - baseline-finalizer: Phase 2 成果"
    log_event "  - design-architect: Phase 5 成果"
    log_event "  - diff-generator: Phase 6 成果"
    log_event "  - deployment-writer: Phase 7 成果"
fi

log_event "=== 流程控制脚本结束 ==="
