import os
from time import sleep
from datetime import datetime
import redis
import json


r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)


INTERVAL = 300
SERVER_NAME = "shoja-server-publisher"
SERVER_IP = "X.X.X.X"
RELATED_SERVICES = ["nginx"]


def get_service_status(service_name):
    if service_name == "keycloak" or service_name == "mongos":
        if service_name == "keycloak":
            service_name = "java"

        processes = list(
            map(lambda x: x[:-1],
                os.popen("ps -ef | awk '{print $8}'").readlines())
        )
        result = list(set([x for x in processes if x == service_name]))

        return 0 if result.__len__() > 0 and result[0] == service_name else -1

    return os.system("systemctl is-active --quiet {}".format(service_name))


def check_health():
    current_date_time = datetime.now().__str__()
    RELATED_SERVICES_STATUS = []

    # CPU usage
    cpu_usage = str(
        round(
            float(
                os.popen(
                    """grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }' """
                ).readline()
            ),
            2,
        )
    )

    # Memory usage
    total_memory, used_memory, free_memory = map(
        int, os.popen("free -t -m").readlines()[-1].split()[1:]
    )
    used_memory_percentage = round((used_memory / total_memory) * 100, 2)

    # Disk usage
    total_disk, used_disk, free_disk, used_disk_percentage = map(
        float,
        list(
            map(lambda x: x[:-1], (os.popen("df -h").readlines()[3].split()[1:-1]))),
    )
    free_disk_percentage = round(100 - used_disk_percentage, 2)

    # Uptime
    server_uptime_response = os.popen("uptime").readlines()[0].split()
    server_uptime = "{} {}".format(
        server_uptime_response[2], server_uptime_response[3][:-1]
    )

    for service in RELATED_SERVICES:
        service_status = get_service_status(service)
        RELATED_SERVICES_STATUS.append(
            {
                "service_name": service,
                "service_status": ("up" if service_status == 0 else "down"),
            }
        )

    r.publish(
        "health-monitor",
        json.dumps(
            {
                "date": current_date_time,
                "serverName": SERVER_NAME,
                "serverIP": SERVER_IP,
                "CPUUsagePercentage": cpu_usage,
                "RAMUsagePercentage": used_memory_percentage,
                "freeRAM": free_memory,
                "diskUsagePercentage": used_disk_percentage,
                "freeDisk": free_disk,
                "freeDiskPercentage": free_disk_percentage,
                "serverUptime": server_uptime,
                "relatedServices": RELATED_SERVICES_STATUS,
            }
        ),
    )


while True:
    check_health()
    sleep(INTERVAL)
