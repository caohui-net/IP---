#!/usr/bin/env python3
"""
改进基线表 - 提升DHCP匹配准确度和数据完整度
"""
import json
import pandas as pd
from pathlib import Path
import ipaddress

def ip_in_network(ip, network, mask):
    """检查IP是否在网络中"""
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        net_obj = ipaddress.IPv4Network(f"{network}/{mask}", strict=False)
        return ip_obj in net_obj
    except:
        return False

def find_matching_dhcp(svi_ip, svi_mask, dhcp_pools):
    """为SVI查找匹配的DHCP池"""
    if not svi_ip:
        return None

    # 方法1: 通过网关匹配
    for pool_name, pool_data in dhcp_pools.items():
        gateway = pool_data.get('gateway', '')
        if gateway == svi_ip:
            return pool_data

    # 方法2: 检查SVI是否在DHCP网络中
    for pool_name, pool_data in dhcp_pools.items():
        network = pool_data.get('network', '')
        mask = pool_data.get('mask', '')
        if network and mask:
            if ip_in_network(svi_ip, network, mask):
                return pool_data

    return None

def calculate_pool_range(network, mask):
    """计算DHCP池范围"""
    try:
        net = ipaddress.IPv4Network(f"{network}/{mask}", strict=False)
        # 排除网络地址和广播地址
        hosts = list(net.hosts())
        if len(hosts) > 0:
            # 通常排除最后一个作为网关
            return f"{hosts[0]} - {hosts[-2]}"
    except:
        pass
    return ''

def enhance_business_classification(vlan_name, vlan_id, svi_ip):
    """增强的业务分类"""
    name_lower = vlan_name.lower()

    # 教师办公
    if any(kw in name_lower for kw in ['teacher', 'faculty', '教师', 'staff', 'office', 'bangong', 'jiaoshi']):
        return '教师办公'

    # 学生宿舍
    if any(kw in name_lower for kw in ['student', '学生', 'dorm', 'sushe', 'xuesheng']):
        return '学生宿舍'

    # 访客/无线
    if any(kw in name_lower for kw in ['guest', 'visitor', '访客', 'wifi', 'wlan', 'fangke']):
        return '访客无线'

    # 设备管理
    if any(kw in name_lower for kw in ['管理', 'manage', 'admin', 'monitor', 'device', 'guanli', 'jiankong']):
        return '设备管理'

    # 服务器
    if any(kw in name_lower for kw in ['server', '服务器', 'data', 'fuwuqi']):
        return '服务器'

    # 物联网
    if any(kw in name_lower for kw in ['iot', '物联', 'sensor', 'camera', '监控', 'wulian']):
        return '物联网'

    # 根据IP段推断
    if svi_ip:
        parts = svi_ip.split('.')
        if len(parts) >= 2:
            second_octet = int(parts[1])
            # 基于常见的网段规划
            if 10 <= second_octet < 50:
                return '教师办公'
            elif 100 <= second_octet < 150:
                return '学生宿舍'
            elif 200 <= second_octet < 250:
                return '访客无线'

    # 根据VLAN ID推断
    if 100 <= vlan_id < 200:
        return '教师办公'
    elif 200 <= vlan_id < 300:
        return '学生宿舍'
    elif 300 <= vlan_id < 400:
        return '访客无线'
    elif vlan_id >= 1000:
        return '设备管理'

    return '其他'

def main():
    base_dir = Path('/home/caohui/projects/IP地址规划/交付成果_20260904')

    print("加载JSON数据...")
    all_campuses = json.load(open(base_dir / 'parsed_all_campuses.json'))

    all_rows = []
    obj_id = 1

    for campus_data in all_campuses:
        campus_name = campus_data.get('campus', 'Unknown')
        print(f"处理{campus_name}...")

        vlans = campus_data.get('vlans', {})
        svis = campus_data.get('svis', {})
        dhcp_pools = campus_data.get('dhcp_pools', {})

        # 建立VLAN到SVI的映射
        svi_by_vlan = {}
        for svi_id, svi_data in svis.items():
            vlan_id = svi_data.get('vlan', '')
            if vlan_id:
                svi_by_vlan[vlan_id] = svi_data

        # 遍历所有VLAN
        for vlan_id_str, vlan_data in vlans.items():
            try:
                vlan_id = int(vlan_id_str)
            except:
                continue

            vlan_name = vlan_data.get('name', '')

            # 获取SVI信息
            svi = svi_by_vlan.get(vlan_id_str, {})
            svi_ip = svi.get('ip', '')
            svi_mask = svi.get('mask', '')

            # CIDR转换
            mask_to_cidr = {
                '255.255.255.0': '24',
                '255.255.254.0': '23',
                '255.255.252.0': '22',
                '255.255.248.0': '21',
                '255.255.240.0': '20',
                '255.255.128.0': '17',
                '255.255.0.0': '16',
                '255.255.255.252': '30',
                '255.255.255.248': '29',
                '255.255.255.240': '28'
            }
            cidr = mask_to_cidr.get(svi_mask, '')

            # 查找匹配的DHCP池
            dhcp = find_matching_dhcp(svi_ip, svi_mask, dhcp_pools)
            dhcp_mode = 'none'
            dhcp_pool = ''
            dhcp_dns = ''

            if dhcp:
                dhcp_mode = 'server'
                network = dhcp.get('network', '')
                mask = dhcp.get('mask', '')
                if network and mask:
                    dhcp_pool = calculate_pool_range(network, mask)
                dns_list = dhcp.get('dns', [])
                if dns_list:
                    dhcp_dns = ', '.join(dns_list)

            # 业务分类
            business = enhance_business_classification(vlan_name, vlan_id, svi_ip)

            # IP前缀
            ip_prefix = ''
            if svi_ip and cidr:
                ip_prefix = f"{svi_ip}/{cidr}"
            elif svi_ip and svi_mask:
                ip_prefix = f"{svi_ip}/{svi_mask}"

            # 确认状态
            completeness = '✓ 完整'
            if not svi_ip:
                completeness = '⚠️ 部分'
            elif not dhcp_mode or dhcp_mode == 'none':
                completeness = '⚠️ 部分'

            # 数据来源
            source = f"VLAN配置行{vlan_data.get('source_line', 'N/A')}"
            if svi:
                source += f" + SVI配置行{svi.get('source_line', 'N/A')}"
            if dhcp:
                source += f" + DHCP配置行{dhcp.get('source_line', 'N/A')}"

            row = {
                '对象ID': f"B-{obj_id:03d}",
                '校区': campus_name,
                'VLAN编号': vlan_id,
                'VLAN名称': vlan_name,
                'IP前缀': ip_prefix,
                'SVI接口IP': svi_ip,
                '网关IP': svi_ip,
                'DHCP模式': dhcp_mode,
                'DHCP池范围': dhcp_pool,
                'DNS服务器': dhcp_dns,
                '业务分类': business,
                '接入设备类型': '',
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

            all_rows.append(row)
            obj_id += 1

    print(f"共提取 {len(all_rows)} 条基线记录")

    # 生成Excel
    df = pd.DataFrame(all_rows)
    output_file = base_dir / '02_现网事实基线表_改进版.xlsx'
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"✓ 生成改进版基线表: {output_file}")

    # 统计
    complete = len([r for r in all_rows if r['确认状态'] == '✓ 完整'])
    partial = len([r for r in all_rows if r['确认状态'] == '⚠️ 部分'])
    dhcp_enabled = len([r for r in all_rows if r['DHCP模式'] == 'server'])

    print(f"\n## 改进后数据质量")
    print(f"✓ 完整: {complete} ({complete/len(all_rows)*100:.1f}%)")
    print(f"⚠️ 部分: {partial} ({partial/len(all_rows)*100:.1f}%)")
    print(f"DHCP已配置: {dhcp_enabled} ({dhcp_enabled/len(all_rows)*100:.1f}%)")

    # 业务分类统计
    business_counts = df['业务分类'].value_counts()
    print(f"\n业务分类分布:")
    for business, count in business_counts.items():
        print(f"  {business}: {count}")

if __name__ == '__main__':
    main()
