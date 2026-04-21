# 论文计划书：公共交通网络上的价值最大化路线规划

## 📋 概述

本论文提出一种基于 **逆向目标 RAPTOR 算法** 的公共交通路径规划系统，通过多维评分函数和三层混合剪枝策略，实现在真实时刻表约束下的价值最大化巡回规划。

> **主投目标 ①**：ITS シンポジウム 2026（札幌，11/12-13）— 英文査読セッション，採録後 IJIT 国際论文誌に掲載，截止约 **6月1日**
> **备投目标 ②**：ACM SIGSPATIAL 2026 (CORE A，Short Paper 6/9 截止) 或 EAI MobiQuitous 2026 (别府，5/31 截止)
> **问题定位**：本研究问题为 **Maximum Collection TSP / TSP with Time Budget** 在真实 GTFS 时刻表网络上的扩展变体

---

## 🎯 核心创新点

### 创新点 1：逆向目标 RAPTOR (Reverse-Objective RAPTOR)
- **问题**：传统公共交通路径规划以"最快到达"为目标，不适用于价值最大化的巡回规划场景
- **方案**：将目标函数反转为价值最大化（乘车时长、站点覆盖、几何扩张等）
- **意义**：在真实 GTFS 时刻表约束下，将 RAPTOR 轮次搜索扩展到价值最大化巡回任务
- **论文论证要点**：
  - 明确形式化反转过程：从标准 RAPTOR 的 min(arrival_time) 到本文的 max(f(r))
  - 阐述反转后搜索空间的变化（无自然上界，搜索不再收敛到单一最优解）
  - 说明为何这不是简单的目标函数替换，而是需要全新的剪枝和终止条件设计
- **关键代码**：`apps/api/services/planners/*.py` 中的 `scoring_fn`

### 创新点 2：三层混合剪枝策略 (Three-Layer Hybrid Pruning)
| 层级 | 策略 | 理论基础 | 作用 |
|------|------|----------|------|
| 宏观 | Beam Pruning | Beam Search 在组合优化中的宽度-质量 trade-off 理论 | 控制搜索宽度，防止状态爆炸 |
| 微观 | Dominance Pruning | Pareto Dominance (Deb, NSGA-II, 2002) | 剔除同位置被支配路径 |
| 规则 | Negative Score Pruning | 约束松弛的罚函数方法 | 软评分实现硬约束 |

- **效果**：184x 加速，解质量提升 3x
- **论文论证要点**：
  - 形式化定义路径支配关系：路径 r1 支配 r2 当且仅当 r1 在所有评分维度 >= r2 且至少一个维度严格 >
  - 强调三层协同的独特性：不是简单技术拼凑，而是利用 RAPTOR 轮次结构分层剪枝
  - 消融实验量化每层独立贡献和协同增益
- **关键代码**：`apps/api/services/planner.py` -> `run_beam_search`

### 创新点 3：几何感知的动态评分 (Geometry-Aware Dynamic Scoring)
- 实时计算凸包面积 (`hull_area`)、象限覆盖 (`quadrants`)
- 将地理空间特征融入路径评价，避免产生局部往返的低质量路径
- **论文论证要点**：
  - 引用推荐系统中 spatial diversity 概念和路线吸引力/平滑度的已有研究
  - 定位凸包面积为上述概念的可计算量化指标
  - 强调与事后评估的区别：几何特征在搜索过程中实时参与决策（每一轮评分和剪枝都考虑空间扩张）
  - 论证对用户心理的直接映射：一日券值回票价 = 地理覆盖范围够大
- **关键代码**：`apps/api/services/planner_utils.py`

### 方法改进考虑点

> 以下两个方向已在实验中设计验证环节，若效果好可升级为额外创新点，若效果不佳则作为分析讨论。

**考虑 A：自适应 Beam Width (Adaptive Beam Search)**
- 思路：参考 NLP 中的 adaptive beam search，根据候选路径质量的标准差动态调整 beam width
- 验证：在实验 3a 中增加 adaptive W 配置与固定 W 对比
- 预期：若有效则增加创新点；若固定 W 更优则分析公共交通场景下 beam width 稳定性的原因

**考虑 B：形式化 Pareto Dominance 关系**
- 思路：引入 Hypervolume Indicator (Zitzler & Thiele, 1999) 量化评估路径集合的 Pareto 前沿质量
- 验证：在实验 1 与实验 4 中计算各算法结果的 Hypervolume，提供理论层面的多目标最优性论证
- 意义：将工程层面的 dominance pruning 上升到多目标优化理论高度

### 研究问题定义（补强版）
- **任务输入**：GTFS 网络 $G=(S,T,F)$，起点站 $s_0$，出发时刻 $t_0$，预算时长 $B$，约束参数（最大换乘次数、最大步行距离、是否必须回到起点）。
- **可行解**：满足时刻表可达性与时间单调性的路径 $r$，可包含步行边与乘车边；默认允许重复站点，但在评分中施加重复惩罚。
- **硬约束**：总耗时不超过 $B$；每段乘车必须符合 GTFS 发车/到达时间；不可出现时间回退。
- **优化目标**：输出 Pareto 候选集 $P$（ride time / unique stops / hull area / quadrant coverage），再由权重函数做任务化排序。
- **问题性质**：本问题与带时间窗的 Orienteering 变体相关，属于 NP-hard 类问题；本文目标是高质量近似解与可扩展求解，不声称全局最优。
- **应用语义**：明确面向一日券价值最大化、公共交通覆盖探索、城市观光巡游三类任务，而非通勤最短路。

---

## 📝 论文结构

### 标题
> "Value-Maximizing Itinerary Planning on Public Transit Networks with Hybrid Pruning Strategies"

### 结构

#### Section 1: Introduction (1.5 页)
- 问题背景：公共交通网络中**非最短路**的路径优化需求
- 动机：价值最大化巡回问题在交通规划中的实际意义（通票/一日券利用率优化、公共交通覆盖率分析等）
- 贡献总结（三点核心创新）
- 论文组织结构

#### Section 2: Related Work (2 页)
- **2.1 Maximum Collection TSP & TSP with Time Budget**
  - Prize-Collecting TSP (PC-TSP)：访问节点子集最大化收集价值，Goemans-Williamson 近似、Christofides 变体
  - TSP with Time Budget：时间预算约束下的巡回优化，ILS + 2-opt/3-opt、VNS 等主流求解方法
  - Orienteering Problem (OP) & TTDP 的关系 (Vansteenwegen et al., 2011)
  - **Gap**：现有 PC-TSP/OP 研究多在抽象图/公路网，很少在真实 GTFS 时刻表上做，且未考虑几何覆盖等空间指标
- **2.2 Public Transit Routing: RAPTOR and Beyond**
  - Delling et al. 的 Round-Based RAPTOR (局部剪枝: earliest arrival, target pruning)
  - 后续改进：McRAPTOR, rRAPTOR, ULTRA
  - 加速技术：Trip-Based Routing, Arc-Flags 等预处理方法
  - **Gap**：所有方法均以时间最小化/换乘最少为目标，无价值最大化讨论
- **2.3 Beam Search, Pruning & Multi-objective Optimization**
  - Beam Search 在组合优化中的理论分析
  - Pareto Dominance 理论与 NSGA-II (Deb, 2002)
  - Hypervolume Indicator (Zitzler & Thiele, 1999)
  - **Gap**：Beam + Dominance + 罚函数的三层组合剪枝未见于公共交通路径搜索
- **2.4 Smart Trip Recommendation & LLM 趋势** (简述)
  - 元启发式在旅游行程中的应用，LLM 协同趋势
  - **Gap**：LLM 与 RAPTOR 时刻表路由的集成尚未出现 -> Future Work

#### Section 3: Problem Definition (1 页)
- 公共交通网络形式化定义（GTFS 上的 stop-trip-time 模型，含步行边）
- 时间约束价值最大化巡回问题 (TCVMP) 建模：输入、可行性、输出形式
- 双层优化定义：
  - 第一层：维护 Pareto 候选集 $P(r)$（$T_{ride}, S_{unique}, A_{hull}, Q_{cover}$）
  - 第二层：按场景权重函数排序 $f_w(r)$，输出 Top-k
- 约束定义：预算时长、换乘上限、步行上限、是否闭环
- 复杂度分析：从 OP/TTDP 变体归约说明 NP-hard 性

#### Section 4: Proposed Method (2.5 页)
| 小节 | 内容 |
|------|------|
| 4.1 | System Overview - 系统架构与整体流程图 |
| 4.2 | Reverse-Objective RAPTOR - 多维评分函数设计与权重策略 |
| 4.3 | Three-Layer Hybrid Pruning - Beam / Dominance / Negative Score 三层剪枝详解 |
| 4.4 | Geometry-Aware Metrics - 凸包面积与象限覆盖的计算方法 |
| 4.5 | Complexity Analysis - 时间/空间复杂度分析 |
| 4.6 | Correctness & Approximation Notes - 剪枝安全条件与启发式近似边界 |

#### Section 5: Experiments (3 页)
见下方实验设计（5 个实验）

#### Section 6: Conclusion & Future Work (0.5 页)
- 总结三点贡献
- 局限性讨论
- 未来方向：
  - LLM 集成的神经符号混合架构
  - 跨城市公共交通网络的泛化验证
  - 实时动态时刻表的支持

---

## 🧪 实验设计（5 个实验）

### 数据集说明
- **数据来源**：福冈市公共交通 GTFS 数据
- **网络规模**：~X 条线路、~Y 个站点、~Z 个时刻表记录
- **时间窗口**：全日运营时段（约 5:00 - 24:00）
- **查询集设定**：至少 10 个起点 × 3 个出发时刻 × 2 个预算窗口（工作日/周末分层采样）
- **硬件环境**：MacBook Pro M-series / Python 3.12
- **复现实验最小单元**：每个配置重复 5 次，固定随机种子集合 {0,1,2,3,4}

---

### 实验 1：算法综合对比实验（含 Pareto 前沿） ⭐⭐⭐ [核心]
**目的**：证明本文方法在公共交通路径优化中的整体优势

**对比算法（按教授指导：以 PC-TSP / TSP-TB 领域方法为核心基线）**：

| # | 算法 | 类别 | 描述 | 论证目的 |
|---|------|------|------|----------|
| 1 | **ILS + 2-opt** | **PC-TSP/OP 主流** | 迭代局部搜索 + 2-opt 邻域改进 | **教授指定：PC-TSP 领域标准基线** |
| 2 | **VNS** | **TSP-TB 主流** | 变邻域搜索，TSP with Time Budget 常用 | **教授指定：TSP-TB 领域标准基线** |
| 3 | **GA (NSGA-II)** | 元启发式 | 多目标进化算法 | 对比多目标优化主流方法 |
| 4 | SA (Multi-objective) | 元启发式 | 多目标退火 + 邻域操作 | 对比经典优化方法 |
| 5 | McRAPTOR / rRAPTOR | RAPTOR 家族 | 多准则到达时间/换乘优化 | 证明 transit SOTA 在价值最大化上失效 |
| 6 | Pure RAPTOR (No Pruning) | RAPTOR 变体 | 原始 RAPTOR 无剪枝 | 证明剪枝必要性 |
| 7 | Greedy with Lookahead | 简单启发式 | 贪心 + N 步前瞻 (N=3) | 轻量启发式下界 |
| 8 | MIP (Small, optional) | 精确求解 | <=20站点 <=2h 子图上 Gurobi/CBC | 解质量上界参考 |
| - | **Ours (Full)** | **本文** | 逆向 RAPTOR + 三层剪枝 + 几何感知评分 | — |

**评价指标**：
- 执行时间 (ms)
- 总乘车时长 (ride_minutes)
- 路径距离 (km)
- 唯一站点数 (unique_stops)
- 路径段数 (legs)
- 凸包面积 (hull_area) — 地理覆盖范围
- Hypervolume / IGD（多目标前沿质量）
- 可行率与约束违背率（feasibility / violation rate）

**呈现方式**：
- 综合对比表格 (Table)，多出发点取平均
- (执行时间, 解质量) 散点图，标注 Pareto 前沿
- 多指标雷达图 (Radar Chart)
- 显著性检验（Wilcoxon signed-rank，报告 p-value 与效应量）

**状态**：✅ 已有初步数据，需补充 SA/GA Baseline + Pareto 前沿散点图 + 凸包面积指标

---

### 实验 2：三层剪枝消融实验 ⭐⭐⭐ [核心]
**目的**：证明每层剪枝策略的**独立贡献**和**协同效应**

**消融配置**：
| 配置 | Beam | Dominance | Negative | 目的 |
|------|------|-----------|----------|------|
| Full (Ours) | ✅ | ✅ | ✅ | 完整算法 |
| w/o Negative Score | ✅ | ✅ | ❌ | 验证规则层贡献 |
| w/o Dominance | ✅ | ❌ | ✅ | 验证微观层贡献 |
| w/o Beam (Only Dom+Neg) | ❌ | ✅ | ✅ | 验证宏观层贡献 |
| Only Beam | ✅ | ❌ | ❌ | 单层剪枝基线 |
| Only Dominance | ❌ | ✅ | ❌ | 单层剪枝基线 |
| No Pruning | ❌ | ❌ | ❌ | 无剪枝基线 |

**评价指标**：
- 执行时间 (ms) + 加速比
- 内存使用 (标签数 / memory_labels)
- 解质量 (ride_minutes, unique_stops)
- 小规模实例相对最优差距（gap-to-best）

**呈现方式**：
- 消融对比表格
- 标签数量柱状图（展示内存节约效果）

**状态**：✅ 已有初步数据，需补充 w/o Beam 和 w/o Dominance+NegScore 配置

---

### 实验 3：参数敏感性分析 ⭐⭐ [重要]
**目的**：分析关键参数对算法性能的影响，指导实际部署中的参数选择

#### 实验 3a：Beam Width 敏感性
- 测试 Beam Width = 10, 20, 50(默认), 100, 200, 500 的时间与质量权衡。
- **验证改进A**：在此加入 Adaptive Beam Search 策略进行对比。

#### 实验 3b：评分函数权重敏感性
- 测试纯时间(1.0, 0, 0, 0)、时间+站点(0.5, 0.5, 0, 0)、均衡(0.25, 0.25, 0.25, 0.25) 与 偏几何(0.2, 0.1, 0.5, 0.2) 权重的指标偏向。

#### 实验 3c：时间窗口可扩展性
- 测试 2小时、4小时、8小时、12小时和全日的执行时间增长曲线（对数坐标）。

**呈现方式**：
- Beam Width vs 执行时间/解质量 折线图
- 权重配置 vs 各维度指标 热力图 (Heatmap)
- 时间窗口 vs 执行时间 对数坐标图

**状态**：❌ 待实施

---

### 实验 4：多目标场景泛化实验 ⭐⭐ [重要]
**目的**：证明评分架构的**可插拔性**和算法在不同优化目标下的通用性

| 场景 | 优化目标 | 主要评价指标 | 实际应用 |
|------|----------|-------------|----------|
| `longest-duration` | 最大化乘车时间 | ride_minutes | 一日券价值最大化 |
| `most-stops` | 最大化站点覆盖 | unique_stops | 公共交通覆盖率调查 |
| `city-loop` | 最大化地理覆盖 | hull_area | 城市观光巡回 |
| `single-digit` | 主题约束路线 | constraint_ratio | 主题旅游（特定线路） |
| `balanced` | 多维度均衡 | composite_score | 综合路径规划 |

**对比**：每个场景下 Ours vs ILS+2opt vs VNS vs NSGA-II 的表现

**呈现方式**：
- 多场景对比表格
- 场景适应性雷达图
- 跨起点/跨日期箱线图（展示稳定性）

**状态**：❌ 待实施

---

### 实验 5：路径可视化与定性分析 ⭐⭐ [加分项]
**目的**：直观展示本文算法（尤其是几何感知）在寻找高质量复杂路线上的智能表现

**分析内容**：
- 在地图上同时可视化 Ours、Greedy、Dijkstra 等生成的最优路径
- 定性分析比较：展示 Ours 如何通过凸包面积评分向外扩张、避免陷入局部回头路（U-turn）
- 列举具体 case（如"Greedy在天神站陷入循环，而Ours成功覆盖了海滨区域"）

**呈现方式**：
- 各算法最优路径的地图可视化并排对比
- 选定 case 的局部路线特写与分析

**状态**：✅ 已有部分路径可视化，需筛选案例进行定性分析

---

### 统一实验协议（新增）
- **公平性**：所有算法使用相同查询集、相同预算与相同 GTFS 数据版本。
- **终止条件**：为 GA/SA 设定统一 wall-clock 上限与迭代上限，避免不公平比较。
- **随机性控制**：每个算法在 5 个随机种子上重复，报告均值、标准差、95% CI。
- **可复现性**：公开参数配置、数据预处理脚本、运行命令与原始结果 JSON。
- **有效性边界**：明确本文为启发式近似，不提供全局最优保证；在小规模实例上用 MIP 给出参考上界。

---

## 📊 已有实验数据

### benchmark_results.json (初版对比)
```json
{
  "Optimized RAPTOR": {"time_ms": 772, "ride_min": 478, "km": 73.67, "stops": 13},
  "Pure RAPTOR": {"time_ms": 142243, "ride_min": 151, "km": 26.24, "stops": 3},
  "Pure Dijkstra": {"time_ms": 1622, "ride_min": 102, "km": 29.37, "stops": 4},
  "A* Search": {"time_ms": 3261, "ride_min": 264, "km": 80.89, "stops": 5},
  "Greedy": {"time_ms": 0.11, "ride_min": 322, "km": 49.32, "stops": 5}
}
```

### ablation_results.json (初版消融)
```json
{
  "Full (All Pruning)": {"time_ms": 11.6, "ride_min": 372, "labels": 10714},
  "Beam+Dom": {"time_ms": 11.0, "ride_min": 372, "labels": 10634},
  "Beam+NegScore": {"time_ms": 20.3, "ride_min": 372, "labels": 20287},
  "Only Beam": {"time_ms": 19.4, "ride_min": 372, "labels": 20302},
  "Only Dom": {"time_ms": 7197, "ride_min": 286, "labels": 1794663},
  "No Pruning": {"time_ms": 1079, "ride_min": 149, "labels": 755540}
}
```

---

## 📈 图表清单

论文中需要的所有图表：

| 编号 | 类型 | 内容 | 对应实验 |
|------|------|------|----------|
| Fig.1 | 系统架构图 | 整体方法框架 | Sec 4 |
| Fig.2 | 算法流程图 | Reverse-Objective RAPTOR 流程 | Sec 4 |
| Fig.3 | 散点图 | 算法对比与 Pareto 前沿 | 实验 1 |
| Fig.4 | 雷达图 | 多目标评分对比 | 实验 1 & 4 |
| Fig.5 | 柱状图+表格 | 消融实验结果（消融时间与内存） | 实验 2 |
| Fig.6 | 折线图 | Beam Width 参数敏感性 | 实验 3a |
| Fig.7 | 热力图 | 评分权重敏感性 | 实验 3b |
| Fig.8 | 对数坐标图 | 时间窗口可扩展性 | 实验 3c |
| Fig.9 | 地图 | 各算法最优路径可视化对比与 Case 分析 | 实验 5 |
| Tab.1 | 表格 | 符号定义表 | Sec 3 |
| Tab.2 | 表格 | 算法综合对比数据 | 实验 1 |
| Tab.3 | 表格 | 消融实验数据 | 实验 2 |

---

## ⏱️ 时间计划（截止：4月12日）

| 阶段 | 任务 | 日期 | 产出 |
|------|------|------|------|
| **Phase 1** | 补充实验 2 (消融配置) + 实验 1 (GA/SA基线与Pareto前沿) | 3/10 - 3/14 | 完整数据 |
| **Phase 2** | 实验 3 (参数与可扩展性) + 实验 4 (多场景泛化) | 3/15 - 3/20 | 完整数据 |
| **Phase 3** | 实验 5 (定性分析与可视化案例筛选) | 3/21 - 3/25 | 案例分析图文 |
| **Phase 4** | 论文初稿 Sec 1-4 (Introduction → Method) | 3/26 - 3/31 | 初稿 |
| **Phase 5** | 论文 Sec 5-6 (Experiments → Conclusion) + 图表制作 | 4/1 - 4/6 | 完整稿 |
| **Phase 6** | 全文修改润色 + 英文校对 + 格式调整 + 投稿 | 4/7 - 4/12 | 终稿 |

---

## 📚 参考文献

### Maximum Collection TSP & TSP with Time Budget (教授指定对比领域)
1. Balas (1989) - "The Prize Collecting Traveling Salesman Problem" [经典]
2. Goemans & Williamson (1995) - "A general approximation technique for constrained forest problems" — PC-TSP 近似算法
3. Vansteenwegen et al. (2011) - "The Orienteering Problem: A Survey" [经典]
4. MDPI 2024 - "Tourist Trip Design Problem: A Systematic Literature Review"

### Public Transit Routing & RAPTOR
5. Delling et al. (2015) - "Round-Based Public Transit Routing" [经典]
6. INFORMS 2023 - "ULTRA: Unlimited Transfers for Multimodal Journey Planning"
7. Witt (2015) - "Trip-Based Public Transit Routing"

### Multi-objective Optimization & Beam Search
8. Deb et al. (2002) - "A fast and elitist multiobjective genetic algorithm: NSGA-II"
9. Zitzler & Thiele (1999) - "Multiobjective evolutionary algorithms" — Hypervolume
10. Hansen & Mladenovic (2001) - "Variable Neighborhood Search" — VNS 基础
11. Lourenco et al. (2003) - "Iterated Local Search" — ILS 基础

### Geometry in Path Planning
12. de Berg et al. (2008) - "Computational Geometry: Algorithms and Applications"

### LLM in Tourism (Future Work)
13. arXiv 2024 - "LLM-based Travel Recommendation with Real-time Traffic Data"

---

## ✅ 下一步行动

### 实验阶段
1. [ ] 实现 ILS+2-opt 和 VNS 基线（教授指定的 PC-TSP/TSP-TB 领域方法）
2. [ ] 实现 NSGA-II 和 SA 基线
3. [ ] 补充实验 1：全部基线对比 + Pareto前沿 + 凸包指标
4. [ ] 补充实验 2：完善消融配置 (w/o Beam, w/o Dom+Neg)
5. [ ] 新建实验 3：Beam Width、评分权重与时间窗口的敏感性分析
6. [ ] 新建实验 4：5 种场景的泛化实验 (Ours vs ILS vs VNS vs NSGA-II)
7. [ ] 新建实验 5：筛选最优路径进行地图可视化与定性比较

### 写作阶段
1. [ ] 绘制系统架构图 (Fig.1) 和算法流程图 (Fig.2)
2. [ ] 撰写 Section 1-4 初稿（强调与 PC-TSP / TSP-TB 的关系）
3. [ ] 制作所有实验图表 (Fig.3-9, Tab.1-3)
4. [ ] 撰写 Section 5-6 + Abstract
5. [ ] 全文修改润色与格式调整
6. [ ] 投稿
