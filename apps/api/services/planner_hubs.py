"""
Transfer Hub Definitions / 換乗枢纽定义

Defines major transfer hub stations in Fukuoka City that should be allowed
more visits during route planning to enable better east-west coverage.
"""

# 換乗枢纽：这些站点可以被多次访问
# Transfer hubs: these stations can be visited multiple times
TRANSFER_HUBS = {
    # 博多站周边 / Hakata Station area
    "博多駅",
    "博多バスターミナル",
    "博多駅前",
    "博多駅筑紫口",
    # 天神周边 / Tenjin area
    "天神",
    "天神バスセンター",
    "西鉄福岡（天神）",
    "天神中央郵便局前",
    "天神北",
    "天神南",
    # 其他主要换乘点 / Other major transfer points
    "キャナルシティ博多前",
    "福岡空港",
    "中洲",
    "祇園町",
    "呉服町",
}

# 枢纽站的最大访问次数
# Maximum visit count for hub stations
HUB_MAX_VISITS = 4

__all__ = ["TRANSFER_HUBS", "HUB_MAX_VISITS"]
