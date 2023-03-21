import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    x = datetime.datetime.now()
    return {
        'year': x.year
    }
