import argparse
import json
import time

import requests as requests
from loguru import logger

import s3
from google_pano import google_meta_download, google_pano_download

SLEEP_SECONDS = 5


def run_task(task_data: dict, threads_num: int):
    logger.info(f"Task launched")
    pano_type = task_data['pano']['type']
    pano_id = task_data['pano']['id']
    logger.info(f"Task for pano {pano_id} ({pano_type}) started")
    if pano_type == 'google_pano':
        try:
            meta = google_meta_download(pano_id)
            logger.info(f"Pano {pano_id} meta downloaded")
            s3.upload_meta(
                bucket=task_data['meta_path']['bucket'],
                key=task_data['meta_path']['path'],
                json_data=json.dumps(meta),
            )
            logger.info(f"Pano {pano_id} meta uploaded to s3")
            img = google_pano_download(pano_id, meta, threads_num)
            logger.info(f"Pano {pano_id} pano downloaded")
            s3.upload_pano(
                bucket=task_data['pano_path']['bucket'],
                key=task_data['pano_path']['path'],
                img=img,
            )
            logger.info(f"Pano {pano_id} pano uploaded to s3")
            return True
        except Exception as e:
            logger.error(f"Task failed {e}")
    return False


GLOBAL_IP = requests.get('https://api.ipify.org').content.decode('utf8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manager_ip', type=str, help='Manager ip:port', required=True)
    parser.add_argument('--delay', type=int, help='Delay in seconds between task requests', required=False,
                        default=SLEEP_SECONDS)
    parser.add_argument('--threads_num', type=int, help='Delay in seconds', required=False, default=5)
    args = parser.parse_args()

    while True:
        time.sleep(SLEEP_SECONDS)
        try:
            response = requests.get(f"http://{args.manager_ip}/issue_task/{GLOBAL_IP}")
            logger.info(f"Request to manager {args.manager_ip} was sent")
            success = response.status_code == 200
            if success:
                logger.info(f"Request to manager {args.manager_ip} is successful")
                response_data = response.json()
                if run_task(response_data, threads_num=args.threads_num):
                    pano_id = response_data['pano']['id']
                    requests.post(f"http://{args.manager_ip}/finish_task/{pano_id}")
            else:
                logger.info(f"Request to manager {args.manager_ip} is unsuccessful")
        except Exception as e:
            print(e)
