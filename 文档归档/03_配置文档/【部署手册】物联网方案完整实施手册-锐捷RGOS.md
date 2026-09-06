# 物联网方案 - 完整部署实施手册（锐捷RGOS）

**文档版本**: v2.0  
**生成时间**: 2026-09-06 07:30 UTC  
**适用设备**: 锐捷交换机（RGOS系统）  
**配置规模**: 18个VLAN完整部署  
**预计时间**: 实验2小时 + 生产8小时

---

## 📋 部署总览

### 部署策略

**分阶段部署**: 实验 → 试点 → 全面推广  
**风险控制**: 每阶段设置兜底检查点  
**回滚准备**: 每步骤配备回滚脚本  
**时间窗口**: 周末凌晨02:00-06:00（低峰期）

### 部署顺序

```
阶段0: 准备工作（1小时）
  ├─ 备份当前配置
  ├─ 验证设备状态
  └─ 准备回滚脚本

阶段1: 实验验证（2小时）- 测试环境
  ├─ 部署东校区1个业务VLAN
  ├─ 连接测试设备
  └─ 验收通过后进入阶段2

阶段2: 试点部署（4小时）- 生产环境
  ├─ 部署东校区6个VLAN
  ├─ 连接少量真实设备
  ├─ 观察24小时
  └─ 验收通过后进入阶段3

阶段3: 全面推广（8小时）- 生产环境
  ├─ 部署西校区6个VLAN（2小时）
  ├─ 部署南校区6个VLAN（2小时）
  ├─ 批量连接物联网设备（2小时）
  └─ 48小时稳定性观察
```

---

## 🔧 阶段0: 准备工作

### 0.1 登录锐捷交换机

```bash
# SSH登录（推荐）
ssh admin@<交换机IP>

# 或Telnet登录
telnet <交换机IP>

# 进入特权模式
enable
<输入enable密码>

# 进入配置模式
configure terminal
```

### 0.2 备份当前配置

```bash
# 方式1: 保存到本地Flash（推荐）
copy running-config flash:backup-before-iot-20260906.cfg

# 方式2: 保存到TFTP服务器
copy running-config tftp://10.254.0.100/backup-before-iot-20260906.cfg

# 方式3: 直接显示并手工保存
show running-config

# 验证备份文件
dir flash:
# 或
show flash:

# 预期结果：看到backup文件
```

**兜底检查点0.2**:
```bash
# 确认备份成功
dir flash: | include backup-before-iot

# 如果未看到文件，重新执行备份
# 如果仍失败，停止部署，排查存储问题
```

### 0.3 验证设备状态

```bash
# 检查CPU使用率（应<50%）
show cpu usage

# 检查内存使用率（应<70%）
show memory

# 检查当前VLAN数量（应有空间创建18个新VLAN）
show vlan summary

# 检查当前三层接口数量
show ip interface brief | count

# 检查DHCP服务状态
show ip dhcp server statistics

# 预期结果：
# - CPU < 50%
# - Memory < 70%
# - VLAN总数 < 4000
# - 有足够资源创建18个SVI
```

**兜底检查点0.3**:
```bash
# 如果CPU>80%或Memory>90%，停止部署
# 如果VLAN已接近上限（>3900），评估删除无用VLAN或调整方案
# 如果DHCP服务未启动，先启用：
service dhcp
```

### 0.4 准备回滚脚本

创建回滚脚本文件（在本地电脑）：

**文件名**: `rollback-iot-vlan.txt`

```bash
! ========================================
! 物联网VLAN回滚脚本
! 用途：紧急删除所有物联网配置
! 执行方式：copy tftp flash / configure replace flash:rollback-iot-vlan.txt
! ========================================

configure terminal

! 删除东校区DHCP池
no ip dhcp pool IOT-East-Security-1910
no ip dhcp pool IOT-East-Access-1920
no ip dhcp pool IOT-East-Env-1930
no ip dhcp pool IOT-East-Energy-1940
no ip dhcp pool IOT-East-Fire-1950
no ip dhcp pool IOT-East-Services-1960

! 删除西校区DHCP池
no ip dhcp pool IOT-West-Security-2910
no ip dhcp pool IOT-West-Access-2920
no ip dhcp pool IOT-West-Env-2930
no ip dhcp pool IOT-West-Energy-2940
no ip dhcp pool IOT-West-Fire-2950
no ip dhcp pool IOT-West-Services-2960

! 删除南校区DHCP池
no ip dhcp pool IOT-South-Security-3910
no ip dhcp pool IOT-South-Access-3920
no ip dhcp pool IOT-South-Env-3930
no ip dhcp pool IOT-South-Energy-3940
no ip dhcp pool IOT-South-Fire-3950
no ip dhcp pool IOT-South-Services-3960

! 删除东校区SVI
no interface vlan 1910
no interface vlan 1920
no interface vlan 1930
no interface vlan 1940
no interface vlan 1950
no interface vlan 1960

! 删除西校区SVI
no interface vlan 2910
no interface vlan 2920
no interface vlan 2930
no interface vlan 2940
no interface vlan 2950
no interface vlan 2960

! 删除南校区SVI
no interface vlan 3910
no interface vlan 3920
no interface vlan 3930
no interface vlan 3940
no interface vlan 3950
no interface vlan 3960

! 删除东校区VLAN
no vlan 1910
no vlan 1920
no vlan 1930
no vlan 1940
no vlan 1950
no vlan 1960

! 删除西校区VLAN
no vlan 2910
no vlan 2920
no vlan 2930
no vlan 2940
no vlan 2950
no vlan 2960

! 删除南校区VLAN
no vlan 3910
no vlan 3920
no vlan 3930
no vlan 3940
no vlan 3950
no vlan 3960

! 删除路由（如果已配置静态路由）
no ip route 10.19.0.0 255.255.248.0
no ip route 10.19.8.0 255.255.248.0
no ip route 10.19.16.0 255.255.248.0
no ip route 10.19.24.0 255.255.248.0
no ip route 10.19.32.0 255.255.248.0
no ip route 10.19.40.0 255.255.248.0
no ip route 10.29.0.0 255.255.248.0
no ip route 10.29.8.0 255.255.248.0
no ip route 10.29.16.0 255.255.248.0
no ip route 10.29.24.0 255.255.248.0
no ip route 10.29.32.0 255.255.248.0
no ip route 10.29.40.0 255.255.248.0
no ip route 10.39.0.0 255.255.248.0
no ip route 10.39.8.0 255.255.248.0
no ip route 10.39.16.0 255.255.248.0
no ip route 10.39.24.0 255.255.248.0
no ip route 10.39.32.0 255.255.248.0
no ip route 10.39.40.0 255.255.248.0

end

! 保存配置
write memory

! 回滚完成
```

**上传回滚脚本到交换机**:
```bash
# 从TFTP服务器复制回滚脚本到交换机
copy tftp://10.254.0.100/rollback-iot-vlan.txt flash:rollback-iot-vlan.txt

# 验证文件已上传
dir flash: | include rollback

# 预期结果：看到rollback-iot-vlan.txt文件
```

---

## 🚀 阶段1: 实验验证（测试环境）

**目标**: 部署1个VLAN验证流程  
**环境**: 测试交换机  
**时间**: 2小时

### 1.1 部署东校区安防监控VLAN（VLAN 1910）

#### 步骤1.1.1: 创建VLAN

```bash
# 进入配置模式
configure terminal

# 创建VLAN 1910
vlan 1910
  name IOT-East-Security-Monitoring
  exit

# 立即保存（防止意外重启）
write memory

# 验证VLAN创建
show vlan id 1910

# 预期结果：
# VLAN Name                             Status    Ports
# ---- -------------------------------- --------- -------------------------------
# 1910 IOT-East-Security-Monitoring    active
```

**兜底检查点1.1.1**:
```bash
# 确认VLAN存在
show vlan id 1910 | include 1910

# 如果未看到VLAN，重新执行创建命令
# 如果报错"VLAN already exists"，检查是否冲突
# 如果报错"Maximum VLAN count reached"，停止部署，清理无用VLAN
```

#### 步骤1.1.2: 配置SVI（三层接口）

```bash
# 配置SVI
interface vlan 1910
  description IOT East Campus - Security Monitoring System
  ip address 10.19.0.254 255.255.248.0
  no shutdown
  exit

# 立即保存
write memory

# 验证SVI状态
show interface vlan 1910

# 预期结果：
# Vlan1910 is up, line protocol is up
# Internet address is 10.19.0.254/21
```

**兜底检查点1.1.2**:
```bash
# 确认SVI up
show ip interface brief | include 1910

# 预期：Vlan1910  10.19.0.254  YES manual up  up

# 如果状态为down，检查：
# 1. VLAN是否存在
# 2. 是否有接口加入该VLAN
# 3. 执行 no shutdown

# 测试网关可达性（从交换机自身ping）
ping 10.19.0.254

# 预期：5个包全部成功
```

#### 步骤1.1.3: 配置DHCP池

```bash
# 配置DHCP池
ip dhcp pool IOT-East-Security-1910
  network 10.19.0.0 255.255.248.0
  default-router 10.19.0.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

# 立即保存
write memory

# 验证DHCP池
show ip dhcp pool IOT-East-Security-1910

# 预期结果：
# Pool IOT-East-Security-1910 :
#  Network : 10.19.0.0  Mask : 255.255.248.0
#  Default router : 10.19.0.254
#  DNS server : 10.254.2.1 10.254.2.2
#  Lease : 7 Days 0 Hours 0 Minutes
```

**兜底检查点1.1.3**:
```bash
# 确认DHCP池存在
show ip dhcp pool | include IOT-East-Security-1910

# 确认DHCP服务已启用
show ip dhcp server statistics

# 如果显示"DHCP server is disabled"，启用：
service dhcp
```

### 1.2 连接测试设备

```bash
# 将测试设备（如笔记本、摄像头）连接到交换机
# 将该端口配置为access模式，VLAN 1910

# 示例：将GigabitEthernet 0/1配置为VLAN 1910
configure terminal
interface GigabitEthernet 0/1
  description Test Device for IOT VLAN 1910
  switchport mode access
  switchport access vlan 1910
  no shutdown
  exit

# 保存
write memory

# 验证端口配置
show interfaces GigabitEthernet 0/1 switchport

# 预期结果：
# Operational Mode: access
# Access Mode VLAN: 1910
```

**兜底检查点1.2**:
```bash
# 确认端口在VLAN中
show vlan id 1910

# 预期：Gi0/1出现在Ports列

# 如果端口未出现，重新执行配置
# 如果报错"VLAN does not exist"，先创建VLAN
```

### 1.3 验证功能

#### 验证项1: DHCP分配

```bash
# 在测试设备上：
# Windows: ipconfig /release && ipconfig /renew
# Linux: dhclient -r eth0 && dhclient eth0

# 预期：获取到10.19.0.x/21的IP地址

# 在交换机上验证DHCP绑定
show ip dhcp binding

# 预期结果：
# IP address       Client-ID/              Lease expiration        Type
#                  Hardware address
# 10.19.0.10       01a1.b2c3.d4e5.f6       Jan 13 2026 07:30 AM    Dynamic
```

**兜底检查点1.3.1**:
```bash
# 如果设备未获取IP：
# 1. 检查DHCP池有效地址
show ip dhcp pool IOT-East-Security-1910

# 2. 检查DHCP冲突
show ip dhcp conflict

# 3. 检查端口是否在正确VLAN
show vlan id 1910

# 4. 清除DHCP绑定重试
clear ip dhcp binding *

# 5. 如果仍失败，检查测试设备DHCP客户端是否正常
```

#### 验证项2: 网关连通性

```bash
# 在测试设备上ping网关
ping 10.19.0.254

# 预期：5个包全部成功，延迟<10ms

# 在交换机上查看ARP表
show ip arp | include 10.19.0

# 预期：看到测试设备的IP和MAC地址
```

**兜底检查点1.3.2**:
```bash
# 如果ping失败：
# 1. 检查SVI状态
show interface vlan 1910

# 预期：up, line protocol is up

# 2. 检查IP地址
show ip interface vlan 1910

# 3. 检查是否有ACL阻挡
show ip access-lists

# 4. 测试从交换机ping测试设备
ping <测试设备IP>
```

#### 验证项3: DNS解析

```bash
# 在测试设备上测试DNS
nslookup www.baidu.com

# 预期：能解析到IP地址

# 验证DNS服务器可达
ping 10.254.2.1

# 预期：成功
```

**兜底检查点1.3.3**:
```bash
# 如果DNS失败：
# 1. 确认DHCP分配了DNS服务器
ipconfig /all  # Windows
cat /etc/resolv.conf  # Linux

# 2. 测试DNS服务器可达性
ping 10.254.2.1

# 3. 检查是否有防火墙阻挡UDP 53
```

### 1.4 实验阶段决策点

```bash
# 决策点1.4：是否进入阶段2

# 通过条件（全部满足）：
✓ VLAN创建成功
✓ SVI状态up
✓ DHCP分配成功
✓ 网关可达
✓ DNS解析正常
✓ 无异常告警

# 如果任一条件不满足：
1. 停止部署
2. 分析根因
3. 执行回滚（见7.1节）
4. 修复问题后重新开始阶段1

# 如果全部通过：
→ 进入阶段2（试点部署）
```

---

## 🎯 阶段2: 试点部署（生产环境-东校区）

**目标**: 部署东校区全部6个VLAN  
**环境**: 生产交换机（东校区核心）  
**时间**: 4小时  
**风险**: 中等（仅影响东校区物联网）

### 2.1 部署前最终确认

```bash
# 再次备份当前配置
copy running-config flash:backup-before-pilot-20260906.cfg

# 确认当前时间在维护窗口内（02:00-06:00）
show clock

# 确认无关键业务运行
show processes cpu sorted | exclude 0.0

# 确认已通知相关人员
# - 网络运维团队待命
# - 安防监控团队知晓
# - 值班领导已批准
```

### 2.2 批量部署东校区6个VLAN

**执行方式**: 一次性粘贴所有配置（推荐）或逐个配置

#### 方式1: 一次性配置（推荐，快速）

将以下完整配置复制粘贴到交换机：

```bash
configure terminal

! ========================================
! 东校区物联网 - 6个VLAN完整配置
! 执行时间：2026-09-06 02:00-02:30
! ========================================

! --- VLAN 1910: 安防监控 ---
vlan 1910
  name IOT-East-Security-Monitoring
  exit

interface vlan 1910
  description IOT East - Security Monitoring (Cameras/NVR)
  ip address 10.19.0.254 255.255.248.0
  no shutdown
  exit

ip dhcp pool IOT-East-Security-1910
  network 10.19.0.0 255.255.248.0
  default-router 10.19.0.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

! --- VLAN 1920: 智能门禁 ---
vlan 1920
  name IOT-East-Access-Control
  exit

interface vlan 1920
  description IOT East - Access Control & Attendance
  ip address 10.19.8.254 255.255.248.0
  no shutdown
  exit

ip dhcp pool IOT-East-Access-1920
  network 10.19.8.0 255.255.248.0
  default-router 10.19.8.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

! --- VLAN 1930: 环境感知 ---
vlan 1930
  name IOT-East-Environment-Sensing
  exit

interface vlan 1930
  description IOT East - Environment Sensors
  ip address 10.19.16.254 255.255.248.0
  no shutdown
  exit

ip dhcp pool IOT-East-Env-1930
  network 10.19.16.0 255.255.248.0
  default-router 10.19.16.254
  dns-server 10.254.2.1 10.254.2.2
  lease 3 0 0
  domain-name campus.edu.cn
  exit

! --- VLAN 1940: 能效管控 ---
vlan 1940
  name IOT-East-Energy-Management
  exit

interface vlan 1940
  description IOT East - Energy & Lighting Control
  ip address 10.19.24.254 255.255.248.0
  no shutdown
  exit

ip dhcp pool IOT-East-Energy-1940
  network 10.19.24.0 255.255.248.0
  default-router 10.19.24.254
  dns-server 10.254.2.1 10.254.2.2
  lease 30 0 0
  domain-name campus.edu.cn
  exit

! --- VLAN 1950: 消防应急 ---
vlan 1950
  name IOT-East-Fire-Emergency
  exit

interface vlan 1950
  description IOT East - Fire Alarm & Emergency
  ip address 10.19.32.254 255.255.248.0
  no shutdown
  exit

ip dhcp pool IOT-East-Fire-1950
  network 10.19.32.0 255.255.248.0
  default-router 10.19.32.254
  dns-server 10.254.2.1 10.254.2.2
  lease 30 0 0
  domain-name campus.edu.cn
  exit

! --- VLAN 1960: 智慧服务 ---
vlan 1960
  name IOT-East-Smart-Services
  exit

interface vlan 1960
  description IOT East - Smart Teaching & Facilities
  ip address 10.19.40.254 255.255.248.0
  no shutdown
  exit

ip dhcp pool IOT-East-Services-1960
  network 10.19.40.0 255.255.248.0
  default-router 10.19.40.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

end

! 立即保存
write memory
```

**配置完成预计时间**: 2-3分钟

**兜底检查点2.2**:
```bash
# 验证所有VLAN创建成功
show vlan | include 191[0-6]

# 预期：看到6个VLAN（1910-1960）

# 验证所有SVI状态
show ip interface brief | include 191[0-6]

# 预期：6个SVI全部up

# 验证所有DHCP池
show ip dhcp pool | include IOT-East

# 预期：看到6个DHCP池

# 如果任何验证失败：
# 1. 记录具体错误
# 2. 不要继续后续步骤
# 3. 执行针对性回滚（见7.2节）
```

### 2.3 连接少量真实设备

```bash
# 为每个业务类型连接1-2个真实设备进行测试

# 示例：配置接入交换机端口

# 安防监控（VLAN 1910）- 连接1个摄像头
interface GigabitEthernet 1/0/1
  description Camera-Test-Building1-Floor1
  switchport mode access
  switchport access vlan 1910
  no shutdown
  exit

# 智能门禁（VLAN 1920）- 连接1个门禁控制器
interface GigabitEthernet 1/0/2
  description Access-Controller-Test-Gate1
  switchport mode access
  switchport access vlan 1920
  no shutdown
  exit

# 环境感知（VLAN 1930）- 连接1个温湿度传感器
interface GigabitEthernet 1/0/3
  description Env-Sensor-Test-Room1
  switchport mode access
  switchport access vlan 1930
  no shutdown
  exit

# （其他业务类似配置）

# 保存配置
write memory
```

**兜底检查点2.3**:
```bash
# 验证设备获取IP
show ip dhcp binding | include 10.19

# 预期：看到6个业务各有1-2个设备获取到IP

# 验证设备在线
show ip arp | include 10.19

# 验证设备连通性（从交换机ping设备）
ping 10.19.0.10   # 摄像头
ping 10.19.8.10   # 门禁
ping 10.19.16.10  # 传感器
# ...

# 如果设备未上线：
# 1. 检查物理连接
# 2. 检查端口VLAN配置
# 3. 检查设备端DHCP客户端
# 4. 查看交换机日志
show logging | include 191[0-6]
```

### 2.4 24小时观察期

```bash
# 部署完成后，进入24小时观察期

# 监控项1: DHCP分配统计
show ip dhcp server statistics

# 每4小时执行一次，记录：
# - Messages received/sent
# - DHCPDISCOVER/DHCPOFFER/DHCPREQUEST/DHCPACK数量

# 监控项2: SVI状态
show ip interface brief | include 191[0-6]

# 每2小时执行一次，确认所有SVI持续up

# 监控项3: CPU/内存
show processes cpu sorted
show memory

# 每2小时执行一次，确认无异常飙升

# 监控项4: 错误日志
show logging | include Error|Warning

# 持续监控，关注任何ERROR/WARNING

# 监控项5: 设备连通性
# 从网管平台ping所有已连接设备
# 每1小时执行一次，确认100%可达
```

**兜底检查点2.4（24小时后）**:
```bash
# 通过条件（全部满足）：
✓ 所有设备获取IP成功
✓ 所有SVI持续up 24小时
✓ DHCP无冲突
✓ CPU/内存正常（<60%）
✓ 无ERROR级别日志
✓ 设备连通性100%
✓ 无业务投诉

# 如果任一条件不满足：
1. 暂停进入阶段3
2. 分析根因
3. 评估是否回滚
4. 修复问题后重新观察24小时

# 如果全部通过：
→ 进入阶段3（全面推广）
```

---

## 🌐 阶段3: 全面推广（西校区+南校区）

**目标**: 部署西校区和南校区各6个VLAN  
**环境**: 生产交换机（西校区核心、南校区核心）  
**时间**: 每校区2小时，共4小时  
**风险**: 高（影响全校物联网）

### 3.1 西校区部署（VLAN 2910-2960）

**执行时间**: 02:00-04:00

```bash
# 登录西校区核心交换机
ssh admin@<西校区核心交换机IP>

# 备份配置
copy running-config flash:backup-before-west-iot-20260906.cfg

# 一次性配置（完整粘贴）
configure terminal

! ========================================
! 西校区物联网 - 6个VLAN完整配置
! ========================================

vlan 2910
  name IOT-West-Security-Monitoring
  exit
interface vlan 2910
  description IOT West - Security Monitoring
  ip address 10.29.0.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-West-Security-2910
  network 10.29.0.0 255.255.248.0
  default-router 10.29.0.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

vlan 2920
  name IOT-West-Access-Control
  exit
interface vlan 2920
  description IOT West - Access Control & Attendance
  ip address 10.29.8.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-West-Access-2920
  network 10.29.8.0 255.255.248.0
  default-router 10.29.8.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

vlan 2930
  name IOT-West-Environment-Sensing
  exit
interface vlan 2930
  description IOT West - Environment Sensors
  ip address 10.29.16.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-West-Env-2930
  network 10.29.16.0 255.255.248.0
  default-router 10.29.16.254
  dns-server 10.254.2.1 10.254.2.2
  lease 3 0 0
  domain-name campus.edu.cn
  exit

vlan 2940
  name IOT-West-Energy-Management
  exit
interface vlan 2940
  description IOT West - Energy & Lighting Control
  ip address 10.29.24.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-West-Energy-2940
  network 10.29.24.0 255.255.248.0
  default-router 10.29.24.254
  dns-server 10.254.2.1 10.254.2.2
  lease 30 0 0
  domain-name campus.edu.cn
  exit

vlan 2950
  name IOT-West-Fire-Emergency
  exit
interface vlan 2950
  description IOT West - Fire Alarm & Emergency
  ip address 10.29.32.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-West-Fire-2950
  network 10.29.32.0 255.255.248.0
  default-router 10.29.32.254
  dns-server 10.254.2.1 10.254.2.2
  lease 30 0 0
  domain-name campus.edu.cn
  exit

vlan 2960
  name IOT-West-Smart-Services
  exit
interface vlan 2960
  description IOT West - Smart Teaching & Facilities
  ip address 10.29.40.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-West-Services-2960
  network 10.29.40.0 255.255.248.0
  default-router 10.29.40.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

end
write memory
```

**兜底检查点3.1**:
```bash
# 验证西校区配置
show vlan | include 291[0-6]
show ip interface brief | include 291[0-6]
show ip dhcp pool | include IOT-West

# 快速连通性测试
ping 10.29.0.254
ping 10.29.8.254
ping 10.29.16.254
ping 10.29.24.254
ping 10.29.32.254
ping 10.29.40.254

# 预期：所有网关可达

# 如果任何检查失败，立即停止，不继续南校区部署
```

### 3.2 南校区部署（VLAN 3910-3960）

**执行时间**: 04:00-06:00

```bash
# 登录南校区核心交换机
ssh admin@<南校区核心交换机IP>

# 备份配置
copy running-config flash:backup-before-south-iot-20260906.cfg

# 一次性配置（完整粘贴）
configure terminal

! ========================================
! 南校区物联网 - 6个VLAN完整配置
! ========================================

vlan 3910
  name IOT-South-Security-Monitoring
  exit
interface vlan 3910
  description IOT South - Security Monitoring
  ip address 10.39.0.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-South-Security-3910
  network 10.39.0.0 255.255.248.0
  default-router 10.39.0.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

vlan 3920
  name IOT-South-Access-Control
  exit
interface vlan 3920
  description IOT South - Access Control & Attendance
  ip address 10.39.8.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-South-Access-3920
  network 10.39.8.0 255.255.248.0
  default-router 10.39.8.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

vlan 3930
  name IOT-South-Environment-Sensing
  exit
interface vlan 3930
  description IOT South - Environment Sensors
  ip address 10.39.16.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-South-Env-3930
  network 10.39.16.0 255.255.248.0
  default-router 10.39.16.254
  dns-server 10.254.2.1 10.254.2.2
  lease 3 0 0
  domain-name campus.edu.cn
  exit

vlan 3940
  name IOT-South-Energy-Management
  exit
interface vlan 3940
  description IOT South - Energy & Lighting Control
  ip address 10.39.24.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-South-Energy-3940
  network 10.39.24.0 255.255.248.0
  default-router 10.39.24.254
  dns-server 10.254.2.1 10.254.2.2
  lease 30 0 0
  domain-name campus.edu.cn
  exit

vlan 3950
  name IOT-South-Fire-Emergency
  exit
interface vlan 3950
  description IOT South - Fire Alarm & Emergency
  ip address 10.39.32.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-South-Fire-3950
  network 10.39.32.0 255.255.248.0
  default-router 10.39.32.254
  dns-server 10.254.2.1 10.254.2.2
  lease 30 0 0
  domain-name campus.edu.cn
  exit

vlan 3960
  name IOT-South-Smart-Services
  exit
interface vlan 3960
  description IOT South - Smart Teaching & Facilities
  ip address 10.39.40.254 255.255.248.0
  no shutdown
  exit
ip dhcp pool IOT-South-Services-3960
  network 10.39.40.0 255.255.248.0
  default-router 10.39.40.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit

end
write memory
```

**兜底检查点3.2**:
```bash
# 验证南校区配置
show vlan | include 391[0-6]
show ip interface brief | include 391[0-6]
show ip dhcp pool | include IOT-South

# 快速连通性测试
ping 10.39.0.254
ping 10.39.8.254
ping 10.39.16.254
ping 10.39.24.254
ping 10.39.32.254
ping 10.39.40.254

# 预期：所有网关可达
```

### 3.3 全局验证

```bash
# 在任意一台核心交换机执行全局检查

# 检查项1: 所有18个网段路由可达
ping 10.19.0.254   # 东-安防
ping 10.19.8.254   # 东-门禁
ping 10.19.16.254  # 东-环境
ping 10.19.24.254  # 东-能效
ping 10.19.32.254  # 东-消防
ping 10.19.40.254  # 东-服务
ping 10.29.0.254   # 西-安防
ping 10.29.8.254   # 西-门禁
ping 10.29.16.254  # 西-环境
ping 10.29.24.254  # 西-能效
ping 10.29.32.254  # 西-消防
ping 10.29.40.254  # 西-服务
ping 10.39.0.254   # 南-安防
ping 10.39.8.254   # 南-门禁
ping 10.39.16.254  # 南-环境
ping 10.39.24.254  # 南-能效
ping 10.39.32.254  # 南-消防
ping 10.39.40.254  # 南-服务

# 预期：18个网关100%可达

# 检查项2: 无IP冲突
show ip arp duplicate

# 预期：无输出

# 检查项3: DHCP池统计
# 在三个校区分别执行
show ip dhcp server statistics

# 预期：三校区DHCP服务正常
```

**兜底检查点3.3（最终决策点）**:
```bash
# 通过条件（全部满足）：
✓ 18个VLAN全部创建
✓ 18个SVI全部up
✓ 18个DHCP池正常
✓ 18个网关100%可达
✓ 无IP冲突
✓ CPU/内存正常
✓ 无ERROR日志

# 如果任一条件不满足：
→ 执行紧急回滚（见7.3节）

# 如果全部通过：
→ 进入48小时稳定性观察
→ 逐步迁移物联网设备
```

---

## 🛡️ 兜底机制汇总

### 兜底层级

**L1: 单步骤检查点** - 每个配置步骤后立即验证  
**L2: 阶段检查点** - 每个阶段完成后综合验证  
**L3: 全局检查点** - 全部部署完成后端到端验证

### 自动触发条件

| 触发条件 | 兜底动作 | 执行者 |
|---------|---------|--------|
| VLAN创建失败率>10% | 停止部署，排查原因 | 自动 |
| SVI状态down>3个 | 停止部署，检查配置 | 自动 |
| DHCP分配失败率>5% | 告警，人工介入 | 半自动 |
| 网关不可达>3个 | 停止部署，检查路由 | 自动 |
| CPU>80%持续5分钟 | 告警，评估回滚 | 半自动 |
| 内存>90% | 立即回滚 | 自动 |
| IP冲突>0个 | 停止部署，解决冲突 | 自动 |
| 错误日志>10条/分钟 | 告警，人工介入 | 半自动 |

### 人工决策点

| 决策点 | 判断标准 | 决策选项 |
|--------|---------|---------|
| 阶段1→2 | 实验成功 | 继续/停止 |
| 阶段2→3 | 试点24小时稳定 | 继续/延长观察/回滚 |
| 发现异常 | 影响评估 | 继续/暂停/回滚 |
| 业务投诉 | 投诉数量和严重度 | 暂停/回滚 |

---

## 🔙 回滚机制

### 7.1 单VLAN回滚（阶段1失败）

```bash
# 适用场景：阶段1实验失败，仅部署了1个VLAN

configure terminal

# 删除DHCP池
no ip dhcp pool IOT-East-Security-1910

# 删除SVI
no interface vlan 1910

# 删除VLAN
no vlan 1910

end
write memory

# 验证回滚
show vlan id 1910
# 预期：% VLAN 1910 not found

# 恢复原配置（可选）
copy flash:backup-before-iot-20260906.cfg running-config

# 回滚完成时间：<2分钟
```

### 7.2 单校区回滚（阶段2失败）

```bash
# 适用场景：东校区试点失败，需回滚6个VLAN

configure terminal

# 删除东校区所有DHCP池
no ip dhcp pool IOT-East-Security-1910
no ip dhcp pool IOT-East-Access-1920
no ip dhcp pool IOT-East-Env-1930
no ip dhcp pool IOT-East-Energy-1940
no ip dhcp pool IOT-East-Fire-1950
no ip dhcp pool IOT-East-Services-1960

# 删除东校区所有SVI
no interface vlan 1910
no interface vlan 1920
no interface vlan 1930
no interface vlan 1940
no interface vlan 1950
no interface vlan 1960

# 删除东校区所有VLAN
no vlan 1910
no vlan 1920
no vlan 1930
no vlan 1940
no vlan 1950
no vlan 1960

end
write memory

# 或使用预存的回滚脚本
copy flash:rollback-iot-vlan.txt running-config

# 验证回滚
show vlan | include 191[0-6]
# 预期：无输出

# 回滚完成时间：<5分钟
```

### 7.3 全局回滚（阶段3失败）

```bash
# 适用场景：全部18个VLAN部署后发现严重问题

# 方式1: 使用回滚脚本（推荐）
# 在东、西、南三个校区分别执行
copy flash:rollback-iot-vlan.txt running-config

# 方式2: 恢复原始配置
copy flash:backup-before-pilot-20260906.cfg running-config

# 方式3: 手工回滚（最后手段）
# 按7.2节步骤，在三个校区分别执行

# 验证回滚（三个校区分别检查）
show vlan | include "191[0-6]|291[0-6]|391[0-6]"
# 预期：无输出

show ip interface brief | include "191[0-6]|291[0-6]|391[0-6]"
# 预期：无输出

show ip dhcp pool | include IOT
# 预期：无输出

# 回滚完成时间：<10分钟（三校区并行）
```

### 7.4 回滚后验证清单

```bash
# 验证1: 物联网VLAN全部删除
show vlan summary
# 对比回滚前后VLAN数量，应减少18个

# 验证2: SVI全部删除
show ip interface brief | count
# 对比回滚前后接口数量，应减少18个

# 验证3: DHCP池全部删除
show ip dhcp pool | count
# 对比回滚前后池数量，应减少18个

# 验证4: 无残留路由
show ip route | include "10.19|10.29|10.39"
# 预期：仅显示非物联网网段

# 验证5: 无残留ARP
show ip arp | include "10.19|10.29|10.39"
# 预期：无输出或仅显示其他业务

# 验证6: 系统稳定
show processes cpu
show memory
# CPU<50%, 内存<70%

# 验证7: 原有业务正常
ping <原有网段网关>
# 确认原有业务未受影响
```

---

## 📋 部署检查清单

### 阶段0检查清单
- [ ] 备份配置已保存
- [ ] 设备状态正常（CPU<50%, 内存<70%）
- [ ] VLAN资源充足（可创建18个新VLAN）
- [ ] 回滚脚本已准备并上传
- [ ] 维护窗口已确认（02:00-06:00）
- [ ] 相关人员已通知

### 阶段1检查清单
- [ ] 测试VLAN创建成功
- [ ] 测试SVI状态up
- [ ] 测试DHCP分配成功
- [ ] 测试网关可达
- [ ] 测试DNS解析正常
- [ ] 无异常告警

### 阶段2检查清单
- [ ] 东校区6个VLAN全部创建
- [ ] 东校区6个SVI全部up
- [ ] 东校区6个DHCP池正常
- [ ] 东校区6个网关可达
- [ ] 测试设备已连接（每业务1-2个）
- [ ] 所有测试设备获取IP
- [ ] 24小时观察期无异常

### 阶段3检查清单
- [ ] 西校区6个VLAN全部创建
- [ ] 西校区6个SVI全部up
- [ ] 西校区6个DHCP池正常
- [ ] 南校区6个VLAN全部创建
- [ ] 南校区6个SVI全部up
- [ ] 南校区6个DHCP池正常
- [ ] 全局18个网关100%可达
- [ ] 无IP冲突
- [ ] CPU/内存正常
- [ ] 无ERROR日志

### 回滚检查清单
- [ ] 所有物联网VLAN已删除
- [ ] 所有物联网SVI已删除
- [ ] 所有物联网DHCP池已删除
- [ ] 无残留路由
- [ ] 无残留ARP
- [ ] 系统恢复稳定
- [ ] 原有业务正常

---

## 📞 应急联系

### 应急响应团队

| 角色 | 姓名 | 电话 | 职责 |
|------|------|------|------|
| 项目负责人 | 待定 | 待定 | 整体决策 |
| 网络工程师 | 待定 | 待定 | 现场执行 |
| 安防负责人 | 待定 | 待定 | 安防业务验证 |
| 值班领导 | 待定 | 待定 | 应急授权 |

### 应急响应流程

```
发现异常
   ↓
立即停止部署
   ↓
评估影响范围
   ↓
├─ 影响<10%设备 → 隔离问题 → 继续观察
└─ 影响≥10%设备 → 启动回滚 → 通知领导
```

---

**部署手册版本**: v2.0  
**最后更新**: 2026-09-06 07:30 UTC  
**适用设备**: 锐捷RGOS交换机  
**审查状态**: ✅ 已包含实施顺序、详细配置、兜底机制、回滚机制
