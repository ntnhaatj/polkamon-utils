import requests
from requests.exceptions import RequestException

METADATA_URL = "http://meta.polkamon.com/meta?id={id}"


def get_metadata(m_id: str) -> dict:
    url = METADATA_URL.format(id=m_id)
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()

    raise RequestException("")


def transform_displayed_info(info: dict) -> str:
    return "\n".join([f"{k}: {v}" for k, v in info.items()])
