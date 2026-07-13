from datetime import timedelta

from app.calendar.utils import has_slot_conflict, lock_field_hour, week_start_for
from app.extensions import db
from app.models import Reservation


def generate_tournament_slots(tournament, start_date, week_plan, user_id):
    """week_plan: her hafta için bir (weekday, hour) çiftleri listesi.
    Lig usulünde aynı liste week_count kez tekrar eder; eleme usulünde her hafta kendi listesine sahiptir.
    Çakışan slotlar atlanır. Döner: (created: list[Reservation], skipped: list[dict])."""
    base_week_start = week_start_for(start_date)
    created = []
    skipped = []

    for week_offset, day_hour_pairs in enumerate(week_plan):
        week_monday = base_week_start + timedelta(weeks=week_offset)
        for weekday, hour in day_hour_pairs:
            slot_date = week_monday + timedelta(days=weekday)
            lock_field_hour(tournament.field_id, hour)
            if has_slot_conflict(tournament.field_id, slot_date, hour, "turnuva"):
                skipped.append({"date": slot_date, "hour": hour})
                continue
            reservation = Reservation(
                field_id=tournament.field_id,
                reservation_type="turnuva",
                tournament_id=tournament.id,
                customer_name=tournament.customer_name,
                phone=tournament.phone,
                deposit_paid=tournament.deposit_paid,
                reservation_date=slot_date,
                reservation_hour=hour,
                notes=tournament.notes,
                created_by_user_id=user_id,
            )
            db.session.add(reservation)
            db.session.flush()
            created.append(reservation)

    return created, skipped
