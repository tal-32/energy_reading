# manual test
Producer -> Redis Stream -> Consumer -> Redis List

decided not to add e2e automated tets for now
i would use something like `testcontainers` to compose these and run the following in each

*docker compose*  
I used podman    
```sh # from project root
podman-compose up -d --build --force-recreate
```

*validate error*  
```sh  # invalid for producer
curl -v -X POST http://localhost:8080/readings -H "Content-Type: application/json" -d '{"sensor_id": "panel_01", "reading": 42.5}'
< HTTP/1.1 422 Unprocessable Entity
< date: Sat, 14 Feb 2026 13:28:33 GMT
< server: uvicorn
< content-length: 482
< content-type: application/json
< 
* Connection #0 to host localhost left intact
{"detail":[{"type":"missing","loc":["body","site_id"],"msg":"Field required","input":{"sensor_id":"panel_01","reading":42.5}},{"type":"missing","loc":["body","device_id"],"msg":"Field required","input":{"sensor_id":"panel_01","reading":42.5}},{"type":"missing","loc":["body","power_reading"],"msg":"Field required","input":{"sensor_id":"panel_01","reading":42.5}},{"type":"missing","loc":["body","timestamp"],"msg":"Field required","input":{"sensor_id":"panel_01","reading":42.5}}]}
```

*make a valid input*  
```sh  # valid for producer
curl -v -X POST http://localhost:8080/readings -H "Content-Type: application/json" -d '{"site_id": "e2etest123", "device_id": "e2etest456", "power_reading": 3.14, "timestamp": "2024-01-15T10:30:00Z"}'
< HTTP/1.1 201 Created
< date: Sat, 14 Feb 2026 13:26:05 GMT
< server: uvicorn
< content-length: 51
< content-type: application/json
< 
* Connection #0 to host localhost left intact
{"status":"accepted","stream_id":"1771075566830-0"}
```

*validate input in redis via cli*
```sh
# validate in readis container
redis-cli KEYS *
1) "energy_readings"
redis-cli XRANGE energy_readings - +
1) 1) "1771075566830-0"
   2) 1) "site_id"
      2) "e2etest123"
      3) "device_id"
      4) "e2etest456"
      5) "power_reading"
      6) "3.14"
      7) "timestamp"
      8) "2024-01-15T10:30:00Z"
```

*validate consumer list*
```sh
# validate consumer
podman exec -it energy_reading_redis-service_1 redis-cli KEYS readings:site:*:*
1) "readings:site:e2etest123"
podman exec -it energy_reading_redis-service_1 redis-cli LRANGE readings:site:e2etest123 0 -1
1) "{\"site_id\": \"e2etest123\", \"device_id\": \"e2etest456\", \"power_reading\": \"3.14\", \"timestamp\": \"2024-01-15T10:30:00Z\"}"
```
