# 物联网方案 - 18个VLAN完整RGOS配置

**配置版本**: v1.1  
**生成时间**: 2026-09-06 07:00 UTC  
**设计依据**: 物联网方案v1.1（已通过taolun审查，P0问题已解决）  
**审查状态**: ✅ Codex确认P0已关闭  
**配置规模**: 18个VLAN，约600行配置

---

## 📋 配置概览

### 业务分类（6类）

| 代码 | 业务名称 | 设备类型 | 预估数量 |
|-----|---------|---------|---------|
| 1 | 安防监控 | 摄像头、NVR、视频分析 | >500 |
| 2 | 智能门禁 | 门锁、刷卡器、人脸识别、考勤 | >200 |
| 3 | 环境感知 | 温湿度、空气质量、光照、噪声 | >300 |
| 4 | 能效管控 | 照明+电表+水表+空调控制 | <200 |
| 5 | 消防应急 | 烟感+温感+报警+应急广播 | <150 |
| 6 | 智慧服务 | 教学+电梯+停车+医疗监测 | <200 |

### VLAN分配（18个）

| 校区 | VLAN范围 | IP段范围 | 总地址 |
|------|---------|---------|--------|
| 东校区 | 1910-1960 | 10.19.0.0/21 - 10.19.40.0/21 | 12,276 |
| 西校区 | 2910-2960 | 10.29.0.0/21 - 10.29.40.0/21 | 12,276 |
| 南校区 | 3910-3960 | 10.39.0.0/21 - 10.39.40.0/21 | 12,276 |

**全校总计**: 36,828个物联网地址

---

## 🔧 完整配置（按校区）

---

## 第一部分：东校区配置（VLAN 1910-1960）

### 1.1 东校区 - 安防监控（VLAN 1910）

```
! ========================================
! 东校区 - 安防监控系统
! VLAN 1910, IP 10.19.0.0/21
! 设备：摄像头、NVR、视频分析服务器
! ========================================

! 创建VLAN
vlan 1910
  name IOT-East-Security-Monitoring
  exit

! 配置SVI（三层接口）
interface vlan 1910
  description IOT East Campus - Security Monitoring
  ip address 10.19.0.254 255.255.248.0
  no shutdown
  exit

! DHCP配置
ip dhcp pool IOT-East-Security-1910
  network 10.19.0.0 255.255.248.0
  default-router 10.19.0.254
  dns-server 10.254.2.1 10.254.2.2
  lease 7 0 0
  domain-name campus.edu.cn
  exit
```

### 1.2 东校区 - 智能门禁（VLAN 1920）

```
! ========================================
! 东校区 - 智能门禁系统
! VLAN 1920, IP 10.19.8.0/21
! 设备：门锁、刷卡器、人脸识别、考勤机
! ========================================

vlan 1920
  name IOT-East-Access-Control
  exit

interface vlan 1920
  description IOT East Campus - Access Control & Attendance
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
```

### 1.3 东校区 - 环境感知（VLAN 1930）

```
! ========================================
! 东校区 - 环境感知系统
! VLAN 1930, IP 10.19.16.0/21
! 设备：温湿度、空气质量、光照、噪声传感器
! ========================================

vlan 1930
  name IOT-East-Environment-Sensing
  exit

interface vlan 1930
  description IOT East Campus - Environment Sensors
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
```

### 1.4 东校区 - 能效管控（VLAN 1940）

```
! ========================================
! 东校区 - 能效管控系统
! VLAN 1940, IP 10.19.24.0/21
! 设备：照明控制、电表、水表、空调控制
! ========================================

vlan 1940
  name IOT-East-Energy-Management
  exit

interface vlan 1940
  description IOT East Campus - Energy & Lighting Control
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
```

### 1.5 东校区 - 消防应急（VLAN 1950）

```
! ========================================
! 东校区 - 消防应急系统
! VLAN 1950, IP 10.19.32.0/21
! 设备：烟感、温感、报警器、应急广播
! ========================================

vlan 1950
  name IOT-East-Fire-Emergency
  exit

interface vlan 1950
  description IOT East Campus - Fire Alarm & Emergency
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
```

### 1.6 东校区 - 智慧服务（VLAN 1960）

```
! ========================================
! 东校区 - 智慧服务系统
! VLAN 1960, IP 10.19.40.0/21
! 设备：教学设备、电梯监控、停车管理、医疗监测
! ========================================

vlan 1960
  name IOT-East-Smart-Services
  exit

interface vlan 1960
  description IOT East Campus - Smart Teaching & Facilities
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
```

---

## 第二部分：西校区配置（VLAN 2910-2960）

### 2.1 西校区 - 安防监控（VLAN 2910）

```
! ========================================
! 西校区 - 安防监控系统
! VLAN 2910, IP 10.29.0.0/21
! ========================================

vlan 2910
  name IOT-West-Security-Monitoring
  exit

interface vlan 2910
  description IOT West Campus - Security Monitoring
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
```

### 2.2 西校区 - 智能门禁（VLAN 2920）

```
! ========================================
! 西校区 - 智能门禁系统
! VLAN 2920, IP 10.29.8.0/21
! ========================================

vlan 2920
  name IOT-West-Access-Control
  exit

interface vlan 2920
  description IOT West Campus - Access Control & Attendance
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
```

### 2.3 西校区 - 环境感知（VLAN 2930）

```
! ========================================
! 西校区 - 环境感知系统
! VLAN 2930, IP 10.29.16.0/21
! ========================================

vlan 2930
  name IOT-West-Environment-Sensing
  exit

interface vlan 2930
  description IOT West Campus - Environment Sensors
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
```

### 2.4 西校区 - 能效管控（VLAN 2940）

```
! ========================================
! 西校区 - 能效管控系统
! VLAN 2940, IP 10.29.24.0/21
! ========================================

vlan 2940
  name IOT-West-Energy-Management
  exit

interface vlan 2940
  description IOT West Campus - Energy & Lighting Control
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
```

### 2.5 西校区 - 消防应急（VLAN 2950）

```
! ========================================
! 西校区 - 消防应急系统
! VLAN 2950, IP 10.29.32.0/21
! ========================================

vlan 2950
  name IOT-West-Fire-Emergency
  exit

interface vlan 2950
  description IOT West Campus - Fire Alarm & Emergency
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
```

### 2.6 西校区 - 智慧服务（VLAN 2960）

```
! ========================================
! 西校区 - 智慧服务系统
! VLAN 2960, IP 10.29.40.0/21
! ========================================

vlan 2960
  name IOT-West-Smart-Services
  exit

interface vlan 2960
  description IOT West Campus - Smart Teaching & Facilities
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
```

---

## 第三部分：南校区配置（VLAN 3910-3960）

### 3.1 南校区 - 安防监控（VLAN 3910）

```
! ========================================
! 南校区 - 安防监控系统
! VLAN 3910, IP 10.39.0.0/21
! ========================================

vlan 3910
  name IOT-South-Security-Monitoring
  exit

interface vlan 3910
  description IOT South Campus - Security Monitoring
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
```

### 3.2 南校区 - 智能门禁（VLAN 3920）

```
! ========================================
! 南校区 - 智能门禁系统
! VLAN 3920, IP 10.39.8.0/21
! ========================================

vlan 3920
  name IOT-South-Access-Control
  exit

interface vlan 3920
  description IOT South Campus - Access Control & Attendance
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
```

### 3.3 南校区 - 环境感知（VLAN 3930）

```
! ========================================
! 南校区 - 环境感知系统
! VLAN 3930, IP 10.39.16.0/21
! ========================================

vlan 3930
  name IOT-South-Environment-Sensing
  exit

interface vlan 3930
  description IOT South Campus - Environment Sensors
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
```

### 3.4 南校区 - 能效管控（VLAN 3940）

```
! ========================================
! 南校区 - 能效管控系统
! VLAN 3940, IP 10.39.24.0/21
! ========================================

vlan 3940
  name IOT-South-Energy-Management
  exit

interface vlan 3940
  description IOT South Campus - Energy & Lighting Control
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
```

### 3.5 南校区 - 消防应急（VLAN 3950）

```
! ========================================
! 南校区 - 消防应急系统
! VLAN 3950, IP 10.39.32.0/21
! ========================================

vlan 3950
  name IOT-South-Fire-Emergency
  exit

interface vlan 3950
  description IOT South Campus - Fire Alarm & Emergency
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
```

### 3.6 南校区 - 智慧服务（VLAN 3960）

```
! ========================================
! 南校区 - 智慧服务系统
! VLAN 3960, IP 10.39.40.0/21
! ========================================

vlan 3960
  name IOT-South-Smart-Services
  exit

interface vlan 3960
  description IOT South Campus - Smart Teaching & Facilities
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
```

---

## 第四部分：路由配置

### 4.1 物联网网段路由宣告

```
! ========================================
! 物联网18个网段路由宣告
! ========================================

! 东校区物联网路由（6个网段）
ip route 10.19.0.0 255.255.248.0 vlan 1910
ip route 10.19.8.0 255.255.248.0 vlan 1920
ip route 10.19.16.0 255.255.248.0 vlan 1930
ip route 10.19.24.0 255.255.248.0 vlan 1940
ip route 10.19.32.0 255.255.248.0 vlan 1950
ip route 10.19.40.0 255.255.248.0 vlan 1960

! 西校区物联网路由（6个网段）
ip route 10.29.0.0 255.255.248.0 vlan 2910
ip route 10.29.8.0 255.255.248.0 vlan 2920
ip route 10.29.16.0 255.255.248.0 vlan 2930
ip route 10.29.24.0 255.255.248.0 vlan 2940
ip route 10.29.32.0 255.255.248.0 vlan 2950
ip route 10.29.40.0 255.255.248.0 vlan 2960

! 南校区物联网路由（6个网段）
ip route 10.39.0.0 255.255.248.0 vlan 3910
ip route 10.39.8.0 255.255.248.0 vlan 3920
ip route 10.39.16.0 255.255.248.0 vlan 3930
ip route 10.39.24.0 255.255.248.0 vlan 3940
ip route 10.39.32.0 255.255.248.0 vlan 3950
ip route 10.39.40.0 255.255.248.0 vlan 3960
```

### 4.2 跨校区路由（如需要）

```
! ========================================
! 跨校区物联网互通路由（可选）
! 根据实际需求配置
! ========================================

! 东校区到西校区物联网
ip route 10.29.0.0 255.255.192.0 <西校区核心交换机IP>

! 东校区到南校区物联网
ip route 10.39.0.0 255.255.192.0 <南校区核心交换机IP>

! （西校区、南校区类似配置）
```

---

## 第五部分：基础ACL配置

### 5.1 物联网访问控制原则

```
! ========================================
! 物联网ACL基础规则
! ========================================

! ACL 100: 物联网到管理网（禁止）
access-list 100 deny ip 10.19.0.0 0.0.255.255 10.254.0.0 0.0.255.255
access-list 100 deny ip 10.29.0.0 0.0.255.255 10.254.0.0 0.0.255.255
access-list 100 deny ip 10.39.0.0 0.0.255.255 10.254.0.0 0.0.255.255
access-list 100 permit ip any any

! ACL 101: 允许物联网访问DNS/NTP
access-list 101 permit udp 10.19.0.0 0.0.255.255 any eq 53
access-list 101 permit udp 10.29.0.0 0.0.255.255 any eq 53
access-list 101 permit udp 10.39.0.0 0.0.255.255 any eq 53
access-list 101 permit udp 10.19.0.0 0.0.255.255 any eq 123
access-list 101 permit udp 10.29.0.0 0.0.255.255 any eq 123
access-list 101 permit udp 10.39.0.0 0.0.255.255 any eq 123
access-list 101 permit ip any any

! ACL 102: 安防监控访问NVR服务器
access-list 102 permit tcp 10.19.0.0 0.0.7.255 host <NVR-Server-IP> eq 554
access-list 102 permit tcp 10.29.0.0 0.0.7.255 host <NVR-Server-IP> eq 554
access-list 102 permit tcp 10.39.0.0 0.0.7.255 host <NVR-Server-IP> eq 554
access-list 102 permit ip any any
```

### 5.2 应用ACL到VLAN接口

```
! 示例：东校区安防监控VLAN应用ACL
interface vlan 1910
  ip access-group 100 in
  ip access-group 102 out
  exit

! （其他VLAN类似配置）
```

---

## 第六部分：验证命令

### 6.1 VLAN验证

```
! 显示所有VLAN
show vlan

! 显示特定VLAN
show vlan id 1910
show vlan id 2920
show vlan id 3930

! 预期结果：18个VLAN全部存在
```

### 6.2 SVI验证

```
! 显示所有三层接口
show ip interface brief

! 显示特定SVI
show interface vlan 1910
show interface vlan 2920
show interface vlan 3930

! 预期结果：18个SVI全部up
```

### 6.3 DHCP验证

```
! 显示DHCP池配置
show ip dhcp pool

! 显示DHCP绑定
show ip dhcp binding

! 显示DHCP统计
show ip dhcp server statistics

! 预期结果：18个DHCP池正常工作
```

### 6.4 路由验证

```
! 显示路由表
show ip route

! 验证物联网路由
show ip route 10.19.0.0
show ip route 10.29.8.0
show ip route 10.39.16.0

! 预期结果：18个网段路由存在
```

### 6.5 连通性验证

```
! 从核心交换机ping网关
ping 10.19.0.254
ping 10.19.8.254
ping 10.19.16.254
（共18个网关）

! 预期结果：所有网关可达
```

---

## 第七部分：回退配置

### 7.1 快速回退命令

```
! ========================================
! 紧急回退：删除所有物联网配置
! ========================================

! 删除东校区VLAN（1910-1960）
no vlan 1910
no vlan 1920
no vlan 1930
no vlan 1940
no vlan 1950
no vlan 1960

! 删除西校区VLAN（2910-2960）
no vlan 2910
no vlan 2920
no vlan 2930
no vlan 2940
no vlan 2950
no vlan 2960

! 删除南校区VLAN（3910-3960）
no vlan 3910
no vlan 3920
no vlan 3930
no vlan 3940
no vlan 3950
no vlan 3960

! 删除DHCP池
no ip dhcp pool IOT-East-Security-1910
no ip dhcp pool IOT-East-Access-1920
（...共18个）

! 删除路由
no ip route 10.19.0.0 255.255.248.0 vlan 1910
（...共18条）

! 预期时间：<5分钟
```

---

## 📊 配置统计

### 配置规模

| 项目 | 数量 |
|------|------|
| VLAN | 18个 |
| SVI接口 | 18个 |
| DHCP池 | 18个 |
| 静态路由 | 18条 |
| ACL规则 | 基础6条（可扩展）|
| 总配置行数 | ~600行 |

### 地址分配

| 校区 | 网段数 | 可用地址 |
|------|--------|---------|
| 东校区 | 6 | 12,276 |
| 西校区 | 6 | 12,276 |
| 南校区 | 6 | 12,276 |
| **合计** | **18** | **36,828** |

---

## ✅ 配置检查清单

### 部署前检查

- [ ] 所有VLAN编号正确（1910-1960, 2910-2960, 3910-3960）
- [ ] 所有IP地址符合/21边界（C值为8的倍数）
- [ ] 所有网关地址为.254
- [ ] 所有DHCP池配置完整
- [ ] DNS服务器地址正确（10.254.2.1/2.2）
- [ ] 租期设置合理（监控/门禁7天，传感器3天，能效/消防30天）
- [ ] 路由配置完整（18条静态路由）
- [ ] ACL规则符合安全策略

### 部署后验证

- [ ] 所有VLAN创建成功（show vlan）
- [ ] 所有SVI接口up（show ip interface brief）
- [ ] 所有网关可达（ping测试）
- [ ] DHCP分配正常（show ip dhcp binding）
- [ ] 路由表正确（show ip route）
- [ ] ACL生效（show ip access-lists）
- [ ] 无IP冲突（show ip arp）
- [ ] 设备能获取IP（终端测试）

---

## 📋 部署建议

### 分阶段部署

**阶段1: 实验验证**（2小时）
- 在测试环境部署1个校区6个VLAN
- 验证VLAN创建、SVI配置、DHCP分配
- 测试连通性和隔离性

**阶段2: 试点部署**（4小时）
- 部署东校区6个VLAN到生产环境
- 连接少量测试设备
- 观察24小时稳定性

**阶段3: 全面部署**（8小时）
- 部署西校区、南校区12个VLAN
- 批量连接物联网设备
- 持续监控48小时

### 回退触发条件

- VLAN创建失败率 >10%
- DHCP分配失败率 >5%
- 网关不可达 >3个
- IP地址冲突 >0个
- 设备连接失败率 >20%

---

**配置版本**: v1.1  
**审查状态**: ✅ Codex确认P0已解决  
**生产就绪**: ✅ 可进入实验验证阶段  
**生成时间**: 2026-09-06 07:00 UTC
