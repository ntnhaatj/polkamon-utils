import requests
from requests.exceptions import RequestException
import backoff

METADATA_URL = "http://meta.polkamon.com/meta?id={id}"


@backoff.on_exception(backoff.expo, RequestException, max_tries=3)
def get_metadata(m_id: str) -> dict:
    url = METADATA_URL.format(id=m_id)
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()

    raise RequestException("")
