#!/bin/bash

# IP地址规划项目 - 最终完成检查
# 功能: 监控成果#7/10完成，自动生成最终交付报告

PROJECT_DIR="/home/caohui/projects/IP地址规划"
OUTPUT_DIR="$PROJECT_DIR/交付成果_20260904"

echo "【IP地址规划项目 - 最终完成检查】"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查关键成果
echo "检查关键成果文件..."
echo ""

ARTIFACT_COUNT=0
for i in 2 3 4 5 6; do
    case $i in
        2) pattern="02_现网事实基线表" size_mb=">200" ;;
        3) pattern="02_现网问题清单|03_现网问题清单" size_mb=">50" ;;
        4) pattern="04_IPAM源数据表" size_mb=">10" ;;
        5) pattern="05_目标设计表" size_mb=">10" ;;
        6) pattern="06_差异矩阵" size_mb=">10" ;;
    esac
    
    if ls "$OUTPUT_DIR"/*$pattern* > /dev/null 2>&1; then
        FILE=$(ls "$OUTPUT_DIR"/*$pattern* 2>/dev/null | head -1)
        SIZE=$(du -h "$FILE" | cut -f1)
        echo "  ✓ 成果#$i: 已生成 ($SIZE)"
        ARTIFACT_COUNT=$((ARTIFACT_COUNT + 1))
    fi
done

echo ""
echo "成果#7、#10生成检查..."

if [ -f "$OUTPUT_DIR/07_配置增量和回退.md" ]; then
    SIZE=$(du -h "$OUTPUT_DIR/07_配置增量和回退.md" | cut -f1)
    echo "  ✓ 成果#7: 已生成 ($SIZE)"
    ARTIFACT_COUNT=$((ARTIFACT_COUNT + 1))
else
    echo "  ⏳ 成果#7: 生成中..."
fi

if [ -f "$OUTPUT_DIR/10_部署实施文档.md" ]; then
    SIZE=$(du -h "$OUTPUT_DIR/10_部署实施文档.md" | cut -f1)
    echo "  ✓ 成果#10: 已生成 ($SIZE)"
    ARTIFACT_COUNT=$((ARTIFACT_COUNT + 1))
else
    echo "  ⏳ 成果#10: 生成中..."
fi

echo ""
echo "支持文档生成检查..."
SUPPORT_COUNT=$(ls "$OUTPUT_DIR"/*.md 2>/dev/null | wc -l)
echo "  📋 支持文档: $SUPPORT_COUNT 份"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "【项目完成度】"
echo "  已完成成果: $ARTIFACT_COUNT/10"
PERCENT=$((ARTIFACT_COUNT * 100 / 10))
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

if [ $ARTIFACT_COUNT -ge 8 ]; then
    echo "✅ 【首轮交付完成】所有关键成果已就绪"
    echo ""
    echo "后续行动:"
    echo "  1. 进行最终质量验收"
    echo "  2. 启动实验验证 (Phase 8)"
    echo "  3. 准备生产部署 (Phase 9)"
else
    echo "⏳ 【等待中】部分成果仍在生成..."
    echo "  预期完成时间: 2026-09-05 18:10 UTC"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
