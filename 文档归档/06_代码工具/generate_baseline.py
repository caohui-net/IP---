#!/usr/bin/env python3
"""
从parsed JSON生成现网事实基线表和问题清单
"""
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict
import re

def load_json(filepath):
    """加载JSON文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def infer_business_type(vlan_name, vlan_id):
    """根据VLAN名称和ID推断业务类型"""
    name_lower = vlan_name.lower()

    # 教师
    if any(kw in name_lower for kw in ['teacher', 'faculty', '教师', 'staff', 'office']):
        return '教师办公'

    # 学生
    if any(kw in name_lower for kw in ['student', '学生', 'dorm', 'dormitory', '宿舍']):
        return '学生宿舍'

    # 访客
    if any(kw in name_lower for kw in ['guest', 'visitor', '访客', 'wifi']):
        return '访客无线'

    # 设备管理
    if any(kw in name_lower for kw in ['管理', 'manage', 'admin', 'monitor', 'device']):
        return '设备管理'

    # 服务器
    if any(kw in name_lower for kw in ['server', '服务器', 'data']):
        return '服务器'

    # 物联网
    if any(kw in name_lower for kw in ['iot', '物联', 'sensor', 'camera', '监控']):
        return '物联网'

    # 根据VLAN ID范围推断
    if 100 <= vlan_id < 200:
        return '教师办公'
    elif 200 <= vlan_id < 300:
        return '学生宿舍'
    elif 300 <= vlan_id < 400:
        return '访客无线'
    elif vlan_id >= 1000:
        return '设备管理'

    return '其他'

def extract_ip_prefix(ip_with_mask):
    """从IP/掩码中提取网络前缀"""
    if not ip_with_mask or '/' not in ip_with_mask:
        return None
    return ip_with_mask.split('/')[0].rsplit('.', 1)[0]

def analyze_campus_data(campus_data, campus_name, obj_id_start):
    """分析单个校区的数据"""
    rows = []
    issues = []

    # 数据已经是字典格式
    vlans_data = campus_data.get('vlans', {})
    svi_data = campus_data.get('svis', {})
    dhcp_pools_data = campus_data.get('dhcp_pools', {})

    # 建立VLAN到DHCP pool的映射（通过network匹配）
    dhcp_by_vlan = {}
    for pool_name, pool_info in dhcp_pools_data.items():
        # 尝试从pool名称或network匹配VLAN
        # 简化：通过network的第三段匹配VLAN ID
        if pool_info.get('network'):
            dhcp_by_vlan[pool_name] = pool_info

    # 建立VLAN到SVI的映射
    svi_by_vlan = {}
    for svi_id, svi_info in svi_data.items():
        vlan_id = svi_info.get('vlan', '')
        if vlan_id:
            svi_by_vlan[vlan_id] = svi_info

    # 遍历所有VLAN
    obj_id = obj_id_start
    for vlan_id_str, vlan_info in vlans_data.items():
        try:
            vlan_id = int(vlan_id_str)
        except:
            continue

        vlan_name = vlan_info.get('name', '')
        vlan_type = vlan_info.get('type', '')

        # SVI信息
        svi_info = svi_by_vlan.get(vlan_id_str, {})
        svi_ip = svi_info.get('ip', '')
        svi_mask = svi_info.get('mask', '')

        # 转换掩码为CIDR
        cidr = ''
        if svi_mask:
            mask_map = {
                '255.255.255.0': '24',
                '255.255.254.0': '23',
                '255.255.252.0': '22',
                '255.255.248.0': '21',
                '255.255.240.0': '20',
                '255.255.128.0': '17',
                '255.255.0.0': '16'
            }
            cidr = mask_map.get(svi_mask, '')

        # DHCP信息 - 通过SVI的IP网段匹配DHCP pool
        dhcp_info = {}
        dhcp_mode = 'none'
        dhcp_pool = ''

        if svi_ip:
            # 提取IP的前三段
            ip_prefix = '.'.join(svi_ip.split('.')[:3])
            for pool_name, pool_data in dhcp_pools_data.items():
                pool_network = pool_data.get('network', '')
                if pool_network.startswith(ip_prefix):
                    dhcp_info = pool_data
                    dhcp_mode = 'server'
                    # 计算池范围 (简化：假设是.1-.253)
                    dhcp_pool = f"{ip_prefix}.1 - {ip_prefix}.253"
                    break

        # 检查SVI是否配置了DHCP server
        if svi_info.get('dhcp_server'):
            dhcp_mode = 'server'

        # 推断业务类型
        business_type = infer_business_type(vlan_name, vlan_id)

        # 构建IP前缀
        ip_prefix = ''
        if svi_ip and cidr:
            ip_prefix = f"{svi_ip}/{cidr}"
        elif svi_ip and svi_mask:
            ip_prefix = f"{svi_ip}/{svi_mask}"

        # 网关IP (通常是SVI IP)
        gateway_ip = svi_ip

        # 数据来源
        source = f"VLAN配置行{vlan_info.get('source_line', 'N/A')}"
        if svi_info:
            source += f" + SVI配置行{svi_info.get('source_line', 'N/A')}"

        # 确认状态
        completeness = '✓ 完整'
        if not svi_ip:
            completeness = '⚠️ 部分'
        if not dhcp_mode or dhcp_mode == 'none':
            if completeness == '✓ 完整':
                completeness = '⚠️ 部分'

        row = {
            '对象ID': f"B-{obj_id:03d}",
            '校区': campus_name,
            'VLAN编号': vlan_id,
            'VLAN名称': vlan_name,
            'IP前缀': ip_prefix,
            'SVI接口IP': svi_ip,
            '网关IP': gateway_ip,
            'DHCP模式': dhcp_mode,
            'DHCP池范围': dhcp_pool,
            '业务分类': business_type,
            '接入设备类型': '',  # 需要从其他数据源获取
            'Trunk配置': '',
            '认证方式': '',
            'ACL/PBR策略': '',
            '在线MAC数': '',
            '在线ARP数': '',
            'DHCP租约数': '',
            '接口状态': 'active' if svi_ip else 'unknown',
            '数据来源': source,
            '确认状态': completeness
        }

        rows.append(row)
        obj_id += 1

    return rows, issues, obj_id

def check_ip_overlaps(all_rows):
    """检查IP地址重叠"""
    issues = []
    ip_usage = defaultdict(list)

    for row in all_rows:
        ip_prefix = row.get('IP前缀', '')
        if not ip_prefix:
            continue

        # 提取网络地址
        if '/' in ip_prefix:
            network = ip_prefix.split('/')[0]
            # 简化：提取前3段作为网络
            parts = network.split('.')
            if len(parts) >= 3:
                net_prefix = '.'.join(parts[:3])
                ip_usage[net_prefix].append({
                    'id': row.get('对象ID', ''),
                    'campus': row.get('校区', ''),
                    'vlan': row.get('VLAN编号', ''),
                    'ip': ip_prefix
                })

    # 检查重叠
    for net_prefix, usages in ip_usage.items():
        if len(usages) > 1:
            issue = {
                'level': 'P0',
                'id': f"P0-{len(issues)+1:03d}",
                'title': f'IP地址重叠: {net_prefix}.x',
                'description': f'网段 {net_prefix}.x 被多个VLAN使用',
                'scope': ', '.join([f"{u.get('campus', '')}-VLAN{u.get('vlan', '')}" for u in usages]),
                'evidence': '; '.join([f"{u.get('id', '')}: {u.get('ip', '')}" for u in usages]),
                'suggestion': '重新规划IP地址，确保每个VLAN使用唯一的网段',
                'closure': '确认无IP地址冲突'
            }
            issues.append(issue)

    return issues

def check_vlan_duplicates(all_rows):
    """检查VLAN编号重复"""
    issues = []
    vlan_usage = defaultdict(list)

    for row in all_rows:
        vlan_id = row.get('VLAN编号')
        if not vlan_id:
            continue

        vlan_usage[vlan_id].append({
            'id': row.get('对象ID', ''),
            'campus': row.get('校区', ''),
            'name': row.get('VLAN名称', '')
        })

    # 检查跨校区重复
    for vlan_id, usages in vlan_usage.items():
        campuses = set(u.get('campus', '') for u in usages)
        if len(campuses) > 1:
            issue = {
                'level': 'P0',
                'id': f"P0-{len(issues)+1:03d}",
                'title': f'VLAN{vlan_id}跨校区重复',
                'description': f'VLAN {vlan_id} 在多个校区使用',
                'scope': ', '.join(campuses),
                'evidence': '; '.join([f"{u.get('campus', '')}: {u.get('name', '')}" for u in usages]),
                'suggestion': '统一VLAN编号规划，避免跨校区冲突',
                'closure': '确认VLAN编号唯一性'
            }
            issues.append(issue)

    return issues

def check_naming_consistency(all_rows):
    """检查命名一致性"""
    issues = []
    business_vlans = defaultdict(list)

    for row in all_rows:
        business = row.get('业务分类', '')
        if business and business != '其他':
            business_vlans[business].append({
                'vlan': row.get('VLAN编号', ''),
                'name': row.get('VLAN名称', ''),
                'campus': row.get('校区', '')
            })

    for business, vlans in business_vlans.items():
        names = set(v.get('name', '') for v in vlans if v.get('name'))
        if len(names) > 3:  # 同一业务超过3种命名方式
            issue = {
                'level': 'P1',
                'id': f"P1-{len(issues)+1:03d}",
                'title': f'{business}VLAN命名不统一',
                'description': f'{business}业务的VLAN命名方式多样，缺乏统一标准',
                'scope': f'{len(vlans)}个VLAN',
                'evidence': f'发现{len(names)}种不同命名: {", ".join(list(names)[:3])}...',
                'suggestion': '制定统一的VLAN命名规范',
                'closure': '所有同类业务VLAN遵循统一命名规则'
            }
            issues.append(issue)

    return issues

def main():
    """主函数"""
    base_dir = Path('/home/caohui/projects/IP地址规划/交付成果_20260904')

    # 加载数据
    print("加载JSON数据...")
    all_campuses = load_json(base_dir / 'parsed_all_campuses.json')

    all_rows = []
    all_issues = []
    obj_id = 1

    # 处理每个校区
    for campus_data in all_campuses:
        campus_name = campus_data.get('campus', 'Unknown')
        print(f"处理{campus_name}...")
        rows, issues, obj_id = analyze_campus_data(campus_data, campus_name, obj_id)
        all_rows.extend(rows)
        all_issues.extend(issues)

    print(f"共提取 {len(all_rows)} 条基线记录")

    # 生成基线表
    df = pd.DataFrame(all_rows)
    output_file = base_dir / '02_现网事实基线表.xlsx'
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"✓ 生成基线表: {output_file}")

    # 问题检查
    print("\n执行问题检查...")
    p0_issues = []
    p0_issues.extend(check_ip_overlaps(all_rows))
    p0_issues.extend(check_vlan_duplicates(all_rows))

    p1_issues = []
    p1_issues.extend(check_naming_consistency(all_rows))

    # 生成问题清单
    with open(base_dir / '03_现网问题清单.md', 'w', encoding='utf-8') as f:
        f.write("# 现网问题清单\n\n")
        f.write(f"**生成时间**: 2026-09-04\n\n")
        f.write(f"**统计**: P0级{len(p0_issues)}项, P1级{len(p1_issues)}项\n\n")

        # P0问题
        f.write("## P0级问题 (可用性风险)\n\n")
        if p0_issues:
            for issue in p0_issues:
                f.write(f"### {issue['id']}: {issue['title']}\n\n")
                f.write(f"**描述**: {issue['description']}\n\n")
                f.write(f"**影响范围**: {issue['scope']}\n\n")
                f.write(f"**证据**: {issue['evidence']}\n\n")
                f.write(f"**建议处置**: {issue['suggestion']}\n\n")
                f.write(f"**关闭标准**: {issue['closure']}\n\n")
                f.write("---\n\n")
        else:
            f.write("*未发现P0级问题*\n\n")

        # P1问题
        f.write("## P1级问题 (功能问题)\n\n")
        if p1_issues:
            for issue in p1_issues:
                f.write(f"### {issue['id']}: {issue['title']}\n\n")
                f.write(f"**描述**: {issue['description']}\n\n")
                f.write(f"**影响范围**: {issue['scope']}\n\n")
                f.write(f"**证据**: {issue['evidence']}\n\n")
                f.write(f"**建议处置**: {issue['suggestion']}\n\n")
                f.write(f"**关闭标准**: {issue['closure']}\n\n")
                f.write("---\n\n")
        else:
            f.write("*未发现P1级问题*\n\n")

        # P2问题
        f.write("## P2级问题 (规范性问题)\n\n")
        f.write("*待现场调研补充*\n\n")

    print(f"✓ 生成问题清单: {base_dir / '03_现网问题清单.md'}")

    # 数据质量报告
    complete_count = len([r for r in all_rows if r['确认状态'] == '✓ 完整'])
    completeness = (complete_count / len(all_rows) * 100) if all_rows else 0

    print(f"\n## 数据质量报告")
    print(f"完整度: {completeness:.1f}% ({complete_count}/{len(all_rows)})")
    print(f"P0问题: {len(p0_issues)}项")
    print(f"P1问题: {len(p1_issues)}项")

if __name__ == '__main__':
    main()
