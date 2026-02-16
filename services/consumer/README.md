## routes

### /sites/{site_id}/readings
Returns all stored readings for the given site
- Stream: "energy_readings"
- Group name: "processing_group"
- Create the consumer group on startup if it doesn't exist
- Acknowledge messages after processing (XACK))

### /health
Returns 200 if the service is healthy
currently it does nothing but it could check the following

*/health/check concept*
- invalid `power_reading` value range
- less than `x` `power_reading` from `device_id` in the past `y` minutes
- no `ACK` from `redis service`
- too many invalid requests in the last `x` minutes
- too many requested in `x` minutes

## Storage
Store readings in Redis using a structure keyed by site_id (e.g., a Redis list or sorted set per site).
