import socket, time
hosts = [
    "ac-t8vmcy7-shard-00-00.rinicso.mongodb.net",
    "ac-t8vmcy7-shard-00-01.rinicso.mongodb.net",
    "ac-t8vmcy7-shard-00-02.rinicso.mongodb.net",
]
for host in hosts:
    start = time.time()
    try:
        s = socket.create_connection((host, 27017), timeout=8)
        s.close()
        print(f"TCP OK  {host} in {time.time()-start:.2f}s")
    except Exception as e:
        print(f"TCP FAIL {host} in {time.time()-start:.2f}s: {e}")
