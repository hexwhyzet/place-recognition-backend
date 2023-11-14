import json

import clickhouse_connect
from shapely import Point

from models.logs import HTTPMethod
from services.logs import create_request_log, create_recognition_log


def GetClickhouseClient():
    return clickhouse_connect.get_client(
        host='clickhouse',
        username='default',
        # password='clickhouse',
        database='logs'
    )


if __name__ == '__main__':
    with GetClickhouseClient() as client:
        # create_request_log(
        #     client,
        #     123,
        #     123,
        #     "1.1.1.1",
        #     {'header': '123'},
        #     json.dumps({'bodyt': True}),
        #     'http://domain.com/request/123',
        #     HTTPMethod.GET.value,
        #     'UserAgent bla bla bla',
        #     json.dumps({'response': 200}),
        #     200,
        #     124
        # )
        create_recognition_log(
            client,
            123,
            123,
            69,
            [69, 1, 2, 3],
            4,
            'clever_augustus',
            [0.1, 0.2, 0.3, 0.4],
            4,
            Point(1, 2),
            'MixVPR-4-1.0.0',
            'DefaultDistance',
            True
        )
        # row1 = [1000, 'String Value 1000', 5.233]
        # row2 = [2000, 'String Value 2000', -107.04]
        # data = [row1, row2]
        # client.insert('new_table', data, column_names=['key', 'value', 'metric'])
        # result = client.query('SELECT min(key), avg(metric) FROM new_table')
        # print(result.result_rows)
