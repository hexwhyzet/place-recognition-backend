from os import environ

from qdrant_client import QdrantClient


def GetQdrantClient():
    return QdrantClient(host=environ.get('QDRANT_HOST'), grpc_port=6334, prefer_grpc=True)
