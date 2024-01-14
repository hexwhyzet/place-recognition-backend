from dataclasses import dataclass
from enum import Enum


class Protocol(str, Enum):
    http = 'http'
    https = 'https'


@dataclass
class NetworkConfig:
    protocol: Protocol
    host: str
    ip: int


DEV = NetworkConfig(protocol=Protocol.http, host='localhost', ip=80)
PROD = NetworkConfig(protocol=Protocol.https, host='8.8.8.8', ip=80)

DEFAULT = DEV


def get_url(path: str, config: NetworkConfig = None):
    if config is None:
        config = DEFAULT
    return f'{config.protocol.value}://{config.host}:{config.ip}/{path}'
