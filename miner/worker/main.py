import argparse
import sys
import time

import requests as requests
from loguru import logger

import miner.worker.s3 as s3
from miner.worker.google_pano import google_meta_download, google_pano_download
from models.pano import PanoMetaRead

SLEEP_SECONDS = 5


def run_task(task_data: dict, threads_num: int):
    import os
    logger.info(os.getenv('AWS_SERVER_PUBLIC_KEY'))
    logger.info(os.getenv('AWS_SERVER_SECRET_KEY'))
    logger.info(f"Task launched")
    logger.info(task_data)
    pano_type = task_data['pano']['type']
    pano_id = task_data['pano']['id']
    logger.info(f"Task for pano {pano_id} ({pano_type}) started")
    if pano_type == 'google_pano':
        try:
            pano_meta = google_meta_download(pano_id)
            logger.info(f"Pano {pano_id} meta downloaded")
            s3.upload_meta(
                bucket=task_data['meta_path']['bucket'],
                key=task_data['meta_path']['path'],
                json_data=PanoMetaRead.from_orm(pano_meta).json(),
            )
            # session.add(pano_meta)
            logger.info(f"Pano {pano_id} meta uploaded to s3")
            for pano in pano_meta.panos:
                img = google_pano_download(pano_meta, pano, threads_num)
                s3.upload_pano(
                    bucket=task_data['pano_path']['bucket'],
                    key=task_data['pano_path']['path'].replace('pano.jpg', f'{pano.width}x{pano.height}.jpg'),
                    img=img,
                )
                logger.info(f"Pano {pano_id} pano downloaded")
                # session.add(pano)
                logger.info(f"Pano {pano_id} {pano.width}x{pano.height}.jpg pano uploaded to s3")
            return True
        except Exception as e:
            logger.error(f"Task failed {e}")
    return False


def main(argv):
    GLOBAL_IP = requests.get('https://api.ipify.org').content.decode('utf8')

    parser = argparse.ArgumentParser()
    parser.add_argument('--manager_ip', type=str, help='Manager ip:port', required=True)
    parser.add_argument('--delay', type=int, help='Delay in seconds between task requests', required=False,
                        default=SLEEP_SECONDS)
    parser.add_argument('--threads_num', type=int, help='Delay in seconds', required=False, default=5)
    args = parser.parse_args()

    # with GetSQLModelSession() as session:
    while True:
        time.sleep(SLEEP_SECONDS)
        try:
            logger.info(f"http://{args.manager_ip}/issue_task/{GLOBAL_IP}")
            response = requests.get(f"http://{args.manager_ip}/issue_task/{GLOBAL_IP}")
            logger.info(f"Request to manager {args.manager_ip} was sent")
            if response.status_code == 200:
                logger.info(f"Request to manager {args.manager_ip} is successful")
                response_data = response.json()
                if run_task(response_data, threads_num=args.threads_num):
                    pano_id = response_data['pano']['id']
                    requests.post(f"http://{args.manager_ip}/finish_task/{pano_id}")
            else:
                logger.info(
                    f"Request to manager {args.manager_ip} is unsuccessful: {response.content.decode('utf8')}")
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main(sys.argv)
