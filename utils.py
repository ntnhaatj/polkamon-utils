import requests
from requests.exceptions import RequestException

METADATA_URL = "http://meta.polkamon.com/meta?id={id}"
RANK_AND_SHARE = "https://pkm-collectorstaking.herokuapp.com/rankAndShare/{score}"


def get_metadata(m_id: str) -> dict:
    url = METADATA_URL.format(id=m_id)
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()

    raise RequestException("")


def get_total_scores() -> int:
    foo_score = 1_000_000
    url = RANK_AND_SHARE.format(score=foo_score)
    res = requests.get(url)
    if res.status_code == 200:
        share = res.json()['share']
        return int(foo_score / share)

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
