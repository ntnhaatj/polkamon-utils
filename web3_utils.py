import requests
import json
from web3 import Web3


TOKEN_DECIMAL = 1E18
BSC_WEB3_PROVIDER = "https://bsc-dataseed.binance.org/"

STAKE_CONTRACT_ADDRESS = '0x4e6b968db22ab24fa58568c3a1624092ad257017'

stake_abi = [{"name": "stake",
              "inputs": [{"internalType": "uint256", "name": "caveId", "type": "uint256"},
                         {"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
              "type": "function"}]
web3 = Web3(Web3.HTTPProvider(BSC_WEB3_PROVIDER))
# contract = web3.eth.contract(address=STAKE_CONTRACT_ADDRESS, abi=stake_abi)


def get_bsc_abi(address: str):
    abi_endpoint = f"https://api.bscscan.com/api?module=contract&action=getabi&address={address}"
    abi = json.loads(requests.get(abi_endpoint).json()['result'])
    return abi
