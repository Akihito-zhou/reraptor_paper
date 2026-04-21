# ReRAPTOR 实验总结（中文）

这份总结按实验 1 到实验 5 的顺序整理，目的是把每个实验“做了什么、为什么做、怎么评价、结果说明了什么”，以及“表和图分别在表达什么”放在一起，便于汇报和和老师讨论。

## 实验1：综合算法对比

### 1. 背景
实验 1 是整篇工作的基础实验，核心问题是：在相同的 GTFS 时刻表约束下，`ReRAPTOR` 是否比代表性基线方法更适合做“时间预算内的高价值公交游程规划”。

这个实验主要回答三个问题：

- 你的方法整体质量是否更高
- 质量提升是否建立在可接受的运行时间之上
- 这种优势在不同预算条件下是否稳定

### 2. 方法
你把 Ours 与多个基线放在同一组 query 上比较，包括：

- NSGA-II
- ILS+2opt
- VNS
- SA
- McRAPTOR
- Pure RAPTOR
- Greedy

实验设置采用：

- 10 个起点
- 3 个出发时刻（07:00 / 10:00 / 14:00）
- 2 个时间预算（4h / 8h）
- 5 个随机种子

也就是说，这个实验是一个标准的综合 benchmark，用来判断你的方法是不是在总体上有竞争力。

### 3. 评价方式
主要评价指标是：

- `composite_score`

辅助指标包括：

- `elapsed_ms`
- `ride_minutes`
- `unique_stops`
- `hull_area`
- `feasible_rate`

另外，你还对 Ours 和 NSGA-II 做了配对 Wilcoxon 检验，用来判断差异是否具有统计显著性。

### 4. 结果
总体上，Ours 的 `composite_score=0.5359`，高于 NSGA-II 的 `0.5010`，提升约 `6.96%`。同时 Ours 的运行时间约 `3640.88 ms`，明显快于 NSGA-II 的 `15276.09 ms`。这说明 Ours 不只是质量更高，而且在“质量-时间”这个权衡上更有优势。

从单项指标上看，NSGA-II 的 `ride_minutes` 和 `unique_stops` 往往更高，但 Ours 的 `hull_area` 提升很明显。这意味着你的方法不是单纯追求“坐得更久”或“经过更多站点”，而是更强调空间覆盖和路线扩张。

预算分开看时，4h 下 Ours 依然领先，但差距较小；8h 下差距更大，说明你的方法在长预算条件下更能体现优势。

### 5. 图表总结
**表：实验1的整体结果**

- 这张表展示所有算法在 60 个 queries 上的平均表现
- 它的核心作用是说明：Ours 在总体 `composite_score` 上是第一，同时运行时间仍然可接受
- 这是证明“整体优势”的主表

**表：实验1的预算分开对比（Ours vs NSGA-II）**

- 这张表把 4h、8h、Overall 分开写
- 它的作用是说明：优势不是只在混合平均后才出现，而是在不同预算下都能观察到
- 这张表也顺带给出显著性结果，说明优势不是随机波动

**图：8h 条件下的多指标面板图**

- 这张图直观展示不同算法在多个指标上的表现
- 它不是为了给精确数值，而是为了让人一眼看出 Ours 强在哪里、弱在哪里
- 它特别能帮助老师理解：为什么 Ours 的综合得分更高，尤其是在空间扩展方面

## 实验2：三层 pruning 的消融实验

### 1. 背景
实验 2 的目的不是证明“你的方法比别人强”，而是证明“你的方法为什么会强”。

`ReRAPTOR` 里有三层 pruning：

- Beam pruning
- Dominance pruning
- Negative-score pruning

这个实验就是把它们一层一层拆开，看每一层分别在发挥什么作用。

### 2. 方法
你设计了多个变体：

- Full
- NoBeam
- NoNeg
- NoDom
- NoDom-NoNeg
- NoBeam-NoNeg
- NoBeam-NoDom-NoNeg

主消融实验沿用了实验 1 的 query 设计，用来确保结论可比较。

此外还有两个补充实验：

- Beam 的 stress test：在更长预算下看 Beam 是否还能控制运行时间
- Negative 的 theme test：在主题约束任务里看 Negative pruning 是否真的提高主题一致性

### 3. 评价方式
主消融重点看：

- `composite_score`
- `elapsed_ms`
- `labels`
- `cap_hit_rate`
- `timeout_rate`

主题补充实验还看：

- `theme_composite`
- `theme_hit_ratio`
- `theme_satisfied_rate`

### 4. 结果
最关键的发现是：`Dominance pruning` 几乎是必需的。

去掉 Dominance 以后：

- `composite_score` 明显下降
- `elapsed_ms` 暴涨
- `labels` 数量急剧膨胀
- `cap_hit_rate` 和 `timeout_rate` 明显上升

这说明没有 Dominance，搜索会迅速失控。

相比之下：

- 去掉 Beam，在普通设置下影响不大
- 去掉 Negative，在普通综合目标下影响也不大

但补充实验说明：

- Beam 在长预算条件下能帮助控制运行时间
- Negative 在主题约束任务中能明显提高语义/主题一致性

因此，这个实验最终支持的是一个“功能分工”结论：

- Dominance pruning：负责保证搜索可计算
- Beam pruning：负责压力条件下的宽度控制
- Negative pruning：负责主题和目标一致性

### 5. 图表总结
**表：主消融结果**

- 这是实验 2 最核心的表
- 它直接展示删掉哪一层以后，系统最先崩掉
- 这张表最重要的信息是：NoDom 的退化最严重，因此 Dominance 是核心组件

**表：Beam 与 Negative 的补充实验摘要**

- 这张表把两个补充实验的结论压缩成一页
- 它不是细节表，而是“解释表”
- 它的作用是补足主消融实验里不明显的部分：Beam 的价值主要在 stress 条件下，Negative 的价值主要在 theme 条件下

**图：正则化指标聚类图**

- 这张图把不同消融版本在多个指标上的表现做了统一归一化
- 用颜色和聚类关系展示各版本的“性能画像”
- 它帮助老师快速看到：Full 是最均衡的，NoDom 类方法明显形成了差的一簇

## 实验3：参数鲁棒性与部署指导

### 1. 背景
如果一个方法只有在极少数参数下才有效，那它的工程价值会很弱。实验 3 就是为了证明：你的方法不是“碰巧调出来”的，而是在一系列合理参数下都能稳定工作。

### 2. 方法
实验 3 分成三部分：

- Exp3a：Beam width sensitivity
- Exp3b：weight profile sensitivity
- Exp3c：budget scalability

具体来说：

- Beam 宽度测试了 10、20、50、100、200、500 和 adaptive
- 权重测试了 default、balanced、geometry、time-only、time+stops 等 profile
- Budget 从 2h 一直拉到 16h

### 3. 评价方式
不同子实验关注点不同：

- Beam：看质量是否稳定、运行时间是否只小幅变化
- Weights：看不同权重是否真的改变路线风格
- Budget：看 runtime 和搜索规模是否随着预算平滑增长

### 4. 结果
Beam 实验说明：在当前 benchmark 下，Beam 改变并不会明显影响最终 `composite_score`，说明结果对 Beam 宽度是稳的，默认值是合理的。

Weights 实验说明：不同 profile 确实会诱导不同类型的路线：

- `Geometry` 更强调空间扩展
- `TimeOnly` 更强调乘车时长
- `Time+Stops` 更强调多站点访问

这说明你的框架不是只能做一种路线，而是可以通过权重控制路线风格。

Budget scalability 结果说明：随着预算从 2h 提高到 16h，运行时间平滑上升，没有出现 feasibility collapse，搜索复杂度虽然增长，但整体是可预测的。

### 5. 图表总结
**表：Beam 宽度摘要**

- 这张表展示同一预算下不同 Beam 配置的表现
- 它最重要的含义是：质量几乎不变，因此默认 Beam 设置是稳妥的

**表：权重设置与路线风格**

- 这张表展示不同权重下 `Ride`、`Stops`、`Hull Area` 如何变化
- 它说明你的打分函数不是装饰性的，而是真的决定了路线风格

**表：Budget scalability**

- 这张表展示预算增大时 runtime、labels、quality 如何变化
- 它的意义是说明系统规模怎么增长，以及增长是否仍然可控

**图：Beam 宽度与性能关系图**

- 这是 Beam 实验的趋势图
- 它的作用是让人一眼看到“质量几乎平、时间只小幅波动”

**图：权重指标热图**

- 这张图把不同 profile 的性能偏向可视化
- 作用是帮助理解“哪一种权重偏向哪一种路线风格”

**图：Budget 与 runtime 增长图**

- 这张图说明 runtime 随 budget 增长的趋势
- 它的重点是“增长是平滑的”，而不是单纯“预算越长越慢”

## 实验4：多目标场景适配实验

### 1. 背景
实验 4 的重点不是继续做一次综合 benchmark，而是回答一个更高层的问题：同一个 `ReRAPTOR` 搜索骨架，能不能通过改目标定义去适配多种任务场景。

### 2. 方法
这里选用了一个代表性子集，而不是完整全网格：

- 3 个起点
- 3 个出发时刻
- 2 个预算
- 2 个 seeds

比较的场景包括：

- `longest-duration`
- `most-stops`
- `city-loop`
- `single-digit`
- `odd-lines`
- `triple-digit`
- `balanced`

比较算法包括 Ours、NSGA-II、ILS+2opt、VNS。

### 3. 评价方式
这组实验不再用单一 `composite_score` 横向比较，而是每个场景看自己的 primary metric。

例如：

- longest-duration 看 ride minutes
- most-stops 看 unique stops
- city-loop 看 hull area
- single-digit / odd-lines 看 line-theme ratio

### 4. 结果
结果非常清楚地表明：你的方法并不是所有场景都第一，但在某些场景上明显更合适。

优势最明显的场景是：

- `most-stops`
- `single-digit`
- `odd-lines`

说明 `ReRAPTOR` 特别适合：

- coverage 型任务
- line-theme 型任务

而在下面这些场景里，NSGA-II 更强：

- `longest-duration`
- `city-loop`
- `balanced`

因此，实验 4 的结论不是“全能最优”，而是“同一框架确实可以迁移到不同目标，而且不同目标下有清晰的强弱边界”。

### 5. 图表总结
**表：scenario summary**

- 这张表按场景列出各算法在 primary metric 上的表现
- 它的作用是说明：不同场景下谁更适合
- 这是实验 4 的主表

**图：scenario adaptability radar**

- 这张图把各算法在多个场景上的相对优势画成雷达图
- 它的作用是非常直观地展示“方法画像”
- Ours 哪些轴更突出、NSGA-II 哪些轴更突出，一眼就能看出来

**图：scenario primary metric boxplots**

- 这张图展示每个场景下 primary metric 的分布而不是均值
- 它的作用是说明结果是否稳定，还是仅仅平均值好看
- 对老师来说，这张图很重要，因为它补充了“波动性”的信息

## 实验5：路线可视化与定性分析

### 1. 背景
前四个实验主要是定量证据，实验 5 则是把这些数字差异转化成可视化路线差异。它回答的问题是：这些分数上的差距，在真实路线图上究竟体现成什么样的行为差异。

### 2. 方法
你没有手工随便挑图，而是按规则自动选了 4 个案例：

- Case A：实验1中 Ours 相对 NSGA-II 综合优势最大的例子
- Case B：实验4中 coverage 表现最突出的例子
- Case C：single-digit 主题场景中最能体现 theme fidelity 的例子
- Case D：triple-digit 困难场景下的失败/对比案例

每个案例都对比：

- Ours
- NSGA-II
- VNS

### 3. 评价方式
这里最重要的不是 runtime，而是：

- 路线是否更连贯
- 是否有明显的局部来回绕行
- 是否覆盖更大的空间范围
- 是否更好地遵守主题约束

### 4. 结果
Case A 和 Case B 是最能支持你核心主张的案例：

- Case A 说明在 balanced objective 下，Ours 的路线更连贯，空间扩展更大
- Case B 说明在 coverage 目标下，Ours 的路线明显更有空间张力

Case C 则展示了一个更细的现象：即使 Ours 和 NSGA-II 在主题 ratio 上打平，它们的路线内容也可能差很多。Ours 给出的是一个更完整、更有内容的 themed route，而 NSGA-II 可能只给出一个很短的、形式上满足条件的路线。

Case D 是一个重要的失败案例，说明在更难的 triple-digit 主题条件下，Ours 的 theme adherence 可能不如 NSGA-II。这种案例的价值在于增强可信度，让整个实验体系更完整。

### 5. 图表总结
**表：案例摘要表**

- 这张表的作用相当于“看图说明书”
- 它告诉读者每个 case 从哪里来、关键数值是什么、阅读重点是什么
- 它帮助老师理解为什么选这几个图，而不是随便挑的

**图：主图（Case A 与 Case B）**

- 这张图对应实验 5 最核心的两类成功案例
- 它的意义是把实验1和实验4里的定量优势，变成路线形状上的可见差异
- 主要看空间扩展、路线连贯性和是否减少无效摆动

**图：补充图（Case C 与 Case D）**

- Case C 说明“分数打平不代表路线质量相同”
- Case D 说明“你的方法在困难主题场景下也有边界和弱点”
- 这张图的价值在于增加解释力和可信度，而不是展示胜利

## 总结

如果把这五个实验连起来看，它们形成了一条很完整的论证链：

- 实验1证明 `ReRAPTOR` 在综合质量上有竞争力
- 实验2证明优势主要来自合理的三层 pruning 设计
- 实验3证明方法在参数上稳定、具有部署价值
- 实验4证明同一个框架能够适配不同场景目标，但强项和边界都很清楚
- 实验5把这些数值结果转化成了可解释的路线行为差异

从论文结构上看，这五个实验并不是互相独立的，而是层层递进的：

- 先证明有效
- 再解释原因
- 再说明稳定性
- 再展示泛化能力
- 最后用可视化解释结果含义

这也是你这组实验设计最完整、最有说服力的地方。
