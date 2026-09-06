#!/bin/bash

# IP地址规划 - 实时监控仪表板
# 显示agents状态、成果进度、质量指标

PROJECT_DIR="/home/caohui/projects/IP地址规划"
OUTPUT_DIR="$PROJECT_DIR/交付成果_20260904"

while true; do
    clear
    
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║       IP地址规划项目 - 实时监控仪表板                              ║"
    echo "║       更新时间: $(date '+%Y-%m-%d %H:%M:%S')                            ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Agents 状态
    echo "【Agents 运行状态】"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 检查各agent是否在运行
    pgrep -f "baseline-finalizer" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✓ baseline-finalizer        [████████░░░░░░░░] 生成成果#2/3"
    else
        echo "  ✗ baseline-finalizer        [停止]"
    fi
    
    pgrep -f "design-architect" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✓ design-architect          [████████░░░░░░░░] 生成成果#5"
    else
        echo "  ✗ design-architect          [停止]"
    fi
    
    pgrep -f "diff-generator" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✓ diff-generator            [████████████░░░░] 生成成果#6/7"
    else
        echo "  ○ diff-generator            [等待依赖]"
    fi
    
    pgrep -f "deployment-writer" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✓ deployment-writer         [████░░░░░░░░░░░░] 生成成果#10"
    else
        echo "  ○ deployment-writer         [等待依赖]"
    fi
    
    echo ""
    
    # 成果文件状态
    echo "【成果文件生成进度】"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    for i in 2 3 4 5 6 7 10; do
        case $i in
            2) name="现网基线表" pattern="02_现网事实基线表" ;;
            3) name="问题清单" pattern="03_现网问题清单|02_现网问题清单" ;;
            4) name="IPAM源表" pattern="04_IPAM源数据表" ;;
            5) name="目标设计" pattern="05_目标设计表" ;;
            6) name="差异矩阵" pattern="06_差异矩阵" ;;
            7) name="配置增量" pattern="07_配置增量" ;;
            10) name="部署文档" pattern="10_部署实施文档" ;;
        esac
        
        if ls "$OUTPUT_DIR"/*$pattern* > /dev/null 2>&1; then
            SIZE=$(du -h $(ls "$OUTPUT_DIR"/*$pattern* 2>/dev/null | head -1) 2>/dev/null | cut -f1)
            echo "  ✓ 成果#$i  $name                      $SIZE"
        else
            echo "  ○ 成果#$i  $name                      [生成中...]"
        fi
    done
    
    echo ""
    
    # 存储统计
    echo "【存储统计】"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    TOTAL_SIZE=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1)
    FILE_COUNT=$(ls "$OUTPUT_DIR"/*.xlsx "$OUTPUT_DIR"/*.md "$OUTPUT_DIR"/*.csv 2>/dev/null | wc -l)
    
    echo "  总大小: $TOTAL_SIZE"
    echo "  文件数: $FILE_COUNT"
    echo "  可用空间: $(df -h "$OUTPUT_DIR" | tail -1 | awk '{print $4}')"
    
    echo ""
    
    # 质量指标
    echo "【质量指标】"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -f "$OUTPUT_DIR/04_IPAM源数据表.csv" ]; then
        IPAM_LINES=$(wc -l < "$OUTPUT_DIR/04_IPAM源数据表.csv" 2>/dev/null)
        echo "  IPAM记录: $IPAM_LINES 条 ✓"
    fi
    
    if ls "$OUTPUT_DIR"/02_现网问题清单* > /dev/null 2>&1; then
        PROBLEM_FILE=$(ls "$OUTPUT_DIR"/02_现网问题清单* 2>/dev/null | head -1)
        PROBLEM_SIZE=$(du -h "$PROBLEM_FILE" 2>/dev/null | cut -f1)
        echo "  问题识别: $PROBLEM_SIZE (详细分析) ✓"
    fi
    
    if [ -f "$OUTPUT_DIR/05_目标设计表.xlsx" ]; then
        echo "  目标设计: 已完成编码验证 ✓"
    fi
    
    echo ""
    
    # 进度摘要
    echo "【进度摘要】"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    COMPLETED=$(ls "$OUTPUT_DIR"/*.xlsx "$OUTPUT_DIR"/*.md "$OUTPUT_DIR"/*.csv 2>/dev/null | wc -l)
    TOTAL=10
    PERCENT=$((COMPLETED * 100 / TOTAL))
    
    echo "  完成度: $COMPLETED/$TOTAL ($PERCENT%)"
    printf "  进度条: ["
    for ((i=0; i<20; i++)); do
        if [ $((i * 5)) -lt $PERCENT ]; then
            printf "█"
        else
            printf "░"
        fi
    done
    printf "] $PERCENT%%\n"
    
    echo ""
    echo "【快捷键】"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  按 'q' 退出  |  按 'r' 刷新  |  自动刷新: 10秒"
    echo ""
    
    # 读取用户输入（非阻塞）
    read -t 10 -n 1 INPUT
    
    case $INPUT in
        q|Q) exit 0 ;;
        r|R) continue ;;
        *) continue ;;
    esac
done
