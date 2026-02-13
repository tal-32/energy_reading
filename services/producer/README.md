## routes

### /readings
Publishes to Redis Stream, returns `201` with `stream ID`
return `422` if getting missing params

### /health
Returns 200 if the service is healthy
currently it does nothing but it could check the following
- invalid `power_reading` value range
- less than `x` `power_reading` from `device_id` in the past `y` minutes
- no `ACK` from `redis service`
- too many invalid requests in the last `x` minutes
