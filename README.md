# Wisecow

Bash web server that serves `fortune | cowsay` over HTTP, containerised and deployed on Kubernetes with TLS.

![wisecow](https://github.com/nyrahul/wisecow/assets/9133227/8d6bfde3-4a5a-480e-8d55-3fef60300d98)

## How it works

```
git push → GitHub Actions → Docker Hub → kubectl apply → K8s rollout
                                                          ├─ NGINX Ingress (TLS)
                                                          └─ KubeArmor (zero-trust)
```

## Repo layout

```
├── wisecow.sh                       # the app
├── Dockerfile
├── k8s/
│   ├── deployment.yaml              # 2 replicas, resource limits, tcp probes
│   ├── service.yaml                 # ClusterIP 80 → 4499
│   ├── ingress.yaml                 # NGINX ingress + TLS termination
│   ├── generate-tls-secret.sh       # self-signed cert → k8s secret
│   └── kubearmor-policy.yaml        # process/file/network lockdown
├── scripts/
│   ├── system_health_monitor.py     # cpu/mem/disk alerting
│   └── app_health_checker.py        # http uptime checker
└── .github/workflows/deploy.yml     # CI/CD pipeline
```

## Running locally

```bash
sudo apt install fortune-mod cowsay -y
./wisecow.sh
# http://localhost:4499
```

## Docker

```bash
docker build -t wisecow .
docker run -p 4499:4499 wisecow
```

## Kubernetes deployment

### 1. TLS secret (run once)

```bash
chmod +x k8s/generate-tls-secret.sh
./k8s/generate-tls-secret.sh
```

### 2. Deploy

```bash
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/ingress.yaml
```

### 3. Verify

```bash
kubectl get pods -l app=wisecow
kubectl get ingress wisecow-ingress
```

Add `wisecow.local` to `/etc/hosts` pointing at your ingress IP, then hit `https://wisecow.local`.

## CI/CD

Pipeline triggers on push to `main`. Two stages:

1. **build** — builds and pushes to Docker Hub with `latest` + commit SHA tags
2. **deploy** — patches the image tag in the deployment manifest, applies everything, waits for rollout

Secrets needed in the repo:

| Secret | What |
|---|---|
| `DOCKER_USERNAME` | Docker Hub user |
| `DOCKER_PASSWORD` | Docker Hub token |
| `KUBE_CONFIG` | base64 kubeconfig |

## Monitoring scripts

```bash
pip install psutil requests

python scripts/system_health_monitor.py   # alerts on CPU>80%, MEM>80%, DISK>85%
python scripts/app_health_checker.py       # probes HTTP endpoints, logs UP/DOWN
```

Both log to stdout and a local file. Kill with `Ctrl+C`.

## KubeArmor zero-trust policy

```bash
kubectl apply -f k8s/kubearmor-policy.yaml
```

What's enforced:

- **Processes** — only `bash`, `cowsay`, `fortune`, `nc`, `cat`, `sleep`, `mkfifo`, `rm`, `env` can execute
- **Files** — `/etc/`, `/root/`, `/var/log/` are blocked; DNS config files are read-only
- **Network** — TCP and UDP only; ICMP and raw sockets blocked
- **Default posture** — anything not in the whitelist is denied

### Triggering a violation (for screenshots)

```bash
kubectl exec -it $(kubectl get pod -l app=wisecow -o jsonpath='{.items[0].metadata.name}') -- bash

# these should be blocked:
apt-get update
echo x > /etc/test

# watch violations in another terminal:
karmor logs --json
```

## License

See [LICENSE](LICENSE).
