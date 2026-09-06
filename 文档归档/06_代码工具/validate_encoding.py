#!/usr/bin/env python3
"""
编码规范验证脚本
验证IPAM源表中的目标IP/VLAN/SVI是否符合第四章编码规则
"""

import csv
import re
from typing import Dict, List, Tuple
from collections import defaultdict

# 编码规则定义
REGION_CODES = {
    '东校区': {'code': 1, 'ip_base': 10, 'vlan_base': 100},
    '西校区': {'code': 2, 'ip_base': 20, 'vlan_base': 200},
    '南校区': {'code': 3, 'ip_base': 30, 'vlan_base': 300},
    '服务器区': {'code': 4, 'ip_base': 40, 'vlan_base': 400},
    '物联网区': {'code': 9, 'ip_base': 90, 'vlan_base': 900},
}

BUSINESS_CODES = {
    '教师有线': {'code': 1, 'vlan_offset': 1},
    '教师无线': {'code': 2, 'vlan_offset': 2},
    '学生有线': {'code': 3, 'vlan_offset': 3},
    '学生无线': {'code': 4, 'vlan_offset': 4},
    '访客无线': {'code': 7, 'vlan_offset': 7},
    '设备管理': {'code': 8, 'vlan_offset': 8},
    '互联网出口': {'code': 9, 'vlan_offset': 99},  # 特殊业务
}

# 服务器区和物联网区特殊处理
SERVER_IOT_BUSINESS = {
    'Web服务器': {'code': 1, 'vlan_offset': 1},
    '数据库服务器': {'code': 1, 'vlan_offset': 1},
    '应用服务器': {'code': 1, 'vlan_offset': 1},
    '存储服务器': {'code': 1, 'vlan_offset': 1},
    '监控摄像头': {'code': 1, 'vlan_offset': 1},
    '门禁系统': {'code': 1, 'vlan_offset': 1},
    '环境监测': {'code': 1, 'vlan_offset': 1},
    '智能照明': {'code': 1, 'vlan_offset': 1},
    '消防系统': {'code': 1, 'vlan_offset': 1},
}

def parse_ip_prefix(prefix: str) -> Tuple[int, int, int, int, int]:
    """解析IP前缀 10.B.C.D/mask"""
    match = re.match(r'10\.(\d+)\.(\d+)\.(\d+)/(\d+)', prefix)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
    return None, None, None, None

def validate_encoding(csv_file: str) -> List[Dict]:
    """验证编码规范"""
    results = []
    ip_conflicts = defaultdict(list)
    vlan_conflicts = defaultdict(list)

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            obj_id = row['对象ID']
            campus = row['校区']
            business = row['业务']
            building_id = int(row['楼栋ID']) if row['楼栋ID'].isdigit() else 0
            target_ip = row['目标IP前缀']
            target_vlan = int(row['目标VLAN']) if row['目标VLAN'].isdigit() else 0
            target_svi = row['目标SVI']

            result = {
                'obj_id': obj_id,
                'campus': campus,
                'business': business,
                'building_id': building_id,
                'target_ip': target_ip,
                'target_vlan': target_vlan,
                'target_svi': target_svi,
                'errors': [],
                'warnings': [],
            }

            # 获取区域编码
            if campus not in REGION_CODES:
                result['errors'].append(f"未知校区: {campus}")
                results.append(result)
                continue

            region_info = REGION_CODES[campus]
            region_code = region_info['code']
            vlan_base = region_info['vlan_base']

            # 获取业务编码
            if campus in ['服务器区', '物联网区']:
                if business in SERVER_IOT_BUSINESS:
                    bus_info = SERVER_IOT_BUSINESS[business]
                else:
                    result['warnings'].append(f"服务器区/物联网区未定义业务: {business}")
                    bus_info = {'code': 1, 'vlan_offset': 1}
            else:
                if business not in BUSINESS_CODES:
                    result['errors'].append(f"未知业务类型: {business}")
                    results.append(result)
                    continue
                bus_info = BUSINESS_CODES[business]

            business_code = bus_info['code']
            vlan_offset = bus_info['vlan_offset']

            # 验证IP编码: 10.B.C.D
            b, c, d, mask = parse_ip_prefix(target_ip)
            if b is None:
                result['errors'].append(f"无法解析目标IP前缀: {target_ip}")
            else:
                # 计算期望的B值
                expected_b = region_code * 10 + business_code

                # 验证B字段
                if b != expected_b:
                    result['errors'].append(
                        f"IP第二段B={b}不符合规则(期望={expected_b}, "
                        f"区域码{region_code}×10+业务码{business_code})"
                    )

                # 验证C字段(楼栋编号×8)
                expected_c = building_id * 8
                if c != expected_c:
                    result['errors'].append(
                        f"IP第三段C={c}不符合规则(期望={expected_c}, "
                        f"楼栋{building_id}×8)"
                    )

                # 检查IP冲突
                ip_conflicts[target_ip].append(obj_id)

            # 验证VLAN编码
            if business == '互联网出口':
                # 互联网出口特殊处理: 基数+99
                expected_vlan = vlan_base + 99
            else:
                expected_vlan = vlan_base + vlan_offset

            if target_vlan != expected_vlan:
                result['warnings'].append(
                    f"VLAN={target_vlan}不符合标准规则(期望={expected_vlan}, "
                    f"基数{vlan_base}+偏移{vlan_offset}), 可能是受控避让"
                )

            # 检查VLAN合法性
            if target_vlan < 1 or target_vlan > 4094:
                result['errors'].append(f"VLAN={target_vlan}不在合法范围[1-4094]")

            # 检查VLAN冲突
            vlan_conflicts[target_vlan].append(obj_id)

            # 验证SVI网关地址
            svi_match = re.match(r'10\.(\d+)\.(\d+)\.(\d+)', target_svi)
            if svi_match:
                svi_b = int(svi_match.group(1))
                svi_c = int(svi_match.group(2))
                svi_d = int(svi_match.group(3))

                # 网关应该与IP前缀的B.C匹配
                if svi_b != b or svi_c != c:
                    result['errors'].append(
                        f"SVI网关{target_svi}与IP前缀{target_ip}的B.C字段不匹配"
                    )

                # 检查网关规则(T-08待决议: 首个/24的.254 vs 末端/24的.254)
                if svi_d == 254:
                    # 假设采用"首个/24的.254"规则
                    if c % 8 != 0:
                        result['warnings'].append(
                            f"SVI网关{target_svi}使用.254, 但C={c}不是8的倍数, "
                            f"需确认是否采用首个/24规则"
                        )
                else:
                    result['warnings'].append(
                        f"SVI网关{target_svi}不是.254结尾, 需确认网关选择规则"
                    )

            results.append(result)

    # 检查IP冲突
    for ip_prefix, obj_ids in ip_conflicts.items():
        if len(obj_ids) > 1:
            for obj_id in obj_ids:
                for result in results:
                    if result['obj_id'] == obj_id:
                        result['errors'].append(
                            f"IP前缀{ip_prefix}冲突, 被{len(obj_ids)}个对象使用: {', '.join(obj_ids)}"
                        )

    # 检查VLAN冲突
    for vlan, obj_ids in vlan_conflicts.items():
        if len(obj_ids) > 1:
            for obj_id in obj_ids:
                for result in results:
                    if result['obj_id'] == obj_id:
                        result['errors'].append(
                            f"VLAN {vlan}冲突, 被{len(obj_ids)}个对象使用: {', '.join(obj_ids)}"
                        )

    return results

def print_validation_report(results: List[Dict]):
    """打印验证报告"""
    print("=" * 80)
    print("编码规范验证报告")
    print("=" * 80)
    print()

    total = len(results)
    errors = sum(1 for r in results if r['errors'])
    warnings = sum(1 for r in results if r['warnings'] and not r['errors'])
    passed = total - errors - warnings

    print(f"总计: {total} 条记录")
    print(f"✓ 通过: {passed} 条")
    print(f"⚠ 警告: {warnings} 条")
    print(f"✗ 错误: {errors} 条")
    print()

    if errors > 0:
        print("=" * 80)
        print("错误详情 (阻塞设计)")
        print("=" * 80)
        for result in results:
            if result['errors']:
                print(f"\n[{result['obj_id']}] {result['campus']} - {result['business']}")
                print(f"  目标IP: {result['target_ip']}")
                print(f"  目标VLAN: {result['target_vlan']}")
                print(f"  目标SVI: {result['target_svi']}")
                for err in result['errors']:
                    print(f"  ✗ {err}")

    if warnings > 0:
        print("\n" + "=" * 80)
        print("警告详情 (需确认)")
        print("=" * 80)
        for result in results:
            if result['warnings'] and not result['errors']:
                print(f"\n[{result['obj_id']}] {result['campus']} - {result['business']}")
                print(f"  目标IP: {result['target_ip']}")
                print(f"  目标VLAN: {result['target_vlan']}")
                for warn in result['warnings']:
                    print(f"  ⚠ {warn}")

    print("\n" + "=" * 80)
    print("验证完成")
    print("=" * 80)

if __name__ == '__main__':
    results = validate_encoding('04_IPAM源数据表.csv')
    print_validation_report(results)

    # 输出JSON供后续处理
    import json
    with open('validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n详细结果已保存到: validation_results.json")
