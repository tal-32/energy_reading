```sh
# make an entry
kubectl exec -it $(kubectl get pod -l app=producer -o name) -- \
  python3 -c "import urllib.request, json; \
  data = json.dumps({ \
    'site_id': 'e2etest123', \
    'device_id': 'e2etest456', \
    'power_reading': 3.14, \
    'timestamp': '2024-01-15T10:30:00Z' \
  }).encode('utf-8'); \
  req = urllib.request.Request('http://localhost:8000/readings', data=data, headers={'Content-Type': 'application/json'}); \
  resp = urllib.request.urlopen(req); \
  print(f'Status: {resp.status}, Body: {resp.read().decode()}')"

kubectl exec -it $(kubectl get pod -l app=redis -o name) -- \
  redis-cli LRANGE readings:site:e2etest123 0 -1

kubectl exec -it $(kubectl get pod -l app=consumer -o name) -- \
  python3 -c "import urllib.request; \
  resp = urllib.request.urlopen('http://localhost:8000/sites/e2etest123/readings'); \
  print(f'Status: {resp.status}'); \
  print(f'Response: {resp.read().decode()}')"
```


## check scaling
*watch scaling*  
```sh # host terminal
watch kubectl get pods,scaledobject
# or
# kubectl get hpa -w
```

*flood the system*  
```sh
kubectl exec -it $(kubectl get pod -l app=producer -o name) -- \
  python3 -c "import urllib.request, json;
for i in range(1000):
    data = json.dumps({'site_id': 'e2etest123', 'device_id': f'dev-{i}', 'power_reading': 3.14, 'timestamp': '2024-01-15T10:30:00Z'}).encode('utf-8');
    req = urllib.request.Request('http://localhost:8000/readings', data=data, headers={'Content-Type': 'application/json'});
    urllib.request.urlopen(req);
    if (i + 1) % 100 == 0: print(f'Sent {i + 1}/1000 messages...')"
```
