from sqlmodel import select

from db.postgres import GetSQLModelSession
from models import Building
from models.geo import BuildingRead
from models.language import TextContent

with GetSQLModelSession() as session:
    ans = session.exec(select(Building).where(Building.id == 7031)).first()
    print(ans)
    # print(ans.translations)
    print(ans.dict())
    print(ans.json())
