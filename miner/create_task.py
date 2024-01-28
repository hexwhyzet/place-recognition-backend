from miner.main import download_pano

if __name__ == '__main__':
    # for i in range(0, 100):
    #     delta = -0.004 * i
    #     crawl.delay(
    #         Coordinates(55.738900170 + delta, 37.61989625 + delta, CoordinateSystem.ELLIPSOID),
    #         PanoSource.GOOGLE,
    #     )
    download_pano.delay(
        122,
        'test6142623',
        3,
        6,
    )
