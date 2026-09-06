#!/usr/bin/env python3
"""
IP/VLAN冲突检查和容量评估
"""

import json
import ipaddress
from collections import defaultdict

def load_target_design():
    """加载目标设计数据"""
    with open('target_design.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def check_ip_conflicts(designs):
    """检查IP前缀冲突"""
    conflicts = []
    ip_map = defaultdict(list)

    # 收集所有IP前缀
    for design in designs:
        ip_prefix = design['目标IP前缀']
        obj_id = design['对象ID']

        try:
            network = ipaddress.ip_network(ip_prefix, strict=False)
            ip_map[str(network)].append(obj_id)
        except:
            conflicts.append({
                'type': 'IP格式错误',
                'obj_id': obj_id,
                'detail': f"无效的IP前缀: {ip_prefix}"
            })

    # 检查重叠
    networks = [(ipaddress.ip_network(ip, strict=False), objs)
                for ip, objs in ip_map.items()]

    for i, (net1, objs1) in enumerate(networks):
        for net2, objs2 in networks[i+1:]:
            if net1.overlaps(net2):
                conflicts.append({
                    'type': 'IP重叠',
                    'network1': str(net1),
                    'objects1': objs1,
                    'network2': str(net2),
                    'objects2': objs2,
                    'detail': f"{net1} 与 {net2} 存在重叠"
                })

    return conflicts

def check_vlan_conflicts(designs, supervlan_groups):
    """检查VLAN冲突 (排除SuperVLAN正常共享)"""
    conflicts = []
    vlan_map = defaultdict(list)

    for design in designs:
        vlan = design['目标VLAN']
        obj_id = design['对象ID']
        campus = design['校区']
        business = design['业务分类']
        svi = design['目标SVI']

        key = f"{campus}-{business}-{vlan}-{svi}"
        is_supervlan = key in supervlan_groups

        vlan_map[vlan].append({
            'obj_id': obj_id,
            'campus': campus,
            'business': business,
            'is_supervlan': is_supervlan,
            'supervlan_key': key if is_supervlan else None
        })

    # 检查真正的冲突 (非SuperVLAN共享)
    for vlan, objects in vlan_map.items():
        if len(objects) > 1:
            # 检查是否属于同一个SuperVLAN组
            supervlan_keys = set(obj['supervlan_key'] for obj in objects
                                if obj['supervlan_key'])

            if len(supervlan_keys) <= 1:
                # 同一个SuperVLAN组, 这是正常的
                continue

            # 不同SuperVLAN组或混合使用, 这是真正的冲突
            conflicts.append({
                'type': 'VLAN真实冲突',
                'vlan': vlan,
                'objects': [obj['obj_id'] for obj in objects],
                'campuses': list(set(obj['campus'] for obj in objects)),
                'businesses': list(set(obj['business'] for obj in objects)),
                'detail': f"VLAN {vlan} 被 {len(objects)} 个不同业务/校区使用"
            })

    return conflicts

def check_vlan_range(designs):
    """检查VLAN合法性"""
    issues = []

    for design in designs:
        vlan = int(design['目标VLAN'])
        obj_id = design['对象ID']

        if vlan < 1 or vlan > 4094:
            issues.append({
                'type': 'VLAN范围错误',
                'obj_id': obj_id,
                'vlan': vlan,
                'detail': f"VLAN {vlan} 不在合法范围 [1-4094]"
            })

    return issues

def check_capacity(designs):
    """检查容量充足性"""
    issues = []

    # 容量阈值 (根据业务类型)
    capacity_thresholds = {
        '教师有线': 500,    # 教师数量较少
        '教师无线': 800,    # 教师+办公设备
        '学生有线': 1500,   # 学生宿舍密集
        '学生无线': 2000,   # 学生移动设备多
        '访客无线': 500,    # 访客数量
        '设备管理': 200,    # 网络设备
        'Web服务器': 50,
        '数据库服务器': 50,
        '应用服务器': 100,
        '存储服务器': 50,
        '监控摄像头': 500,
        '门禁系统': 300,
        '环境监测': 200,
        '智能照明': 500,
        '消防系统': 300,
    }

    for design in designs:
        obj_id = design['对象ID']
        business = design['业务分类']
        usable_ips = design['可用IP数']
        dhcp_pool_size = design['DHCP池大小']

        # 获取容量阈值
        threshold = capacity_thresholds.get(business, 500)

        # 评估: 需要当前容量 + 3-5年增长(50%-100%)
        required_capacity = threshold * 1.5  # 50%增长

        if usable_ips < required_capacity:
            issues.append({
                'type': '容量可能不足',
                'obj_id': obj_id,
                'business': business,
                'usable_ips': usable_ips,
                'dhcp_pool_size': dhcp_pool_size,
                'threshold': threshold,
                'required': int(required_capacity),
                'detail': f"{business} 可用IP={usable_ips}, 建议≥{int(required_capacity)}"
            })
        elif usable_ips < threshold * 2:
            issues.append({
                'type': '容量预留偏紧',
                'obj_id': obj_id,
                'business': business,
                'usable_ips': usable_ips,
                'threshold': threshold,
                'required': int(threshold * 2),
                'detail': f"{business} 可用IP={usable_ips}, 5年增长空间偏紧"
            })

    return issues

def check_server_conflicts(designs):
    """检查服务器区地址冲突"""
    issues = []

    # 服务器区目标: 10.41.0.0/16
    server_designs = [d for d in designs if d['校区'] == '服务器区']

    if server_designs:
        issues.append({
            'type': '服务器区潜在冲突',
            'affected': [d['对象ID'] for d in server_designs],
            'target_range': '10.41.0.0/16',
            'conflict_with': '现网10.41.12.0/22 (需现场核实)',
            'detail': '目标服务器区10.41.0.0/16与现网10.41.12.0/22可能存在路由所有权冲突',
            'recommendation': '需确认现网10.41.12.0/22的实际使用情况、路由发布和防火墙规则'
        })

    return issues

def generate_report(data, ip_conflicts, vlan_conflicts, vlan_range_issues,
                   capacity_issues, server_conflicts):
    """生成冲突和容量检查报告"""
    print("=" * 80)
    print("IP/VLAN冲突和容量评估报告")
    print("=" * 80)
    print()

    # 统计
    total_designs = len(data['designs'])
    total_issues = (len(ip_conflicts) + len(vlan_conflicts) +
                   len(vlan_range_issues) + len(capacity_issues) +
                   len(server_conflicts))

    print(f"目标设计记录数: {total_designs}")
    print(f"SuperVLAN组数: {len(data['supervlan_groups'])}")
    print(f"发现问题数: {total_issues}")
    print()

    # IP冲突
    print("-" * 80)
    print(f"1. IP前缀冲突检查: {len(ip_conflicts)} 个问题")
    print("-" * 80)
    if ip_conflicts:
        for conflict in ip_conflicts:
            print(f"\n[{conflict['type']}]")
            if 'network1' in conflict:
                print(f"  网段1: {conflict['network1']} ({', '.join(conflict['objects1'])})")
                print(f"  网段2: {conflict['network2']} ({', '.join(conflict['objects2'])})")
            print(f"  详情: {conflict['detail']}")
    else:
        print("✓ 无IP前缀冲突")

    # VLAN冲突
    print("\n" + "-" * 80)
    print(f"2. VLAN真实冲突检查: {len(vlan_conflicts)} 个问题")
    print("-" * 80)
    if vlan_conflicts:
        for conflict in vlan_conflicts:
            print(f"\n[VLAN {conflict['vlan']}]")
            print(f"  冲突对象: {', '.join(conflict['objects'])}")
            print(f"  涉及校区: {', '.join(conflict['campuses'])}")
            print(f"  涉及业务: {', '.join(conflict['businesses'])}")
            print(f"  详情: {conflict['detail']}")
    else:
        print("✓ 无VLAN真实冲突 (SuperVLAN共享是正常设计)")

    # VLAN范围
    print("\n" + "-" * 80)
    print(f"3. VLAN合法性检查: {len(vlan_range_issues)} 个问题")
    print("-" * 80)
    if vlan_range_issues:
        for issue in vlan_range_issues:
            print(f"\n[{issue['obj_id']}]")
            print(f"  VLAN: {issue['vlan']}")
            print(f"  详情: {issue['detail']}")
    else:
        print("✓ 所有VLAN在合法范围内")

    # 容量评估
    print("\n" + "-" * 80)
    print(f"4. 容量充足性评估: {len(capacity_issues)} 个问题")
    print("-" * 80)
    if capacity_issues:
        insufficient = [i for i in capacity_issues if i['type'] == '容量可能不足']
        tight = [i for i in capacity_issues if i['type'] == '容量预留偏紧']

        print(f"\n容量不足 ({len(insufficient)} 个):")
        for issue in insufficient:
            print(f"  [{issue['obj_id']}] {issue['business']}: "
                  f"可用{issue['usable_ips']}, 建议≥{issue['required']}")

        print(f"\n容量偏紧 ({len(tight)} 个):")
        for issue in tight[:5]:  # 只显示前5个
            print(f"  [{issue['obj_id']}] {issue['business']}: "
                  f"可用{issue['usable_ips']}, 建议≥{issue['required']}")
        if len(tight) > 5:
            print(f"  ... 还有 {len(tight) - 5} 个")
    else:
        print("✓ 所有网段容量充足")

    # 服务器区冲突
    print("\n" + "-" * 80)
    print(f"5. 服务器区地址冲突: {len(server_conflicts)} 个问题")
    print("-" * 80)
    if server_conflicts:
        for conflict in server_conflicts:
            print(f"\n[{conflict['type']}]")
            print(f"  影响对象: {', '.join(conflict['affected'])}")
            print(f"  目标范围: {conflict['target_range']}")
            print(f"  冲突对象: {conflict['conflict_with']}")
            print(f"  详情: {conflict['detail']}")
            print(f"  建议: {conflict['recommendation']}")
    else:
        print("✓ 无明显服务器区冲突")

    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)

    # 汇总
    summary = {
        'total_designs': total_designs,
        'total_issues': total_issues,
        'ip_conflicts': ip_conflicts,
        'vlan_conflicts': vlan_conflicts,
        'vlan_range_issues': vlan_range_issues,
        'capacity_issues': capacity_issues,
        'server_conflicts': server_conflicts,
    }

    return summary

def main():
    # 加载数据
    print("加载目标设计数据...")
    data = load_target_design()
    designs = data['designs']
    supervlan_groups = data['supervlan_groups']

    # 执行检查
    print("执行冲突和容量检查...")
    print()

    ip_conflicts = check_ip_conflicts(designs)
    vlan_conflicts = check_vlan_conflicts(designs, supervlan_groups)
    vlan_range_issues = check_vlan_range(designs)
    capacity_issues = check_capacity(designs)
    server_conflicts = check_server_conflicts(designs)

    # 生成报告
    summary = generate_report(data, ip_conflicts, vlan_conflicts,
                            vlan_range_issues, capacity_issues, server_conflicts)

    # 保存结果
    with open('conflict_capacity_check.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n详细结果已保存到: conflict_capacity_check.json")

if __name__ == '__main__':
    main()
