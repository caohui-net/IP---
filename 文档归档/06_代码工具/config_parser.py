#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件结构化提取工具
从东、西、南三校区核心交换机配置文件提取关键信息
"""

import re
import json
from collections import defaultdict
from typing import Dict, List, Tuple

class ConfigParser:
    def __init__(self, config_file: str, campus: str):
        self.config_file = config_file
        self.campus = campus
        self.lines = []
        self.vlans = {}
        self.svis = {}
        self.dhcp_pools = {}
        self.dhcp_excluded = []
        self.routes = []
        self.ospf = {}
        self.address_manage = []
        self.interfaces = {}
        self.acls = {}
        self.ipv6_pools = {}

    def load_file(self):
        """加载配置文件"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()
        print(f"[{self.campus}] 已加载 {len(self.lines)} 行配置")

    def parse_vlans(self):
        """提取VLAN定义"""
        in_vlan_block = False
        current_vlan = None

        for i, line in enumerate(self.lines, start=1):
            line = line.strip()

            # 单独的VLAN定义块
            if line.startswith('vlan ') and not line.startswith('vlan range'):
                match = re.match(r'vlan (\d+)', line)
                if match:
                    vlan_id = match.group(1)
                    current_vlan = vlan_id
                    self.vlans[vlan_id] = {
                        'id': vlan_id,
                        'name': '',
                        'type': 'static',
                        'supervlan': False,
                        'subvlans': [],
                        'source_line': i,
                        'campus': self.campus
                    }
                    in_vlan_block = True

            # VLAN range定义
            elif line.startswith('vlan range'):
                match = re.match(r'vlan range (.+)', line)
                if match:
                    ranges = match.group(1)
                    # 解析VLAN范围
                    for part in ranges.split(','):
                        part = part.strip()
                        if '-' in part:
                            start, end = part.split('-')
                            for vid in range(int(start), int(end)+1):
                                if str(vid) not in self.vlans:
                                    self.vlans[str(vid)] = {
                                        'id': str(vid),
                                        'name': '',
                                        'type': 'static',
                                        'supervlan': False,
                                        'subvlans': [],
                                        'source_line': i,
                                        'campus': self.campus
                                    }
                        else:
                            if part not in self.vlans:
                                self.vlans[part] = {
                                    'id': part,
                                    'name': '',
                                    'type': 'static',
                                    'supervlan': False,
                                    'subvlans': [],
                                    'source_line': i,
                                    'campus': self.campus
                                }

            # VLAN name
            elif in_vlan_block and line.startswith('name '):
                match = re.match(r'name (.+)', line)
                if match and current_vlan:
                    self.vlans[current_vlan]['name'] = match.group(1)

            # SuperVLAN
            elif in_vlan_block and line == 'supervlan':
                if current_vlan:
                    self.vlans[current_vlan]['supervlan'] = True

            # SubVLAN
            elif in_vlan_block and line.startswith('subvlan '):
                match = re.match(r'subvlan (.+)', line)
                if match and current_vlan:
                    subvlans_str = match.group(1)
                    subvlans = []
                    for part in subvlans_str.split(','):
                        part = part.strip()
                        if '-' in part:
                            start, end = part.split('-')
                            subvlans.extend([str(x) for x in range(int(start), int(end)+1)])
                        else:
                            subvlans.append(part)
                    self.vlans[current_vlan]['subvlans'] = subvlans

            # 退出VLAN块
            elif in_vlan_block and (line.startswith('interface ') or line == '!' or line.startswith('vlan ')):
                in_vlan_block = False
                current_vlan = None

    def parse_svis(self):
        """提取SVI接口配置"""
        in_svi_block = False
        current_vlan = None

        for i, line in enumerate(self.lines, start=1):
            line = line.strip()

            if line.startswith('interface VLAN '):
                match = re.match(r'interface VLAN (\d+)', line)
                if match:
                    current_vlan = match.group(1)
                    self.svis[current_vlan] = {
                        'vlan': current_vlan,
                        'ip': '',
                        'mask': '',
                        'secondary_ips': [],
                        'ipv6': '',
                        'description': '',
                        'dhcp_server': False,
                        'source_line': i,
                        'campus': self.campus
                    }
                    in_svi_block = True

            elif in_svi_block and current_vlan:
                if line.startswith('description '):
                    match = re.match(r'description (.+)', line)
                    if match:
                        self.svis[current_vlan]['description'] = match.group(1)

                elif line.startswith('ip address '):
                    match = re.match(r'ip address ([\d.]+) ([\d.]+)( secondary)?', line)
                    if match:
                        ip = match.group(1)
                        mask = match.group(2)
                        is_secondary = match.group(3) is not None
                        if is_secondary:
                            self.svis[current_vlan]['secondary_ips'].append({'ip': ip, 'mask': mask})
                        else:
                            self.svis[current_vlan]['ip'] = ip
                            self.svis[current_vlan]['mask'] = mask

                elif line.startswith('ipv6 address '):
                    match = re.match(r'ipv6 address (.+)', line)
                    if match:
                        self.svis[current_vlan]['ipv6'] = match.group(1)

                elif line.startswith('ipv6 dhcp server'):
                    self.svis[current_vlan]['dhcp_server'] = True

                elif line.startswith('interface ') or (line == '!' and i < len(self.lines) and self.lines[i].strip().startswith('interface')):
                    in_svi_block = False
                    current_vlan = None

    def parse_dhcp_pools(self):
        """提取DHCP池配置"""
        in_pool_block = False
        current_pool = None

        for i, line in enumerate(self.lines, start=1):
            line = line.strip()

            if line.startswith('ip dhcp pool '):
                match = re.match(r'ip dhcp pool (.+)', line)
                if match:
                    current_pool = match.group(1)
                    self.dhcp_pools[current_pool] = {
                        'name': current_pool,
                        'network': '',
                        'mask': '',
                        'gateway': '',
                        'dns': [],
                        'lease': '',
                        'options': {},
                        'source_line': i,
                        'campus': self.campus
                    }
                    in_pool_block = True

            elif in_pool_block and current_pool:
                if line.startswith('network '):
                    match = re.match(r'network ([\d.]+) ([\d.]+)', line)
                    if match:
                        self.dhcp_pools[current_pool]['network'] = match.group(1)
                        self.dhcp_pools[current_pool]['mask'] = match.group(2)

                elif line.startswith('default-router '):
                    match = re.match(r'default-router ([\d.]+)', line)
                    if match:
                        self.dhcp_pools[current_pool]['gateway'] = match.group(1)

                elif line.startswith('dns-server '):
                    match = re.match(r'dns-server (.+)', line)
                    if match:
                        dns_list = match.group(1).split()
                        self.dhcp_pools[current_pool]['dns'] = dns_list

                elif line.startswith('lease '):
                    match = re.match(r'lease (.+)', line)
                    if match:
                        self.dhcp_pools[current_pool]['lease'] = match.group(1)

                elif line.startswith('option '):
                    match = re.match(r'option (\d+) ip ([\d.]+)', line)
                    if match:
                        option_code = match.group(1)
                        option_value = match.group(2)
                        self.dhcp_pools[current_pool]['options'][option_code] = option_value

                elif line.startswith('ip dhcp pool ') or line == '!':
                    in_pool_block = False
                    current_pool = None

        # 提取DHCP excluded地址
        for i, line in enumerate(self.lines, start=1):
            line = line.strip()
            if line.startswith('ip dhcp excluded-address '):
                match = re.match(r'ip dhcp excluded-address ([\d.]+)(?: ([\d.]+))?', line)
                if match:
                    start_ip = match.group(1)
                    end_ip = match.group(2) if match.group(2) else start_ip
                    self.dhcp_excluded.append({
                        'start': start_ip,
                        'end': end_ip,
                        'source_line': i,
                        'campus': self.campus
                    })

    def parse_address_manage(self):
        """提取address-manage策略"""
        in_addr_manage = False

        for i, line in enumerate(self.lines, start=1):
            line = line.strip()

            if line == 'address-manage':
                in_addr_manage = True
            elif in_addr_manage:
                if line.startswith('match ip '):
                    match = re.match(r'match ip ([\d.]+) ([\d.]+) (?:([\w/]+) )?vlan (\d+)', line)
                    if match:
                        self.address_manage.append({
                            'network': match.group(1),
                            'mask': match.group(2),
                            'interface': match.group(3) if match.group(3) else '',
                            'vlan': match.group(4),
                            'source_line': i,
                            'campus': self.campus
                        })
                elif line == '!' or not line.startswith('match'):
                    in_addr_manage = False

    def parse_routes(self):
        """提取静态路由"""
        for i, line in enumerate(self.lines, start=1):
            line = line.strip()

            if line.startswith('ip route '):
                match = re.match(r'ip route ([\d.]+) ([\d.]+) ([\d.]+)(?: (.+))?', line)
                if match:
                    self.routes.append({
                        'destination': match.group(1),
                        'mask': match.group(2),
                        'next_hop': match.group(3),
                        'description': match.group(4).replace('description ', '') if match.group(4) else '',
                        'source_line': i,
                        'campus': self.campus
                    })

    def parse_ospf(self):
        """提取OSPF配置"""
        in_ospf_block = False

        for i, line in enumerate(self.lines, start=1):
            line = line.strip()

            if line.startswith('router ospf '):
                match = re.match(r'router ospf (\d+)', line)
                if match:
                    process_id = match.group(1)
                    self.ospf = {
                        'process_id': process_id,
                        'networks': [],
                        'passive_interfaces': [],
                        'redistribute': [],
                        'source_line': i,
                        'campus': self.campus
                    }
                    in_ospf_block = True

            elif in_ospf_block:
                if line.startswith('network '):
                    match = re.match(r'network ([\d.]+) ([\d.]+) area ([\d.]+)', line)
                    if match:
                        self.ospf['networks'].append({
                            'network': match.group(1),
                            'wildcard': match.group(2),
                            'area': match.group(3)
                        })

                elif line.startswith('passive-interface '):
                    match = re.match(r'passive-interface (.+)', line)
                    if match:
                        self.ospf['passive_interfaces'].append(match.group(1))

                elif line.startswith('redistribute '):
                    match = re.match(r'redistribute (.+)', line)
                    if match:
                        self.ospf['redistribute'].append(match.group(1))

                elif line == '!' or line.startswith('switch ') or line.startswith('ipv6 '):
                    in_ospf_block = False

    def parse_all(self):
        """执行所有解析"""
        print(f"\n=== 开始解析 {self.campus}校区配置 ===")
        self.load_file()
        self.parse_vlans()
        print(f"  提取VLAN: {len(self.vlans)} 个")
        self.parse_svis()
        print(f"  提取SVI: {len(self.svis)} 个")
        self.parse_dhcp_pools()
        print(f"  提取DHCP池: {len(self.dhcp_pools)} 个")
        print(f"  提取DHCP排除地址: {len(self.dhcp_excluded)} 条")
        self.parse_address_manage()
        print(f"  提取address-manage: {len(self.address_manage)} 条")
        self.parse_routes()
        print(f"  提取静态路由: {len(self.routes)} 条")
        self.parse_ospf()
        if self.ospf:
            print(f"  提取OSPF进程: {self.ospf.get('process_id', 'N/A')}")

    def export_json(self, output_file: str):
        """导出为JSON"""
        data = {
            'campus': self.campus,
            'vlans': self.vlans,
            'svis': self.svis,
            'dhcp_pools': self.dhcp_pools,
            'dhcp_excluded': self.dhcp_excluded,
            'address_manage': self.address_manage,
            'routes': self.routes,
            'ospf': self.ospf
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[{self.campus}] 已导出至 {output_file}")


def main():
    """主函数"""
    base_dir = '/home/caohui/projects/IP地址规划'
    configs = [
        (f'{base_dir}/原始文档/东校区核心_纯净配置_20260824.txt', '东校区'),
        (f'{base_dir}/原始文档/西校区核心_纯净配置_20260824.txt', '西校区'),
        (f'{base_dir}/原始文档/南校区核心_纯净配置_20260824.txt', '南校区')
    ]

    all_data = []

    for config_file, campus in configs:
        parser = ConfigParser(config_file, campus)
        parser.parse_all()
        output_file = f'{base_dir}/交付成果_20260904/parsed_{campus}.json'
        parser.export_json(output_file)
        all_data.append({
            'campus': campus,
            'vlans': parser.vlans,
            'svis': parser.svis,
            'dhcp_pools': parser.dhcp_pools,
            'dhcp_excluded': parser.dhcp_excluded,
            'address_manage': parser.address_manage,
            'routes': parser.routes,
            'ospf': parser.ospf
        })

    # 合并输出
    merged_file = f'{base_dir}/交付成果_20260904/parsed_all_campuses.json'
    with open(merged_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"\n合并数据已导出至 {merged_file}")

    print("\n=== 配置解析完成 ===")


if __name__ == '__main__':
    main()
