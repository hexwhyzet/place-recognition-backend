import sys

import uvicorn as uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

import db
import google_pano
from models import Pano, PanoType, S3Path, IssueTask
from s3 import BUCKET

from loguru import logger

app = FastAPI()


def get_pano_path(pano: Pano):
    return S3Path(
        bucket=BUCKET,
        path=f"{pano.type}/{pano.id}/pano.jpg"
    )


def get_meta_path(pano: Pano):
    return S3Path(
        bucket=BUCKET,
        path=f"{pano.type}/{pano.id}/meta.json"
    )


@app.get("/issue_task/{ip}", response_class=JSONResponse)
def issue_task(_: Request, ip: str):
    pano: Pano = db.issue_task(ip)
    if pano:
        logger.info(f"Not downloaded pano was found {pano.id} for ip {ip}")
        return JSONResponse(jsonable_encoder(IssueTask(
            pano=pano,
            pano_path=get_pano_path(pano),
            meta_path=get_meta_path(pano)
        )))
    else:
        logger.info(f"No free pano was found for ip {ip}")
    return JSONResponse(status_code=404, content="No panos found to download")


@app.post("/finish_task/{pano_id}", response_class=JSONResponse)
def finish_task(_: Request, pano_id: str):
    pano: Pano = db.get_pano(pano_id)
    if not pano:
        logger.error(f"Pano {pano_id} was not found in database, could not finish task")
        return JSONResponse(status_code=404, content="Pano not found")
    else:
        logger.info(f"Pano {pano_id} was found")
    if pano.type == PanoType.GOOGLE_PANO:
        # meta_path = get_meta_path(pano)
        # logger.info(f"Pano {pano_id} meta downloaded")
        # meta_dict = google_pano.check_meta(meta_path)
        # if not meta_dict:
        #     logger.error(f"Pano {pano_id} meta is incorrect")
        #     return JSONResponse(status_code=404, content="Meta is incorrect")
        # else:
        #     logger.info(f"Pano {pano_id} meta ok")
        # pano_path = get_pano_path(pano)
        # if not google_pano.check_pano(pano_path, meta_dict):
        #     logger.error(f"Pano {pano_id} pano is incorrect")
        #     return JSONResponse(status_code=404, content="Pano is incorrect")
        # else:
        #     logger.info(f"Pano {pano_id} pano ok")
        db.finish_task(pano_id)
        logger.info(f"Task for {pano_id} was finished")
        return
    logger.error(f"Pano type {pano.type} is wrong")
    return JSONResponse(status_code=404, content="Pano has wrong type")


@app.post("/add_pano/{pano_type}/{pano_id}", response_class=JSONResponse)
def add_pano(_: Request, pano_type: PanoType, pano_id: str):
    if pano_type == PanoType.GOOGLE_PANO:
        if not google_pano.check_pano_id(pano_id):
            return JSONResponse(status_code=404, content="Wrong pano id")
        else:
            logger.error(f"Pano id {pano_id} is wrong")
    else:
        logger.error(f"Pano type {pano_type} is wrong")
    db.add_pano(pano_id, pano_type)
    return


@app.get("/echo", response_class=JSONResponse)
def add_pano(_: Request):
    return JSONResponse(status_code=200, content="Hello World!")
