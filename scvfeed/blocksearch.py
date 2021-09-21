import typing
import requests
import json
from web3 import Web3
import os
import logging
from enum import Enum
from dataclasses import dataclass
from scvfeed.exceptions import FilterNotFoundError


logger = logging.getLogger(__name__)

STAKE_CONTRACT_ADDRESS = '0x4e6b968db22ab24fa58568c3a1624092ad257017'

stake_abi = [{"name": "stake",
              "inputs": [{"internalType": "uint256", "name": "caveId", "type": "uint256"},
                         {"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
              "type": "function"}]


def get_bsc_abi(address: str):
    abi_endpoint = f"https://api.bscscan.com/api?module=contract&action=getabi&address={address}"
    abi = json.loads(requests.get(abi_endpoint).json()['result'])
    return abi


PMON_TOKEN_TOPIC = '0x00000000000000000000000085f0e02cb992aa1f9f47112f815f519ef1a59e2d'


class TradeSide(Enum):
    SELL = 1
    BUY = 2

    @classmethod
    def of(cls, side: int):
        return cls.SELL if side == cls.SELL.value else cls.BUY

    def __str__(self):
        return 'SELL' if self == TradeSide.SELL else 'BUY'


BSC_PROVIDER = os.getenv("BSC_PROVIDER", "wss://bsc-ws-node.nariox.org:443")


@dataclass
class OfferInfo:
    token_id: int
    side: TradeSide
    price: int
    tx: str

    def __eq__(self, other):
        return self.tx == other.tx


# EvNewOffer (
#   index_topic_1 address user,
#   index_topic_2 address nft,
#   index_topic_3 uint256 tokenId,
#   uint256 price,
#   uint8 side,
#   uint256 id
# )
class ScvBlockSearch:
    CONTRACT = '0x9437E3E2337a78D324c581A4bFD9fe22a1aDBf04'
    NEW_OFFER_EVT = 'EvNewOffer(address,address,uint256,uint256,uint8,uint256)'
    TOKEN_DECIMAL = 1E18

    def __init__(self, provider):
        if 'wss' in provider:
            self.web3 = Web3(Web3.WebsocketProvider(provider))
        else:
            self.web3 = Web3(Web3.HTTPProvider(provider))
        self.scv_filter = self.web3.eth.filter({
            "address": self.CONTRACT,
            "topics": [Web3.sha3(text=self.NEW_OFFER_EVT).hex()]
        })

    @classmethod
    def _handle_new_evt(cls, evt) -> OfferInfo:
        logger.debug(f"processing {evt}")
        token_topic = evt['topics'][2].hex()
        if token_topic == PMON_TOKEN_TOPIC:
            token_id = int.from_bytes(evt['topics'][3], 'big')
            data = evt['data'].replace('0x', '')
            price_hexstr, side_hexstr, _ = [data[i:i + 64] for i in range(0, len(data), 64)]
            side = TradeSide.of(int(f"0x{side_hexstr}", 16))
            price = int(f"0x{price_hexstr}", 16)
            tx = evt['transactionHash'].hex()
            logger.info("new event %s %d with price %.2f, tx %s", side, token_id, price, tx)
            return OfferInfo(token_id=token_id, side=side, price=price, tx=tx)
        return OfferInfo(0, TradeSide.SELL, 0, '')

    def get_sell_event(self) -> typing.Generator:
        try:
            new_entries = self.scv_filter.get_new_entries()
        except Exception as e:
            logger.exception(str(e))
            raise FilterNotFoundError from e

        # to avoid duplicated event emit
        last_offer_info = OfferInfo(0, TradeSide.SELL, 0, '')
        for e in new_entries:
            try:
                offer_info = self._handle_new_evt(e)
            except Exception as e:
                logging.exception(str(e))
                continue
            if offer_info.side == TradeSide.SELL and offer_info != last_offer_info:
                last_offer_info = offer_info
                yield offer_info
