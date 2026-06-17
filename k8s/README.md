# Task 3: CCE Application Deployment

These manifests deploy the required task 3 resources:

- Backend Flask `Deployment`, with 2 replicas, resource requests/limits, `ConfigMap` injection, `Secret` injection, and `/api/ping` probes.
- Redis `Deployment`, with 1 replica and memory limit no greater than 512Mi.
- Backend `LoadBalancer` `Service`, with the Huawei Cloud ELB annotation.
- Frontend Nginx `Deployment`, with Nginx config mounted from `ConfigMap`.
- Frontend internal `ClusterIP` `Service`.
- Redis internal `ClusterIP` `Service`.
- `ConfigMap` for Redis host/port.
- `ConfigMap` for Nginx reverse proxy config.
- `Secret` for the Redis password.
- `PersistentVolumeClaim` for Redis data persistence.

Before applying, replace `<YOUR_ORG>` in `deployment.yaml` with your SWR organization name:

```powershell
swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/backend:v1
```

If you want to use your own Redis password, generate a new base64 value:

```powershell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("your_password"))
```

Then replace `data.password` in `secret.yaml`.

If the backend image is in a private SWR repository, create an image pull secret before applying the deployment:

```powershell
kubectl create secret docker-registry swr-secret `
  --docker-server=swr.cn-north-4.myhuaweicloud.com `
  --docker-username="cn-north-4@<AK>" `
  --docker-password="<SK>"
```

If CCE reports that `kubernetes.io/elb.id` or `service.spec.loadBalancerIP` is not defined, create or choose an ELB in the Huawei Cloud console, copy its ID, then uncomment and fill `kubernetes.io/elb.id` in `service.yaml`.

Apply to CCE:

```powershell
kubectl apply -f k8s/
kubectl get pods
kubectl get svc
```

Check the Redis PVC:

```powershell
kubectl get pvc redis-data-pvc
```

Verify Redis data persistence:

```powershell
$redisPassword = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String((kubectl get secret redis-secret -o jsonpath="{.data.password}")))
$redisPod = kubectl get pod -l app=redis -o jsonpath="{.items[0].metadata.name}"
kubectl exec $redisPod -- redis-cli -a $redisPassword SET testkey hello
kubectl exec $redisPod -- redis-cli -a $redisPassword GET testkey
kubectl delete pod $redisPod
kubectl wait --for=condition=ready pod -l app=redis --timeout=180s
$newRedisPod = kubectl get pod -l app=redis -o jsonpath="{.items[0].metadata.name}"
kubectl exec $newRedisPod -- redis-cli -a $redisPassword GET testkey
```

Verify the Nginx ConfigMap volume mount:

```powershell
kubectl apply -f k8s/nginx-config.yaml
kubectl apply -f k8s/deployment.yaml
kubectl wait --for=condition=ready pod -l app=frontend --timeout=180s
$frontendPod = kubectl get pod -l app=frontend -o jsonpath="{.items[0].metadata.name}"
kubectl exec $frontendPod -- cat /etc/nginx/conf.d/default.conf
```

To demonstrate that the mounted file updates from the ConfigMap, change `proxy_pass http://backend-svc:80;` in `nginx-config.yaml` to another port such as `proxy_pass http://backend-svc:5001;`, apply it, wait for the kubelet ConfigMap refresh interval, then inspect the mounted file again:

```powershell
kubectl apply -f k8s/nginx-config.yaml
kubectl exec $frontendPod -- cat /etc/nginx/conf.d/default.conf
```

Do not mount the file with `subPath` for this task. ConfigMap volumes mounted with `subPath` do not receive live ConfigMap updates.

After `backend-svc` obtains an external ELB IP, verify:

```powershell
curl http://<ELB_IP>/api/ping
```
