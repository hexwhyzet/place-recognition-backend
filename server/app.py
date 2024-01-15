import datetime
import time
import uuid
from typing import List, Optional, Callable

from fastapi import FastAPI, HTTPException, status, Request, Response, APIRouter
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel

from db.postgres import GetSQLModelSession
from db.qdrant import GetQdrantClient
from libs.coordinates import Coordinates, CoordinateSystem
from libs.predictors import PredictByClosestDescriptor
from models.geo import BuildingReadWithGroup, Building
from models.logs import HTTPMethod, Recognition
from services.geo import select_geo_object_by_id, selected_geo_object_exists
from services.logs import create_request, create_recognition, last_recognition
from services.release import release_exists

IP = "0.0.0.0"
PORT = 8080

QDRANT_CLIENT = GetQdrantClient()
DEFAULT_RELEASE_NAME = "beautiful_morse"


class RecognizeData(BaseModel):
    descriptor: List[float]
    coordinates: Optional[Coordinates] = None
    direction: float = None
    release_name: str = None


class RequestLogRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            with GetSQLModelSession() as session:
                before = time.time_ns()
                request.state.buildings_info_db = session
                try:
                    response = await original_route_handler(request)
                except HTTPException as http_exception:
                    response = JSONResponse(
                        status_code=http_exception.status_code,
                        content={"error": http_exception.detail}
                    )
                    logger.error(http_exception)
                except (Exception,) as exception:
                    response = JSONResponse(
                        status_code=500,
                        content={"error": exception.details()}
                    )
                    logger.error(exception)

                response_time = (time.time_ns() - before) / 1e6
                response.headers["X-Response-Time"] = str(response_time)

                create_request(session=session,
                               id=uuid.UUID(hex=request.headers.get("x-request-id")),
                               timestamp=int(before // 1e9),
                               ipv4=request.headers.get("host").replace("localhost", "127.0.0.1"),
                               request_headers=dict(request.headers.items()),
                               request_body=(await request.body()),
                               request_url=str(request.url),
                               http_method=getattr(HTTPMethod, request.method),
                               user_agent=request.headers.get("user-agent"),
                               response_headers=dict(response.headers.items()),
                               response_body=response.body,
                               status=response.status_code,
                               response_time=response_time)
                return response

        return custom_route_handler


app = FastAPI()
router = APIRouter(
    route_class=RequestLogRoute,
)
templates = Jinja2Templates(directory="templates")


@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    return "OK"


@router.get("/health_routed", status_code=status.HTTP_200_OK)
def health_routed():
    return "OK"


@router.post("/recognize", response_model=BuildingReadWithGroup)
def recognize(recognize_data: RecognizeData, request: Request):
    session = request.state.buildings_info_db

    release_name = recognize_data.release_name or DEFAULT_RELEASE_NAME

    if not release_exists(session, release_name):
        raise HTTPException(status_code=404, detail=f'Release "{release_name}" does not exists')

    predictor = PredictByClosestDescriptor(qdrant_client=QDRANT_CLIENT, release_name=release_name)

    coordinates = None if recognize_data.coordinates is None else recognize_data.coordinates.point(
        CoordinateSystem.ELLIPSOID)
    prediction = predictor.predict(session, recognize_data.descriptor)

    create_recognition(session=session,
                       request_id=uuid.UUID(hex=request.headers.get("x-request-id")),
                       timestamp=int(time.time()),
                       result_building_id=prediction.answer.building_id,
                       release_items=prediction.closest,
                       closest_size=len(prediction.closest),
                       release_name=predictor.release_name,
                       descriptor=recognize_data.descriptor,
                       descriptor_size=4096,
                       coordinates=coordinates,
                       model="MixVPR",
                       predictor=PredictByClosestDescriptor.__name__,
                       debug_token=request.headers.get("x-debug-token"))

    if not selected_geo_object_exists(session, Building, prediction.answer.building_id):
        raise Exception("Recognized building was not found in BuildingInfo database")
    building: Building = select_geo_object_by_id(session, Building, prediction.answer.building_id)

    if building.group.image_url is None:
        building.group.image_url = prediction.answer.image_url
    return building


@router.get("/debug/{debug_token}", response_model=BuildingReadWithGroup)
def debug(debug_token: str, request: Request):
    recognition = last_recognition(session=request.state.buildings_info_db, debug_token=debug_token)
    if not recognition:
        raise HTTPException(status_code=404, detail="Debug token not found")
    return templates.TemplateResponse(
        request=request,
        name="debug.html",
        context={
            "recognition": recognition,
            "release_items": recognition.release_items,
            "moscow_timezone": datetime.timezone(offset=datetime.timedelta(hours=3), name="Moscow"),
            "date_format": '%Y-%m-%d, %H:%M:%S'
        },
    )


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=IP, port=PORT, proxy_headers=True)
