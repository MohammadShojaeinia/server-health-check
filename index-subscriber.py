import asyncio
import sys
import asyncio_redis
import pymongo
import json

REDIS_HOST = "X.X.X.X"
REDIS_PORT = 6379


client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.database
healthmonitor = db.healthmonitor


@asyncio.coroutine
def health_monitor_subscriber():
    connection = yield from asyncio_redis.Connection.create(
        host=REDIS_HOST, port=REDIS_PORT
    )

    subscriber = yield from connection.start_subscribe()

    yield from subscriber.subscribe(["health-monitor"])

    while True:
        message = (yield from subscriber.next_published()).value
        message = json.loads(message)

        healthmonitor.insert_one(
            {
                "date": message["date"],
                "serverName": message["serverName"],
                "serverIP": message["serverIP"],
                "CPUUsagePercentage": message["CPUUsagePercentage"],
                "RAMUsagePercentage": message["RAMUsagePercentage"],
                "freeRAM": message["freeRAM"],
                "diskUsagePercentage": message["diskUsagePercentage"],
                "freeDisk": message["freeDisk"],
                "freeDiskPercentage": message["freeDiskPercentage"],
                "serverUptime": message["serverUptime"],
                "relatedServices": message["relatedServices"],
            }
        )

    connection.close()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(health_monitor_subscriber())
    except KeyboardInterrupt:
        sys.exit()