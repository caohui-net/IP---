#!/bin/bash

# IP地址规划项目 - 成果自动发布和协调脚本
# 功能: 监控agents输出，自动发布成果，协调后续agents启动

PROJECT_DIR="/home/caohui/projects/IP地址规划"
OUTPUT_DIR="$PROJECT_DIR/交付成果_20260904"
STATE_DIR="/tmp/ip-planning-state"

mkdir -p "$STATE_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    local msg="$1"
    local ts=$(date '+%H:%M:%S')
    echo -e "${BLUE}[$ts]${NC} $msg" | tee -a "$OUTPUT_DIR/成果发布日志.txt"
}

log_success() {
    local msg="$1"
    local ts=$(date '+%H:%M:%S')
    echo -e "${GREEN}[$ts]${NC} ✓ $msg" | tee -a "$OUTPUT_DIR/成果发布日志.txt"
}

log_warn() {
    local msg="$1"
    local ts=$(date '+%H:%M:%S')
    echo -e "${YELLOW}[$ts]${NC} ⚠ $msg" | tee -a "$OUTPUT_DIR/成果发布日志.txt"
}

log_error() {
    local msg="$1"
    local ts=$(date '+%H:%M:%S')
    echo -e "${RED}[$ts]${NC} ✗ $msg" | tee -a "$OUTPUT_DIR/成果发布日志.txt"
}

# 快速质量检查
quick_check_artifact() {
    local file="$1"
    local type="$2"

    if [ ! -f "$file" ]; then
        return 1
    fi

    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")

    case "$type" in
        "xlsx")
            if [ $size -gt 10000 ]; then
                return 0
            else
                return 1
            fi
            ;;
        "md")
            if [ $size -gt 5000 ]; then
                return 0
            else
                return 1
            fi
            ;;
        "csv")
            if [ $size -gt 5000 ]; then
                return 0
            else
                return 1
            fi
            ;;
        *)
            if [ $size -gt 1000 ]; then
                return 0
            else
                return 1
            fi
            ;;
    esac
}

# 成果发布确认
publish_artifact() {
    local artifact_num="$1"
    local artifact_name="$2"
    local artifact_file="$3"
    local artifact_type="$4"

    if quick_check_artifact "$artifact_file" "$artifact_type"; then
        log_success "成果#$artifact_num 已生成: $artifact_name"
        log_success "  文件: $(basename $artifact_file)"
        log_success "  大小: $(du -h "$artifact_file" | cut -f1)"

        # 记录发布状态
        touch "$STATE_DIR/artifact_${artifact_num}_published"

        # 标记为可用于后续处理
        echo "$(date '+%s')" > "$STATE_DIR/artifact_${artifact_num}_timestamp"

        return 0
    else
        return 1
    fi
}

# 检查是否可启动后续agents
check_dependencies() {
    local artifact="$1"

    case "$artifact" in
        "2")
            # 成果#2不依赖其他成果
            return 0
            ;;
        "3")
            # 成果#3由baseline-finalizer同时生成
            return 0
            ;;
        "5")
            # 成果#5依赖成果#4，已完成
            if [ -f "$STATE_DIR/artifact_4_published" ]; then
                return 0
            fi
            ;;
        "6")
            # 成果#6依赖成果#2、5
            if [ -f "$STATE_DIR/artifact_2_published" ] && [ -f "$STATE_DIR/artifact_5_published" ]; then
                return 0
            fi
            ;;
        "7")
            # 成果#7依赖成果#6
            if [ -f "$STATE_DIR/artifact_6_published" ]; then
                return 0
            fi
            ;;
        "10")
            # 成果#10依赖成果#6、7
            if [ -f "$STATE_DIR/artifact_6_published" ] && [ -f "$STATE_DIR/artifact_7_published" ]; then
                return 0
            fi
            ;;
    esac

    return 1
}

# 主监控循环
log_info "=== 启动成果发布监控系统 ==="
log_info "目标: 8份成果的生成、质量检查、协调发布"
log_info ""

ITERATION=0
MAX_ITERATIONS=60  # 30分钟

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))

    # 检查成果#2
    if [ ! -f "$STATE_DIR/artifact_2_published" ]; then
        if publish_artifact "2" "现网事实基线表" "$OUTPUT_DIR/02_现网事实基线表.xlsx" "xlsx"; then
            log_info "触发后续依赖: 可启动成果#6的差异矩阵生成"
        fi
    fi

    # 检查成果#3
    if [ ! -f "$STATE_DIR/artifact_3_published" ]; then
        if publish_artifact "3" "现网问题清单" "$OUTPUT_DIR/03_现网问题清单.md" "md"; then
            log_info "现网问题识别完成，可进行风险讨论"
        fi
    fi

    # 检查成果#5
    if [ ! -f "$STATE_DIR/artifact_5_published" ]; then
        if publish_artifact "5" "目标IP/VLAN设计表" "$OUTPUT_DIR/05_目标设计表.xlsx" "xlsx"; then
            log_info "触发后续依赖: 可启动成果#6的差异矩阵生成"
        fi
    fi

    # 检查成果#6
    if [ ! -f "$STATE_DIR/artifact_6_published" ]; then
        if publish_artifact "6" "差异矩阵" "$OUTPUT_DIR/06_差异矩阵.xlsx" "xlsx"; then
            log_info "差异分析完成，可启动成果#7配置增量生成"
            log_info "触发后续依赖: 可启动成果#10部署文档生成"
        fi
    fi

    # 检查成果#7
    if [ ! -f "$STATE_DIR/artifact_7_published" ]; then
        if publish_artifact "7" "配置增量和回退" "$OUTPUT_DIR/07_配置增量和回退.md" "md"; then
            log_info "配置增量生成完成，可启动部署文档最终编写"
        fi
    fi

    # 检查成果#10
    if [ ! -f "$STATE_DIR/artifact_10_published" ]; then
        if publish_artifact "10" "部署实施文档" "$OUTPUT_DIR/10_部署实施文档.md" "md"; then
            log_info "部署文档完成，可进行部署前检查"
        fi
    fi

    # 统计已发布成果
    PUBLISHED_COUNT=$(ls "$STATE_DIR"/artifact_*_published 2>/dev/null | wc -l)

    # 检查是否所有关键成果都已发布
    if [ -f "$STATE_DIR/artifact_2_published" ] && \
       [ -f "$STATE_DIR/artifact_3_published" ] && \
       [ -f "$STATE_DIR/artifact_5_published" ] && \
       [ -f "$STATE_DIR/artifact_6_published" ] && \
       [ -f "$STATE_DIR/artifact_7_published" ] && \
       [ -f "$STATE_DIR/artifact_10_published" ]; then

        log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_success "所有关键成果已发布！(6/6)"
        log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_info ""
        log_info "【最终成果统计】"

        # 列出所有生成的成果文件
        for f in "$OUTPUT_DIR"/0[2357]_*.* "$OUTPUT_DIR"/10_*.*; do
            if [ -f "$f" ]; then
                SIZE=$(du -h "$f" | cut -f1)
                LINES=$(wc -l < "$f" 2>/dev/null || echo "N/A")
                log_success "  $(basename $f) ($SIZE)"
            fi
        done

        log_info ""
        log_info "【项目状态】"
        log_success "✓ Phase 2: 现网基线采集完成"
        log_success "✓ Phase 3: 现网问题识别完成"
        log_success "✓ Phase 4: IPAM源表已就绪"
        log_success "✓ Phase 5: 目标设计完成"
        log_success "✓ Phase 6: 差异分析和配置增量完成"
        log_success "✓ Phase 7: 部署文档完成"

        log_info ""
        log_info "【下一步】"
        log_info "1. 进行成果质量最终验收"
        log_info "2. 启动实验验证环节 (Phase 8)"
        log_info "3. 按批次执行生产部署"
        log_info "4. 采集竣工配置 (Phase 9)"

        break
    fi

    # 进度显示
    if [ $((ITERATION % 6)) -eq 0 ]; then
        log_info "监控中... ($ITERATION/60, 已发布: $PUBLISHED_COUNT)"
    fi

    sleep 30
done

if [ $ITERATION -eq $MAX_ITERATIONS ]; then
    log_warn "达到最大监控时间(30分钟)"
    log_warn "已发布成果数: $(ls "$STATE_DIR"/artifact_*_published 2>/dev/null | wc -l)"
    log_error "部分成果仍未生成，请检查agents状态"
fi

log_info ""
log_info "=== 成果发布监控结束 ==="
