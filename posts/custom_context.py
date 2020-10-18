import datetime as dt


def get_year(request):
    year = dt.datetime.now().year
    return {
        "year": year
    }