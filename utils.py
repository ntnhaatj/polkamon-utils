import requests
from requests.exceptions import RequestException
from functools import reduce
from datetime import datetime, timedelta, date
import backoff

METADATA_URL = "http://meta.polkamon.com/meta?id={id}"
RANK_AND_SHARE = "https://pkm-collectorstaking.herokuapp.com/rankAndShare/{score}"
LEADERBOARD = "https://pkm-collectorstaking.herokuapp.com/leaderboard?limit={limit}"
OVERALL = "https://nft-tracker.net/_next/data/FYCcAwpjHdPYAgMShl2aN/collections/polychainmonsters/statistics.json?slug=polychainmonsters&tab=overall"


@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_tries=2)
def get_metadata(m_id: str) -> dict:
    url = METADATA_URL.format(id=m_id)
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()

    raise RequestException


def get_share_on_score(score: int) -> float:
    url = RANK_AND_SHARE.format(score=score)
    res = requests.get(url)
    if res.status_code == 200:
        return float(res.json()['share']) / 100

    raise RequestException("")


def get_total_scores() -> int:
    foo_score = 1_000_000
    return int(foo_score / get_share_on_score(foo_score))


def get_leaderboard(anchor_rank: int = 10):
    if anchor_rank > 100:
        raise NotImplementedError(f"not support over {100}")

    url = LEADERBOARD.format(limit=min(100, anchor_rank + 3))
    res = requests.get(url)
    if res.status_code == 200:
        leaderboard = [{**u, 'rank': i + 1} for i, u in enumerate(res.json())]
        cutoff_from = anchor_rank - 3
        return leaderboard[cutoff_from:]

    raise RequestException("")


def transform_displayed_info(info: dict) -> str:
    return "\n".join([f"{k}: {v}" for k, v in info.items()])


def get_datatype_from_list(data_type, attrs: list):
    for a in attrs:
        try:
            return data_type.of(a)
        except NotImplementedError:
            pass
    return None


def get_overall_stats():
    res = requests.get(OVERALL)
    if res.status_code == 200:
        return res.json()

    raise RequestException


def get_birthday_stats():
    """
    :return:
    [
      {
        "count": 42384,
        "value": {
          "year": 2021,
          "month": 5,
          "day": 26
        }
      },
      {
        "count": 28791,
        "value": {
          "year": 2021,
          "month": 4,
          "day": 3
        }
      },
    ]
    """
    try:
        birthday = get_overall_stats()['pageProps']['initialCollection']['attributes']['Birthday']
    except IndexError:
        raise IndexError("overall API has changed")
    return birthday


def get_weekly_birthday_snapshot():
    def transform_bdate(b: dict):
        v = b['value']
        s = f"{v['year']}-{v['month']}-{v['day']}"
        date = datetime.strptime(s, "%Y-%m-%d").date()
        return {**b, 'value': date}
    birthday = get_birthday_stats()
    today = date.today()
    offset = (today.weekday() - 2) % 7
    last_date_after_snapshot = today - timedelta(days=offset)
    last_7_days_stats = list(filter(lambda b: b['value'] >= last_date_after_snapshot,
                                    map(transform_bdate, birthday)))
    total = reduce(lambda total, s: total + int(s['count']), last_7_days_stats, 0)
    return last_7_days_stats, total
