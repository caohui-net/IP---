#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现网事实基线表生成器
基于配置解析结果生成完整的基线矩阵
"""

import json
import csv
import ipaddress
from typing import Dict, List, Tuple
from datetime import datetime

class BaselineGenerator:
    def __init__(self, parsed_data_file: str):
        self.parsed_data_file = parsed_data_file
        self.all_data = []
        self.baseline_records = []
        self.issues = {'P0': [], 'P1': [], 'P2': []}

    def load_data(self):
        """加载解析后的配置数据"""
        with open(self.parsed_data_file, 'r', encoding='utf-8') as f:
            self.all_data = json.load(f)
        print(f"已加载 {len(self.all_data)} 个校区的数据")

    def ip_to_network(self, ip: str, mask: str) -> str:
        """将IP地址和掩码转换为网络前缀"""
        try:
            network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
            return str(network)
        except:
            return f"{ip}/{mask}"

    def mask_to_cidr(self, mask: str) -> int:
        """将掩码转换为CIDR前缀长度"""
        try:
            return ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
        except:
            return 0

    def find_dhcp_pool_for_vlan(self, campus_data: Dict, vlan_id: str) -> Dict:
        """为指定VLAN查找对应的DHCP池"""
        # 先通过VLAN名称匹配
        vlan_info = campus_data['vlans'].get(vlan_id, {})
        vlan_name = vlan_info.get('name', '').lower()

        for pool_name, pool in campus_data['dhcp_pools'].items():
            if vlan_id in pool_name or vlan_name in pool_name.lower():
                return pool

        # 通过SVI的IP网段匹配
        svi = campus_data['svis'].get(vlan_id)
        if svi and svi.get('ip'):
            svi_network = self.ip_to_network(svi['ip'], svi['mask'])
            for pool_name, pool in campus_data['dhcp_pools'].items():
                if pool.get('network'):
                    pool_network = self.ip_to_network(pool['network'], pool['mask'])
                    if svi_network == pool_network:
                        return pool

        return {}

    def detect_ip_overlaps(self):
        """检测IP地址重叠"""
        all_networks = {}

        for campus_data in self.all_data:
            campus = campus_data['campus']
            for vlan_id, svi in campus_data['svis'].items():
                if svi.get('ip') and svi.get('mask'):
                    network_str = self.ip_to_network(svi['ip'], svi['mask'])
                    if network_str not in all_networks:
                        all_networks[network_str] = []
                    all_networks[network_str].append({
                        'campus': campus,
                        'vlan': vlan_id,
                        'svi_ip': svi['ip'],
                        'line': svi['source_line']
                    })

        # 检查重叠
        for network, locations in all_networks.items():
            if len(locations) > 1:
                campuses = [loc['campus'] for loc in locations]
                vlans = [f"VLAN{loc['vlan']}" for loc in locations]
                self.issues['P0'].append({
                    'type': 'IP地址重叠',
                    'severity': 'P0',
                    'description': f"网段 {network} 在多个位置声明",
                    'affected': f"{', '.join(campuses)} - {', '.join(vlans)}",
                    'evidence': f"配置行号: {', '.join([str(loc['line']) for loc in locations])}",
                    'impact': '可能导致路由冲突和流量黑洞',
                    'recommendation': '重新规划IP地址，确保每个网段只在一个位置使用'
                })

    def detect_vlan_duplicates(self):
        """检测VLAN编号重复"""
        vlan_usage = {}

        for campus_data in self.all_data:
            campus = campus_data['campus']
            for vlan_id, vlan in campus_data['vlans'].items():
                if vlan_id not in vlan_usage:
                    vlan_usage[vlan_id] = []
                vlan_usage[vlan_id].append({
                    'campus': campus,
                    'name': vlan.get('name', ''),
                    'line': vlan['source_line']
                })

        # VLAN跨校区使用是正常的，但同一VLAN在不同校区有不同名称是问题
        for vlan_id, locations in vlan_usage.items():
            if len(locations) > 1:
                names = set([loc['name'] for loc in locations if loc['name']])
                if len(names) > 1:
                    self.issues['P1'].append({
                        'type': 'VLAN命名不一致',
                        'severity': 'P1',
                        'description': f"VLAN {vlan_id} 在不同校区有不同名称",
                        'affected': f"名称: {', '.join(names)}",
                        'evidence': f"校区: {', '.join([loc['campus'] for loc in locations])}",
                        'impact': '可能导致运维混淆',
                        'recommendation': '统一VLAN命名规范'
                    })

    def detect_dhcp_issues(self, campus_data: Dict, vlan_id: str, svi: Dict, dhcp_pool: Dict) -> List[str]:
        """检测DHCP配置问题"""
        problems = []

        # 检查网关是否与SVI一致
        if dhcp_pool.get('gateway'):
            if dhcp_pool['gateway'] != svi.get('ip'):
                problems.append(f"DHCP网关({dhcp_pool['gateway']})与SVI IP({svi.get('ip')})不一致")
        else:
            if svi.get('ip'):
                problems.append("DHCP池缺少网关配置")

        # 检查DHCP网络与SVI是否匹配
        if dhcp_pool.get('network') and svi.get('ip'):
            pool_net = self.ip_to_network(dhcp_pool['network'], dhcp_pool['mask'])
            svi_net = self.ip_to_network(svi['ip'], svi['mask'])
            if pool_net != svi_net:
                problems.append(f"DHCP网络({pool_net})与SVI网络({svi_net})不匹配")

        return problems

    def generate_baseline_records(self):
        """生成基线记录"""
        record_id = 1

        for campus_data in self.all_data:
            campus = campus_data['campus']
            print(f"\n处理 {campus}...")

            # 处理每个有SVI的VLAN
            for vlan_id, svi in campus_data['svis'].items():
                vlan_info = campus_data['vlans'].get(vlan_id, {})
                dhcp_pool = self.find_dhcp_pool_for_vlan(campus_data, vlan_id)

                # 检测DHCP问题
                dhcp_issues = self.detect_dhcp_issues(campus_data, vlan_id, svi, dhcp_pool)
                for issue in dhcp_issues:
                    self.issues['P1'].append({
                        'type': 'DHCP配置问题',
                        'severity': 'P1',
                        'description': issue,
                        'affected': f"{campus} VLAN{vlan_id}",
                        'evidence': f"SVI行号:{svi['source_line']}, DHCP池:{dhcp_pool.get('source_line', 'N/A')}",
                        'impact': '可能导致终端无法获取正确IP或网关',
                        'recommendation': '修正DHCP配置使其与SVI一致'
                    })

                # 确定网络前缀
                if svi.get('ip') and svi.get('mask'):
                    network = self.ip_to_network(svi['ip'], svi['mask'])
                    cidr = self.mask_to_cidr(svi['mask'])
                else:
                    network = ""
                    cidr = 0

                # 确定DHCP模式
                if dhcp_pool:
                    dhcp_mode = "server"
                    dhcp_range = f"{dhcp_pool.get('network', '')} - (动态分配)"
                elif svi.get('dhcp_server'):
                    dhcp_mode = "relay"
                    dhcp_range = ""
                else:
                    dhcp_mode = "none"
                    dhcp_range = ""

                # 查找address-manage条目
                related_addr_manage = []
                for am in campus_data.get('address_manage', []):
                    if am['vlan'] == vlan_id:
                        related_addr_manage.append(am['interface'] if am['interface'] else 'local')

                # 确定业务分类
                vlan_name = vlan_info.get('name', '').lower()
                business_type = self.classify_business(vlan_name, vlan_id)

                # 数据完整度标记
                completeness = self.assess_completeness(svi, dhcp_pool, vlan_info)

                record = {
                    'ID': record_id,
                    '校区': campus,
                    'VLAN编号': vlan_id,
                    'VLAN名称': vlan_info.get('name', ''),
                    'IP前缀': network,
                    'CIDR': f"/{cidr}" if cidr > 0 else "",
                    'SVI接口IP': svi.get('ip', ''),
                    '网关IP': dhcp_pool.get('gateway', svi.get('ip', '')),
                    'DHCP模式': dhcp_mode,
                    'DHCP池范围': dhcp_range,
                    'DNS服务器': ', '.join(dhcp_pool.get('dns', [])),
                    '接入设备': ', '.join(related_addr_manage) if related_addr_manage else '',
                    '认证方式': self.detect_auth_method(campus_data, vlan_id),
                    '业务分类': business_type,
                    'IPv6地址': svi.get('ipv6', ''),
                    '描述': svi.get('description', ''),
                    'SuperVLAN': 'Yes' if vlan_info.get('supervlan') else 'No',
                    'SubVLANs': ','.join(vlan_info.get('subvlans', [])),
                    '数据来源': f"配置文件行{svi['source_line']}",
                    '采集日期': '2026-08-24',
                    '数据完整度': completeness,
                    '问题标记': '; '.join(dhcp_issues) if dhcp_issues else ''
                }

                self.baseline_records.append(record)
                record_id += 1

            print(f"  {campus}: 生成 {len([r for r in self.baseline_records if r['校区'] == campus])} 条记录")

    def classify_business(self, vlan_name: str, vlan_id: str) -> str:
        """根据VLAN名称和编号分类业务"""
        # 教师/办公
        if any(k in vlan_name for k in ['bangong', '办公', 'teacher', 'staff', 'weisheng', '卫生', 'caiwu', '财务', 'gongwen', '公文']):
            return '教师办公'

        # 学生
        if any(k in vlan_name for k in ['student', 'xsgy', '学生', 'wuxian', '无线']):
            return '学生网络'

        # 管理
        if any(k in vlan_name for k in ['guanli', '管理', 'ap-guanli', 'ap_guanli']):
            return '设备管理'

        # 宿舍
        if any(k in vlan_name for k in ['sushe', '宿舍', 'dorm']):
            return '学生宿舍'

        # 机房/服务器
        if any(k in vlan_name for k in ['jifang', '机房', 'server', 'dmz']):
            return '数据中心'

        # 监控
        if any(k in vlan_name for k in ['jiankong', '监控', 'monitor', 'camera']):
            return '安防监控'

        # 门禁/一卡通
        if any(k in vlan_name for k in ['menjing', '门禁', 'mensuo', '门锁', 'yikatong', '一卡通', 'renlian', '人脸']):
            return '一卡通/门禁'

        # 其他基础设施
        if any(k in vlan_name for k in ['link', 'uplink', 'guanli', 'management']):
            return '网络互联'

        # 按VLAN编号段分类
        vid = int(vlan_id)
        if 101 <= vid <= 199:
            return '教学区域'
        elif 201 <= vid <= 299:
            return '办公区域'
        elif 300 <= vid <= 499:
            return '学生宿舍'
        elif 1001 <= vid <= 1999:
            return '设备管理'

        return '其他'

    def detect_auth_method(self, campus_data: Dict, vlan_id: str) -> str:
        """检测认证方式（从配置推断）"""
        # 这里简化处理，实际需要检查接口配置中的dot1x、web-auth等
        # 由于配置解析器未提取接口级别的认证配置，这里返回通用值
        return '待确认'

    def assess_completeness(self, svi: Dict, dhcp_pool: Dict, vlan_info: Dict) -> str:
        """评估数据完整度"""
        score = 0
        total = 5

        if svi.get('ip'):
            score += 1
        if svi.get('description'):
            score += 1
        if dhcp_pool:
            score += 1
        if vlan_info.get('name'):
            score += 1
        if svi.get('ipv6'):
            score += 1

        percentage = (score / total) * 100

        if percentage >= 80:
            return '✓ 完整'
        elif percentage >= 50:
            return '⚠️ 部分'
        else:
            return '✗ 不完整'

    def export_baseline_csv(self, output_file: str):
        """导出基线表为CSV"""
        if not self.baseline_records:
            print("没有基线记录可导出")
            return

        fieldnames = [
            'ID', '校区', 'VLAN编号', 'VLAN名称', 'IP前缀', 'CIDR',
            'SVI接口IP', '网关IP', 'DHCP模式', 'DHCP池范围', 'DNS服务器',
            '接入设备', '认证方式', '业务分类', 'IPv6地址', '描述',
            'SuperVLAN', 'SubVLANs', '数据来源', '采集日期',
            '数据完整度', '问题标记'
        ]

        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.baseline_records)

        print(f"\n基线表已导出: {output_file}")
        print(f"  总记录数: {len(self.baseline_records)}")

        # 统计
        by_campus = {}
        by_business = {}
        for record in self.baseline_records:
            campus = record['校区']
            business = record['业务分类']
            by_campus[campus] = by_campus.get(campus, 0) + 1
            by_business[business] = by_business.get(business, 0) + 1

        print(f"\n按校区统计:")
        for campus, count in sorted(by_campus.items()):
            print(f"  {campus}: {count} 条")

        print(f"\n按业务分类统计:")
        for business, count in sorted(by_business.items(), key=lambda x: x[1], reverse=True):
            print(f"  {business}: {count} 条")

    def export_issues_markdown(self, output_file: str):
        """导出问题清单为Markdown"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 现网问题清单\n\n")
            f.write(f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**数据来源:** 三校区核心交换机配置（2026-08-24采集）\n\n")

            for severity in ['P0', 'P1', 'P2']:
                issues = self.issues[severity]
                if not issues:
                    continue

                severity_name = {
                    'P0': '高风险问题（影响可用性）',
                    'P1': '中风险问题（功能问题）',
                    'P2': '低风险问题（规范性问题）'
                }

                f.write(f"## {severity}: {severity_name[severity]}\n\n")
                f.write(f"**问题数量:** {len(issues)}\n\n")

                for i, issue in enumerate(issues, 1):
                    f.write(f"### {severity}-{i:03d}: {issue['description']}\n\n")
                    f.write(f"**类型:** {issue['type']}\n\n")
                    f.write(f"**影响范围:** {issue['affected']}\n\n")
                    f.write(f"**证据:** {issue['evidence']}\n\n")
                    f.write(f"**影响:** {issue['impact']}\n\n")
                    f.write(f"**建议:** {issue['recommendation']}\n\n")
                    f.write("---\n\n")

        print(f"\n问题清单已导出: {output_file}")
        for severity, issues in self.issues.items():
            print(f"  {severity}: {len(issues)} 个问题")

    def generate_quality_report(self, output_file: str):
        """生成数据质量报告"""
        total_records = len(self.baseline_records)

        # 统计完整度
        completeness_stats = {'✓ 完整': 0, '⚠️ 部分': 0, '✗ 不完整': 0}
        for record in self.baseline_records:
            comp = record['数据完整度']
            completeness_stats[comp] = completeness_stats.get(comp, 0) + 1

        # 统计缺失字段
        missing_fields = {}
        for record in self.baseline_records:
            for field in ['IPv6地址', '描述', 'DNS服务器', '接入设备']:
                if not record.get(field):
                    missing_fields[field] = missing_fields.get(field, 0) + 1

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 数据质量报告\n\n")
            f.write(f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## 整体完整度\n\n")
            f.write(f"- 总记录数: {total_records}\n")
            for comp, count in completeness_stats.items():
                pct = (count / total_records * 100) if total_records > 0 else 0
                f.write(f"- {comp}: {count} 条 ({pct:.1f}%)\n")

            overall_completeness = completeness_stats.get('✓ 完整', 0) / total_records * 100 if total_records > 0 else 0
            f.write(f"\n**整体完整度: {overall_completeness:.1f}%**\n\n")

            f.write("## 缺失字段统计\n\n")
            for field, count in sorted(missing_fields.items(), key=lambda x: x[1], reverse=True):
                pct = (count / total_records * 100) if total_records > 0 else 0
                f.write(f"- {field}: {count} 条缺失 ({pct:.1f}%)\n")

            f.write("\n## 需要补充的信息\n\n")
            f.write("### 现场确认项\n\n")
            f.write("1. **认证方式**: 所有记录标记为'待确认'，需现场验证dot1x、portal等认证配置\n")
            f.write("2. **实际在线设备**: MobaXterm文件未包含MAC表、ARP表，无法确认实际在线情况\n")
            f.write("3. **接口状态**: 需要通过`show interface status`确认UP/DOWN状态\n")
            f.write("4. **DHCP租约**: 需要通过`show ip dhcp binding`确认实际分配情况\n\n")

            f.write("### 建议补充采集的数据\n\n")
            f.write("```\n")
            f.write("show mac address-table count\n")
            f.write("show ip arp summary\n")
            f.write("show ip dhcp binding\n")
            f.write("show interface status\n")
            f.write("show spanning-tree summary\n")
            f.write("show ip ospf neighbor\n")
            f.write("```\n")

        print(f"\n数据质量报告已导出: {output_file}")

    def run(self):
        """执行完整流程"""
        print("=== 开始生成现网事实基线 ===\n")
        self.load_data()

        print("\n检测问题...")
        self.detect_ip_overlaps()
        self.detect_vlan_duplicates()

        print("\n生成基线记录...")
        self.generate_baseline_records()

        base_dir = '/home/caohui/projects/IP地址规划/交付成果_20260904'

        self.export_baseline_csv(f'{base_dir}/01_现网事实基线表.csv')
        self.export_issues_markdown(f'{base_dir}/02_现网问题清单_P0_P1_P2.md')
        self.generate_quality_report(f'{base_dir}/baseline_quality_report.md')

        print("\n=== 基线生成完成 ===")


def main():
    generator = BaselineGenerator('/home/caohui/projects/IP地址规划/交付成果_20260904/parsed_all_campuses.json')
    generator.run()


if __name__ == '__main__':
    main()
