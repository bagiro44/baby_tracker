"""
Модели данных для трекера
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SleepRecord:
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: int
    started_by: int
    ended_by: Optional[int]
    created_at: datetime
    updated_at: datetime

@dataclass
class FeedingRecord:
    id: int
    feeding_type: str  # "Грудное" или "Искусственное"
    amount_ml: Optional[int]
    user_id: int
    timestamp: datetime
    created_at: datetime
    reminder_sent: bool
    breast_feeding_type: Optional[str]  # "Начало кормления" или "Конец кормления"
    last_breast: Optional[str]  # "Левая" или "Правая"

@dataclass
class WeightRecord:
    id: int
    weight_grams: int
    user_id: int
    timestamp: datetime
    created_at: datetime
    note: str

@dataclass
class Statistics:
    total_sleep_sessions: int
    completed_sleep_sessions: int
    active_sleep: bool
    avg_duration: str
    total_feedings: int
    breast_feedings: int
    bottle_feedings: int
    today_feedings: int
    today_bottle_feedings: int
    total_bottle_amount: int
    total_bottle_all_time: int
    last_bottle_feeding: str
    last_weight: str
    weight_trend: str
    weight_records_count: int