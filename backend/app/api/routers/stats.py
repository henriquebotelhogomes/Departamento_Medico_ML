"""Statistics endpoint for the dashboard."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.ml.labels import CLASS_LABELS
from app.models.prediction import Prediction
from app.schemas.prediction import ClassCount, StatsOut, TimePoint

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
async def get_stats(current_user: CurrentUser, db: DbSession) -> StatsOut:
    base = Prediction.user_id == current_user.id

    total = await db.scalar(select(func.count()).select_from(Prediction).where(base)) or 0
    avg_conf = await db.scalar(select(func.avg(Prediction.confidence)).where(base)) or 0.0

    # Counts per class (fill zeros for classes never predicted).
    rows = await db.execute(
        select(Prediction.predicted_class, func.count())
        .where(base)
        .group_by(Prediction.predicted_class)
    )
    counts = {int(cls): int(cnt) for cls, cnt in rows.all()}
    by_class = [
        ClassCount(class_id=cid, label=label, count=counts.get(cid, 0))
        for cid, label in CLASS_LABELS.items()
    ]

    # Predictions over time (bucketed by day, aggregated in Python for DB portability).
    created = await db.execute(select(Prediction.created_at).where(base))
    day_counter: Counter[str] = Counter(dt.strftime("%Y-%m-%d") for (dt,) in created.all())
    over_time = [TimePoint(date=day, count=n) for day, n in sorted(day_counter.items())]

    return StatsOut(
        total_predictions=int(total),
        average_confidence=round(float(avg_conf), 4),
        by_class=by_class,
        over_time=over_time,
    )
