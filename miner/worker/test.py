# import io
#
# import numpy as np
# import requests as requests
# from PIL import Image
#
# response = requests.get(
#     'https://storage.yandexcloud.net/place-recognition/google_pano/KzCpnCLybCyYweFkD6ucwQ/pano.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=79bQMfkbQTwv3KG0_hFb%2F20230528%2Fru-central1%2Fs3%2Faws4_request&X-Amz-Date=20230528T210956Z&X-Amz-Expires=3600&X-Amz-Signature=A5DD0BA76EDCA6208975DF46FA4EB9EFD10C0053B80784B49FEB642468BD0F3C&X-Amz-SignedHeaders=host')
#
# metadata = requests.get(
#     'https://storage.yandexcloud.net/place-recognition/google_pano/KzCpnCLybCyYweFkD6ucwQ/meta.json?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=79bQMfkbQTwv3KG0_hFb%2F20230528%2Fru-central1%2Fs3%2Faws4_request&X-Amz-Date=20230528T212215Z&X-Amz-Expires=3600&X-Amz-Signature=C9A43C812B2024A9D67E3B9D4EEE3946D1E5311B85E97C6A12A17E9844AD78C4&X-Amz-SignedHeaders=host').json()
#
# h = metadata['resolution']['height']
# w = metadata['resolution']['width']
#
# bytes_im = Image.open(io.BytesIO(response.content)).convert('RGB').crop((0, 0, w, h))
#
# # response = requests.get('https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png', stream=True).raw
# #
# # bytes_im = Image.open(response).convert('RGB')
#
# import numpy as np
#
# concatenated = Image.fromarray(
#     np.concatenate(
#         [bytes_im, bytes_im],
#         axis=1
#     )
# )
#
# print(concatenated)
#
# concatenated.save("test.jpg")
#
from loguru import logger

from google_pano import google_meta_download, google_pano_download
from miner.worker import s3
from models.pano import PanoMetaRead

pano_id = "KzCpnCLybCyYweFkD6ucwQ"

pano_meta = google_meta_download(pano_id)

for pano in pano_meta.panos:
    img = google_pano_download(pano_meta, pano, 10)
    logger.info(f"Pano {pano_id} meta downloaded")
    s3.upload_meta(
        bucket='place-recognition',
        key=f'google_pano/{pano_id}/meta.json',
        json_data=PanoMetaRead.from_orm(pano_meta).json(),
    )
    logger.info(f"Pano {pano_id} pano downloaded")
    s3.upload_pano(
        bucket='place-recognition',
        key=f'google_pano/{pano_id}/pano.jpg'.replace('pano.jpg', f'{pano.width}x{pano.height}.jpg'),
        img=img,
    )
    logger.info(f"Pano {pano_id} {pano.width}x{pano.height}.jpg pano uploaded to s3")
