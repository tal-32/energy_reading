*manual build*  
podman build -t energy_reading/producer:latest -f services/producer/Dockerfile .
podman build -t energy_reading/consumer:latest -f services/consumer/Dockerfile .

## helm
used version 4.1.1: https://get.helm.sh/helm-v4.1.1-linux-amd64.tar.gz
this helm version is local so it is in .helm (see .gitignore)

*setup*  
.helm/helm repo add kedacore https://kedacore.github.io/charts
.helm/helm repo update
.helm/helm install keda kedacore/keda --namespace keda --create-namespace
 
*checks*  
.helm/helm lint charts/enery_reading
.helm/helm template energy-release charts/enery_reading
.helm/helm install energy-test charts/enery_reading --dry-run --debug
.helm/helm template energy-release charts/enery_reading > deployment.yaml

## deploy
#.helm/helm uninstall energy-reading  # cleanup
.helm/helm upgrade --install energy-reading ./charts/enery_reading
.helm/helm uninstall energy-reading

*kind images*
podman save localhost/energy_reading/producer:latest | podman exec -i kind-cluster-control-plane ctr -n k8s.io images import -
podman save localhost/energy_reading/consumer:latest | podman exec -i kind-cluster-control-plane ctr -n k8s.io images import -
podman exec -it kind-cluster-control-plane crictl images