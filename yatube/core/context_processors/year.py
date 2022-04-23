from django.utils import timezone


def year(request):
    year = timezone.now().year
    context = {
        'year': year,
    }
    return (context)
