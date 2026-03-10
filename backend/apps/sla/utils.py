import math
from datetime import timedelta


def add_business_days(start_dt, hours):
    """
    Retorna um datetime avançando `hours` horas em dias úteis
    (segunda a sexta, excluindo feriados cadastrados em Holiday).

    Lógica:
      - Converte horas em dias: days = ceil(hours / 24)
      - Avança esse número de dias úteis a partir de start_dt
      - O horário do resultado é o mesmo de start_dt
    """
    from apps.sla.models import Holiday

    days_to_add = math.ceil(hours / 24)
    holidays = set(Holiday.objects.values_list('date', flat=True))

    current = start_dt.date()
    added = 0
    while added < days_to_add:
        current += timedelta(days=1)
        # weekday(): 0=seg … 4=sex, 5=sab, 6=dom
        if current.weekday() < 5 and current not in holidays:
            added += 1

    # Recombina com o horário original e o timezone de start_dt
    import datetime
    return start_dt.replace(
        year=current.year,
        month=current.month,
        day=current.day,
    )
