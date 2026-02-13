## routes

### /readings
Publishes to Redis Stream, returns `201` with `stream ID`
return `422` if getting missing params

### /health
Returns 200 if the service is healthy
currently it does nothing but it could check the following
- low space
- unable to reach `redis service` or other related error (example missing site)
- got unexpected struct
- too many invalid requests in the last `x` minutes
- too many requested in `x` minutes
