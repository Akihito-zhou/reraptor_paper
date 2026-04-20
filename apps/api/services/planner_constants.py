from __future__ import annotations

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"  # 数据目录 / データ保存場所
TIMETABLE_PREFIX = "timetable_"  # 时刻表文件前缀 / ダイヤCSVの接頭辞
SEGMENTS_PREFIX = "segments_"  # 片段文件前缀 / セグメントCSVの接頭辞

START_TIME_MINUTES = 7 * 60  # 默认开始时间07:00 / デフォルト開始時刻07:00
TRANSFER_BUFFER_MINUTES = 3  # 最小换乘缓冲 / 乗換最低待機時間
MAX_BRANCH_PER_EXPANSION = 5  # Beam搜索分支上限 / ビーム探索の分岐数
MAX_QUEUE_SIZE = 1500  # 优先队列容量 / 優先度キュー上限
MAX_EXPANSIONS = 90000  # 搜索扩展步数 / 探索ステップ上限
MAX_LOOKAHEAD_MINUTES = 240  # 从候选出发时刻向后查看的最大时间窗 / 次の便を探す時間窓（分）
REST_STOP_THRESHOLD = 15  # 触发休息建议的等待分钟 / 休憩提案を出す待ち時間
DEFAULT_REALTIME_CACHE_SECONDS = 120  # 实时API缓存秒数 / リアルタイムAPIキャッシュ秒
MAX_LABELS_PER_STOP = 5  # 每站保留的标签数 / 各停留所のラベル保持数
MAX_TRANSFERS = 50  # RAPTOR允许的换乘轮数 / RAPTORの最大ラウンド
ALL_QUADRANTS_MASK = 1 | 2 | 4 | 8  # 四象限全覆盖位掩码 / 4象限制覇ビット
BOUNDARY_BIN_COUNT = 18  # 边界角度分桶 / 境界角度ビン数
BOUNDARY_MIN_DIST_KM = 0  # 视为边界站的最小距离 / 境界候補の最小距離
BOUNDARY_MAX_DIST_KM = 10.0  # 视为边界站的最大距离 / 境界候補の最大距離
MAX_ROUTES_FOR_RAPTOR = 50000  # 预加载线路数 (Increased from 400 to cover all suburbs in experiments)
MAX_TRIPS_PER_ROUTE = 60  # 每线路保留班次数 / 路線あたりの便数
MAX_WALK_DISTANCE_KM = 1.0  # 最大步行距离 (km) / 最大徒歩距離

# ===== Challenge Difficulty Tiers / チャレンジ難易度 =====
# 初級: <2h, 中級: 2-4h, 高級: 4-6h, 特級: 8h+
DIFFICULTY_TIERS = {
    "beginner": {
        "name_ja": "初級",
        "name_en": "Beginner",
        "emoji": "🌱",
        "min_minutes": 0,
        "max_minutes": 120,
        "target_minutes": 90,
        "color": "#4CAF50",  # Green
        "description_ja": "気軽に楽しめる2時間以内のルート",
        "description_en": "Easy routes under 2 hours",
    },
    "intermediate": {
        "name_ja": "中級",
        "name_en": "Intermediate",
        "emoji": "🚌",
        "min_minutes": 120,
        "max_minutes": 240,
        "target_minutes": 180,
        "color": "#2196F3",  # Blue
        "description_ja": "半日で楽しむ2〜4時間のルート",
        "description_en": "Half-day routes of 2-4 hours",
    },
    "advanced": {
        "name_ja": "高級",
        "name_en": "Advanced",
        "emoji": "🏆",
        "min_minutes": 240,
        "max_minutes": 360,
        "target_minutes": 300,
        "color": "#FF9800",  # Orange
        "description_ja": "本格的な4〜6時間のチャレンジ",
        "description_en": "Serious 4-6 hour challenges",
    },
    "expert": {
        "name_ja": "特級",
        "name_en": "Expert",
        "emoji": "👑",
        "min_minutes": 480,
        "max_minutes": 720,
        "target_minutes": 540,
        "color": "#9C27B0",  # Purple
        "description_ja": "究極の8時間超えエンデュランス",
        "description_en": "Ultimate 8+ hour endurance",
    },
}


def get_difficulty_tier(ride_minutes: int) -> dict:
    """Get difficulty tier based on ride duration."""
    if ride_minutes < 120:
        return DIFFICULTY_TIERS["beginner"]
    elif ride_minutes < 240:
        return DIFFICULTY_TIERS["intermediate"]
    elif ride_minutes < 360:
        return DIFFICULTY_TIERS["advanced"]
    else:
        return DIFFICULTY_TIERS["expert"]

REST_SUGGESTIONS = [
    "コンビニで飲み物を補給しよう",
    "近くのベーカリーでテイクアウトを",
    "周辺を5分だけ散策して気分転換を",
    "ベンチで次のルートを確認しよう",
    "軽くストレッチしてリフレッシュ",
]

__all__ = [
    "DATA_DIR",
    "TIMETABLE_PREFIX",
    "SEGMENTS_PREFIX",
    "START_TIME_MINUTES",
    "TRANSFER_BUFFER_MINUTES",
    "MAX_BRANCH_PER_EXPANSION",
    "MAX_QUEUE_SIZE",
    "MAX_EXPANSIONS",
    "MAX_LOOKAHEAD_MINUTES",
    "REST_STOP_THRESHOLD",
    "DEFAULT_REALTIME_CACHE_SECONDS",
    "MAX_LABELS_PER_STOP",
    "MAX_TRANSFERS",
    "ALL_QUADRANTS_MASK",
    "BOUNDARY_BIN_COUNT",
    "BOUNDARY_MIN_DIST_KM",
    "BOUNDARY_MAX_DIST_KM",
    "MAX_ROUTES_FOR_RAPTOR",
    "MAX_TRIPS_PER_ROUTE",
    "MAX_WALK_DISTANCE_KM",
    "REST_SUGGESTIONS",
    "DIFFICULTY_TIERS",
    "get_difficulty_tier",
]
