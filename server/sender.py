from db.postgres import GetSQLModelSession
from db.qdrant import GetQdrantClient
from tools.descriptor import from_local_image, send_recognize_request

QDRANT_CLIENT = GetQdrantClient()
RELEASE_NAME = "sharp_hofstadter"

if __name__ == '__main__':
    image = from_local_image('tmp/img16.png')
    with GetSQLModelSession() as session:
        print("Server sent!")
        response = send_recognize_request(image, release_name=RELEASE_NAME, debug_token='sender')
        print(response.content.decode("utf-8"))
