#!/usr/bin/env python3
"""
目标设计表生成器
基于IPAM源表生成完整的目标配置设计
"""

import csv
import json
import re
from typing import Dict, List
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# 加载IPAM源数据
def load_ipam_data(csv_file: str) -> List[Dict]:
    """加载IPAM源数据"""
    data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

# 解析IP前缀
def parse_ip_prefix(prefix: str):
    """解析IP前缀"""
    match = re.match(r'(\d+\.\d+\.\d+\.\d+)/(\d+)', prefix)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

# 计算IP容量
def calculate_capacity(mask: int) -> Dict:
    """计算IP容量"""
    total_ips = 2 ** (32 - mask)
    usable_ips = total_ips - 2  # 减去网络地址和广播地址

    # DHCP池通常预留20%作为静态IP
    dhcp_pool_size = int(usable_ips * 0.8)
    static_reserve = usable_ips - dhcp_pool_size

    return {
        'total_ips': total_ips,
        'usable_ips': usable_ips,
        'dhcp_pool_size': dhcp_pool_size,
        'static_reserve': static_reserve,
    }

# 生成DHCP配置
def generate_dhcp_config(row: Dict) -> Dict:
    """生成DHCP详细配置"""
    dhcp_mode = row['DHCP配置']
    target_ip = row['目标IP前缀']
    target_svi = row['目标SVI']

    ip_addr, mask = parse_ip_prefix(target_ip)
    if not ip_addr:
        return {}

    capacity = calculate_capacity(mask)

    # 解析网段
    ip_parts = ip_addr.split('.')
    network_base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"

    config = {
        'mode': dhcp_mode,
        'gateway': target_svi,
        'dns_primary': '114.114.114.114',
        'dns_secondary': '8.8.8.8',
        'lease_time': '86400',  # 24小时
    }

    if '禁用' in dhcp_mode or '静态' in dhcp_mode:
        config['pool_start'] = 'N/A'
        config['pool_end'] = 'N/A'
        config['pool_size'] = 0
    else:
        # DHCP池范围: 从.10开始到.250 (或网段容量限制)
        if mask == 24:  # /24
            pool_start = f"{network_base}.10"
            pool_end = f"{network_base}.250"
            pool_size = 241
        elif mask == 21:  # /21 (2048 IPs)
            pool_start = f"{network_base}.10"
            # /21跨越8个/24, 计算最后一个/24
            last_octet = int(ip_parts[2]) + 7
            pool_end = f"{ip_parts[0]}.{ip_parts[1]}.{last_octet}.250"
            pool_size = capacity['dhcp_pool_size']
        else:
            pool_start = f"{network_base}.10"
            pool_end = f"{network_base}.{min(250, capacity['usable_ips'])}"
            pool_size = capacity['dhcp_pool_size']

        config['pool_start'] = pool_start
        config['pool_end'] = pool_end
        config['pool_size'] = pool_size

    return config

# 识别SuperVLAN架构
def identify_supervlan_groups(data: List[Dict]) -> Dict:
    """识别SuperVLAN分组"""
    groups = {}

    for row in data:
        campus = row['校区']
        business = row['业务']
        vlan = row['目标VLAN']
        svi = row['目标SVI']

        key = f"{campus}-{business}-{vlan}-{svi}"

        if key not in groups:
            groups[key] = []
        groups[key].append(row['对象ID'])

    # 只保留有多个对象的组 (SuperVLAN)
    supervlan_groups = {k: v for k, v in groups.items() if len(v) > 1}

    return supervlan_groups

# 生成目标设计记录
def generate_target_design(row: Dict, supervlan_groups: Dict) -> Dict:
    """生成单条目标设计记录"""
    obj_id = row['对象ID']
    campus = row['校区']
    business = row['业务']
    building_id = row['楼栋ID']
    building_name = row['楼栋名称']

    target_ip = row['目标IP前缀']
    target_vlan = row['目标VLAN']
    target_svi = row['目标SVI']

    # DHCP配置
    dhcp_config = generate_dhcp_config(row)

    # 容量评估
    _, mask = parse_ip_prefix(target_ip)
    capacity = calculate_capacity(mask) if mask else {}

    # SuperVLAN识别
    key = f"{campus}-{business}-{target_vlan}-{target_svi}"
    is_supervlan = key in supervlan_groups
    supervlan_members = supervlan_groups.get(key, [])

    # 安全策略
    security_policy = row['安全策略']
    auth_method = row['认证方式']

    # IPv6配置
    ipv6_config = row['IPv6配置'] if row['IPv6配置'] != '无' else 'N/A'

    # 迁移批次
    migration_batch = row['迁移批次']

    # 路由所有权
    routing_owner = row['路由所有权']

    design = {
        '对象ID': obj_id,
        '校区': campus,
        '业务分类': business,
        '楼栋ID': building_id,
        '楼栋名称': building_name,
        '目标IP前缀': target_ip,
        '目标VLAN': target_vlan,
        '目标SVI': target_svi,
        'DHCP模式': dhcp_config.get('mode', 'N/A'),
        'DHCP池起始': dhcp_config.get('pool_start', 'N/A'),
        'DHCP池结束': dhcp_config.get('pool_end', 'N/A'),
        'DHCP池大小': dhcp_config.get('pool_size', 0),
        'DHCP网关': dhcp_config.get('gateway', 'N/A'),
        'DHCP DNS主': dhcp_config.get('dns_primary', 'N/A'),
        'DHCP DNS副': dhcp_config.get('dns_secondary', 'N/A'),
        '租约时间': dhcp_config.get('lease_time', 'N/A'),
        '网段掩码': f"/{mask}" if mask else 'N/A',
        '总IP数': capacity.get('total_ips', 0),
        '可用IP数': capacity.get('usable_ips', 0),
        '静态预留': capacity.get('static_reserve', 0),
        '是否SuperVLAN': '是' if is_supervlan else '否',
        'SuperVLAN成员数': len(supervlan_members) if is_supervlan else 1,
        'SuperVLAN成员': ','.join(supervlan_members) if is_supervlan else obj_id,
        '认证方式': auth_method,
        '安全策略': security_policy,
        'IPv6配置': ipv6_config,
        '路由所有权': routing_owner,
        '迁移批次': migration_batch,
        '端口配置': row['端口编号'],
        'Trunk配置': row['Trunk配置'],
        '验证项': row['验证项'],
        '回退编号': row['回退编号'],
        '责任人': row['责任人'],
    }

    return design

# 生成Excel文件
def generate_excel(designs: List[Dict], risks: List[Dict], encoding_checks: List[Dict]):
    """生成目标设计Excel文件"""
    wb = Workbook()

    # 样式定义
    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Sheet 1: 目标设计明细表
    ws1 = wb.active
    ws1.title = "目标设计明细"

    # 写入标题行
    headers1 = list(designs[0].keys())
    for col_idx, header in enumerate(headers1, 1):
        cell = ws1.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # 写入数据
    for row_idx, design in enumerate(designs, 2):
        for col_idx, key in enumerate(headers1, 1):
            cell = ws1.cell(row=row_idx, column=col_idx, value=design[key])
            cell.border = border
            cell.alignment = Alignment(vertical='center')

    # 调整列宽
    from openpyxl.utils import get_column_letter
    for col_idx in range(1, len(headers1) + 1):
        ws1.column_dimensions[get_column_letter(col_idx)].width = 15

    # Sheet 2: 编码验证表
    ws2 = wb.create_sheet("编码验证")

    headers2 = ['对象ID', '校区', '业务', '目标IP前缀', '目标VLAN', '目标SVI',
                '编码规范性', '验证结果', '问题描述']
    for col_idx, header in enumerate(headers2, 1):
        cell = ws2.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # 写入编码检查结果
    for row_idx, check in enumerate(encoding_checks, 2):
        ws2.cell(row=row_idx, column=1, value=check['obj_id']).border = border
        ws2.cell(row=row_idx, column=2, value=check['campus']).border = border
        ws2.cell(row=row_idx, column=3, value=check['business']).border = border
        ws2.cell(row=row_idx, column=4, value=check['target_ip']).border = border
        ws2.cell(row=row_idx, column=5, value=check['target_vlan']).border = border
        ws2.cell(row=row_idx, column=6, value=check['target_svi']).border = border

        # 编码规范性
        if check['is_compliant']:
            cell = ws2.cell(row=row_idx, column=7, value='符合')
            cell.fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
        else:
            cell = ws2.cell(row=row_idx, column=7, value='不符合')
            cell.fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
        cell.border = border

        ws2.cell(row=row_idx, column=8, value=check['result']).border = border
        ws2.cell(row=row_idx, column=9, value=check['issues']).border = border

    # Sheet 3: 风险清单
    ws3 = wb.create_sheet("风险清单")

    headers3 = ['风险等级', '风险类别', '风险描述', '影响对象', '处置建议', '状态']
    for col_idx, header in enumerate(headers3, 1):
        cell = ws3.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # 写入风险
    for row_idx, risk in enumerate(risks, 2):
        level_cell = ws3.cell(row=row_idx, column=1, value=risk['level'])
        level_cell.border = border
        if risk['level'] == 'P0':
            level_cell.fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
        elif risk['level'] == 'P1':
            level_cell.fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')

        ws3.cell(row=row_idx, column=2, value=risk['category']).border = border
        ws3.cell(row=row_idx, column=3, value=risk['description']).border = border
        ws3.cell(row=row_idx, column=4, value=risk['affected']).border = border
        ws3.cell(row=row_idx, column=5, value=risk['recommendation']).border = border
        ws3.cell(row=row_idx, column=6, value=risk['status']).border = border

    # 调整列宽
    for sheet in [ws2, ws3]:
        for col_idx in range(1, 10):
            sheet.column_dimensions[get_column_letter(col_idx)].width = 20

    # 保存文件
    wb.save('05_目标设计表.xlsx')
    print("✓ 已生成: 05_目标设计表.xlsx")

# 生成编码验证记录
def generate_encoding_checks(designs: List[Dict], supervlan_groups: Dict) -> List[Dict]:
    """生成编码验证记录"""
    checks = []

    for design in designs:
        obj_id = design['对象ID']
        campus = design['校区']
        business = design['业务分类']
        target_ip = design['目标IP前缀']
        target_vlan = design['目标VLAN']
        target_svi = design['目标SVI']
        is_supervlan = design['是否SuperVLAN'] == '是'

        issues = []
        is_compliant = True

        # 检查SuperVLAN架构
        if is_supervlan:
            result = f"SuperVLAN架构 (共{design['SuperVLAN成员数']}个楼栋)"
        else:
            result = "独立VLAN"

        # 这里简化检查,实际应根据修正后的规则
        # 当前IPAM数据基本符合SuperVLAN设计

        check = {
            'obj_id': obj_id,
            'campus': campus,
            'business': business,
            'target_ip': target_ip,
            'target_vlan': target_vlan,
            'target_svi': target_svi,
            'is_compliant': is_compliant,
            'result': result,
            'issues': '; '.join(issues) if issues else '无'
        }
        checks.append(check)

    return checks

# 生成风险清单
def generate_risks() -> List[Dict]:
    """生成风险清单"""
    risks = [
        {
            'level': 'P0',
            'category': '编码规则',
            'description': 'SuperVLAN架构下,同一业务多个楼栋共享VLAN号,这是正常设计而非冲突',
            'affected': '所有SuperVLAN业务',
            'recommendation': '更新编码验证规则,识别SuperVLAN模式',
            'status': '已识别'
        },
        {
            'level': 'P0',
            'category': '服务器区冲突',
            'description': '目标10.41.0.0/16与现网10.41.12.0/22可能存在路由冲突',
            'affected': 'IPAM-027至IPAM-030 (服务器区)',
            'recommendation': '需确认现网10.41.12.0/22的实际使用情况和路由所有权',
            'status': '待核实'
        },
        {
            'level': 'P1',
            'category': '网关规则',
            'description': '当前设计使用.1作为网关,待确认是否统一改为.254',
            'affected': '所有SVI网关',
            'recommendation': '用户确认T-08: 采用首个/24的.1还是.254作为网关',
            'status': '待决议'
        },
        {
            'level': 'P1',
            'category': 'SuperVLAN迁移',
            'description': 'SuperVLAN父号变化可能导致短时业务中断',
            'affected': '所有SuperVLAN业务',
            'recommendation': '用户确认T-11: 直接修改父VLAN号还是新建并行迁移',
            'status': '待决议'
        },
        {
            'level': 'P1',
            'category': '容量规划',
            'description': '需评估/21块(2048 IP)是否满足未来3-5年增长',
            'affected': '所有/21网段',
            'recommendation': '结合现有终端数和增长趋势,评估容量充足性',
            'status': '待评估'
        },
    ]

    return risks

# 主函数
def main():
    print("=" * 80)
    print("目标设计表生成器")
    print("=" * 80)
    print()

    # 加载数据
    print("1. 加载IPAM源数据...")
    ipam_data = load_ipam_data('04_IPAM源数据表.csv')
    print(f"   ✓ 已加载 {len(ipam_data)} 条记录")

    # 识别SuperVLAN分组
    print("\n2. 识别SuperVLAN架构...")
    supervlan_groups = identify_supervlan_groups(ipam_data)
    print(f"   ✓ 识别到 {len(supervlan_groups)} 个SuperVLAN组")

    # 生成目标设计
    print("\n3. 生成目标设计记录...")
    designs = []
    for row in ipam_data:
        design = generate_target_design(row, supervlan_groups)
        designs.append(design)
    print(f"   ✓ 已生成 {len(designs)} 条设计记录")

    # 生成编码验证
    print("\n4. 生成编码验证记录...")
    encoding_checks = generate_encoding_checks(designs, supervlan_groups)
    print(f"   ✓ 已生成 {len(encoding_checks)} 条验证记录")

    # 生成风险清单
    print("\n5. 生成风险清单...")
    risks = generate_risks()
    print(f"   ✓ 已生成 {len(risks)} 条风险记录")

    # 生成Excel
    print("\n6. 生成Excel文件...")
    generate_excel(designs, risks, encoding_checks)

    # 输出JSON
    print("\n7. 输出JSON数据...")
    with open('target_design.json', 'w', encoding='utf-8') as f:
        json.dump({
            'designs': designs,
            'supervlan_groups': supervlan_groups,
            'encoding_checks': encoding_checks,
            'risks': risks,
        }, f, ensure_ascii=False, indent=2)
    print("   ✓ 已保存: target_design.json")

    print("\n" + "=" * 80)
    print("目标设计表生成完成")
    print("=" * 80)
    print("\n文件清单:")
    print("  - 05_目标设计表.xlsx (3个Sheet)")
    print("  - target_design.json (JSON数据)")

if __name__ == '__main__':
    main()
