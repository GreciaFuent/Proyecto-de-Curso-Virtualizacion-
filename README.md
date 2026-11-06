# KubeLab — Kubernetes Platform on Proxmox

**Group 4 · Virtualization Course**

## 1. Project Overview

KubeLab is a self-hosted container platform built on a physical server running Proxmox VE. Four Debian 13 virtual machines form a **k3s Kubernetes cluster** with one control-plane node and three workers. The platform hosts a task-management web application, a REST API, and a persistent PostgreSQL database. GitHub Actions, Argo CD, Doppler, MetalLB, Traefik, Prometheus, Grafana, Loki, and Promtail provide delivery automation, networking, secrets, metrics, and logs.

The Git repository contains the application configurations, deployment manifests, workflows, and evidence used to reproduce and evaluate the platform.

## 2. Architecture

```text
                         GitHub repository
                               |
                         GitHub Actions
                         (build / publish)
                               |
                             Argo CD  <--------- Doppler
                               |              (secrets operator)
Physical host                  |
  Proxmox VE 192.168.1.150     |
    |                          |
    +-- kube-control .151 -----+----- k3s control plane
    +-- kube-worker1 .152 -----|
    +-- kube-worker2 .153 -----|----- Kubernetes workloads
    +-- kube-worker3 .154 -----|
                               |
                      MetalLB (Layer 2)
                       192.168.1.160
                               |
                            Traefik
                 +-------------+--------------+
                 |             |              |
                Web           API         Observability
                 |             |          Prometheus / Grafana
                 +-------------+          Loki / Promtail
                               |
                          PostgreSQL
                         (persistent PVC)

Remote clients -- Tailscale subnet route 192.168.1.0/24
```

Traefik routes HTTP/HTTPS traffic by hostname and PostgreSQL traffic over TCP. The API and web run with multiple replicas on worker nodes. Argo CD reconciles declarative manifests from Git.

## 3. Proxmox and Virtual Machine Inventory

| Virtual machine | Role | Static IP | vCPU | Approx. RAM | Kubernetes-reported ephemeral storage |
|---|---|---|---:|---:|---:|
| `kube-control` | Control plane | `192.168.1.151` | 2 | 4 GiB | 19.6 GiB |
| `kube-worker1` | Worker | `192.168.1.152` | 1 | 2 GiB | 7.3 GiB |
| `kube-worker2` | Worker | `192.168.1.153` | 1 | 2 GiB | 7.3 GiB |
| `kube-worker3` | Worker | `192.168.1.154` | 1 | 2 GiB | 7.3 GiB |

**Important:** The storage column is Kubernetes-reported *ephemeral storage*, not an independently verified Proxmox virtual disk size. The control-plane VM has a 20 GiB virtual disk.

- **Hypervisor:** Proxmox VE on the assigned physical machine.
- **Proxmox management address:** `192.168.1.150/24` on bridge `vmbr0`.
- **Original LAN gateway:** `192.168.1.1`.
- **Guest OS:** Debian GNU/Linux 13 (trixie).
- **Kubernetes distribution:** k3s `v1.36.5+k3s1` at the recorded verification.
- **Service IP reserved for MetalLB:** `192.168.1.160/32`.
- **Application workload placement:** workers; the control plane is reserved for management.

k3s was chosen for its small footprint and straightforward server/agent architecture, appropriate for virtual machines with limited CPU and RAM.

### 3.1 Recreating the virtual machines in Proxmox

1. Install Proxmox VE directly on the physical server and create/configure the bridge `vmbr0` attached to the laboratory network.
2. Assign the host address `192.168.1.150/24` and the LAN gateway `192.168.1.1` to the management network.
3. Upload a Debian 13 installation ISO to Proxmox storage.
4. Create a VM called `kube-control`, allocate **2 vCPU, approximately 4 GiB RAM, and a 20 GiB disk**, and attach its network interface to `vmbr0`.
5. Install Debian, enable SSH, and assign `192.168.1.151/24` to the VM.
6. Create `kube-worker1`, `kube-worker2`, and `kube-worker3`, each with **1 vCPU and approximately 2 GiB RAM**. Provide sufficient local disk capacity for Kubernetes and container images.
7. Install Debian and assign `192.168.1.152/24`, `192.168.1.153/24`, and `192.168.1.154/24`, respectively.
8. Configure the appropriate gateway, DNS, hostnames, and SSH access for each guest.
9. Check connectivity between the four VMs and the Proxmox host.

The laboratory preserves these VM addresses even when the Proxmox host uses its Wi-Fi/hotspot connection as an alternate upstream route. Network forwarding/NAT on the hypervisor provides outbound connectivity to guests when the wired uplink is unavailable; this does not change the Kubernetes node addresses.

## 4. Kubernetes Installation and Verification

Install a k3s server on `kube-control`, then join the three agents to `https://192.168.1.151:6443`. The following is a *reconstruction outline*: use a current, explicitly selected k3s version matching the environment and provide the join token securely.

**On the control plane:**

```bash
curl -sfL https://get.k3s.io | sh -s - server --node-ip 192.168.1.151
sudo kubectl get nodes
```

Read the join token securely from `/var/lib/rancher/k3s/server/node-token`; do not put it in Git, screenshots, or documentation.

**On each worker:**

```bash
# Set K3S_URL to https://192.168.1.151:6443
# Set K3S_TOKEN to the privately obtained cluster join token.
curl -sfL https://get.k3s.io | K3S_URL="https://192.168.1.151:6443" K3S_TOKEN="<PRIVATE_JOIN_TOKEN>" sh -s - agent
```

Repeat for all three worker VMs, setting each machine's static address and hostname before joining. Configure workload placement so the application pods are scheduled on workers rather than the control plane.

**Validation commands:**

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

Expected nodes: `kube-control`, `kube-worker1`, `kube-worker2`, and `kube-worker3`, all `Ready`.

## 5. Repository Structure

This monorepo is organized around the actual Kubernetes components rather than the example directory layout in the course handout.

| Path | Purpose |
|---|---|
| `api/` | API Kubernetes deployment and service resources |
| `web/` | Web Kubernetes deployment and service resources |
| `postgres/` | PostgreSQL StatefulSet, service, initialization Job, and DopplerSecret |
| `plataforma/` | MetalLB resources, Traefik configuration, and ingress routes |
| `monitoring/` | Prometheus, Grafana, Loki, Promtail, and dashboard configuration |
| `argocd/` | Argo CD Application manifests |
| `.github/workflows/` | Automated GitHub Actions workflows |
| `scripts/` | Application load-testing scripts |
| `docs/` | Required host mappings, AI declaration, and evidence screenshots |

Inspect the repository for the application source/Dockerfiles and workflow build contexts; use the paths configured in the workflow files when building images.

## 6. Application and Database

The task-management application consists of:

- **Web:** a user interface for listing, creating, updating, and deleting tasks.
- **API:** CRUD endpoints, a `/health` endpoint, and Prometheus-compatible `/metrics`.
- **PostgreSQL:** the `tareasdb` database and `tareas` table, deployed as a StatefulSet with persistent storage.

The API health endpoint was checked successfully and returned a healthy status with the database connected. PostgreSQL accepts authenticated traffic through the Traefik TCP entry point on port `5432`.

### Database schema initialization

The `postgres/init-job.yaml` file defines an Argo CD `PostSync` hook. The Job loads `init.sql` from a ConfigMap and uses credentials synchronized into a Kubernetes Secret. The hook is deleted after success, so it may not appear in `kubectl get jobs` after completion.

The initial schema is:

```sql
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL
);
```

This creates the table only when absent, protecting existing rows from schema recreation by that statement.

### Application container images

The CI workflows build and publish the API and web images with commit-derived tags instead of deploying `latest`. Images and Kubernetes manifests are version-controlled through GitOps.

## 7. Networking: MetalLB and Traefik

MetalLB uses **Layer 2** mode with an `IPAddressPool` and `L2Advertisement` maintained in Git. Its reserved address is `192.168.1.160/32`. Traefik has a LoadBalancer service using `192.168.1.160`.

- Hostname-based routes are defined for the web, API, Grafana, Prometheus, and Argo CD.
- PostgreSQL uses an `IngressRouteTCP` over TCP port `5432`.
- Local domains use the suffix `grupo4.lab`.
- The exact host mappings are stored in [`docs/hosts.txt`](docs/hosts.txt).

### Service access table

| Service | URL / endpoint | Expected result |
|---|---|---|
| Web app | `http://app.grupo4.lab` | Task management UI |
| API health | `http://api.grupo4.lab/health` | HTTP 200 and healthy API/database status |
| Grafana | `http://grafana.grupo4.lab` | Grafana sign-in and dashboard |
| Prometheus | `http://prometheus.grupo4.lab` | Prometheus interface and metrics |
| Argo CD | `https://argocd.grupo4.lab` | Argo CD interface (laboratory certificate) |
| PostgreSQL | `192.168.1.160:5432` | Authenticated SQL connection to `tareasdb` |

Argo CD may present a browser warning because its HTTPS certificate is not publicly trusted.

## 8. Persistent Storage

The cluster uses the default **`local-path`** StorageClass. The following PVCs were observed in `Bound` state:

| Component | PVC | Size |
|---|---|---:|
| PostgreSQL | `postgres-data-postgres-0` | 1 GiB |
| Prometheus | `prometheus-datos` | 1 GiB |
| Loki | `loki-datos` | 1 GiB |
| Grafana | `grafana-datos` / `grafana-datos-nuevo` | 1 GiB each |

The additional API PVC `mi-api-datos` is also bound. PVC binding and the PostgreSQL StatefulSet were verified. Local-path storage is node-local; this is not a distributed, multi-node storage solution.

Useful checks:

```bash
kubectl get storageclass
kubectl get pvc -A
kubectl get statefulsets -A
```

## 9. Monitoring and Logging

**Prometheus** collects cluster/node and application metrics, including the API `/metrics` endpoint.

**Grafana** uses provisioned data sources for Prometheus and Loki. Its version-controlled dashboard is called **Virtualization** and contains nine panels:

1. Available Disk Space
2. CPU
3. Memory Usage (%)
4. Uptime
5. Prometheus CPU
6. Prometheus Memory
7. API Requests per Second
8. API and Web Logs
9. Active Replicas - API and Web

The source JSON is `monitoring/dashboards/virtualizacion.json`; its deployed ConfigMap is maintained in `monitoring/grafana-gitops/grafana-dashboard-json.yaml`.

**Loki** stores application and cluster logs. **Promtail** runs as a DaemonSet across all four nodes. **Node Exporter** also runs on all four nodes. The Grafana, Prometheus, and Loki pods were verified as `Running`.

```bash
kubectl get pods -n monitoring
kubectl get daemonsets -A
```

## 10. High Availability and Autoscaling

Both the API and web run with at least two replicas. Their manifests define resource requests/limits, liveness/readiness probes, PodDisruptionBudgets (PDBs), and HorizontalPodAutoscalers (HPAs).

| Component | CPU request | CPU limit | Memory request | Memory limit | Readiness / liveness path |
|---|---:|---:|---:|---:|---|
| API | 50m | 300m | 96 MiB | 256 MiB | `/health` on port 8000 |
| Web | 25m | 200m | 32 MiB | 96 MiB | `/` on port 80 |

| HPA | Minimum replicas | Maximum replicas | Target CPU |
|---|---:|---:|---:|
| `mi-api-hpa` | 2 | 6 | 60% |
| `mi-web-hpa` | 2 | 6 | 60% |

Each PDB specifies `minAvailable: 1`.

### Evidence of scaling and recovery

- The API was observed scaling from 2 to 6 replicas under load, then returning to 2.
- The web scaled under load and later returned to 2 replicas.
- Load tests completed with successful requests and no reported errors.
- After deleting a web pod, Kubernetes created a replacement, Argo CD remained `Synced / Healthy`, and the service returned HTTP 200.

Load tests are available in the `scripts/` directory, including `prueba-carga-api.sh` and `prueba-carga-web.sh`.

```bash
kubectl get deployment mi-api mi-web
kubectl get hpa
kubectl get pdb
```

## 11. CI/CD and GitOps

**GitHub Actions** builds and publishes images for the API and web. The workflows use Doppler for credentials and commit-based image tags. **Argo CD** watches the Git repository and reconciles the Kubernetes configuration automatically, including pruning and self-healing where configured.

Six Argo CD applications were observed in `Synced / Healthy` state:

- `grafana`
- `mi-api`
- `mi-web`
- `plataforma`
- `postgres`
- `prometheus`

The delivery flow is:

1. Application or configuration change is committed and merged to the main branch.
2. GitHub Actions runs the appropriate workflow and publishes a uniquely tagged image.
3. The manifest/image reference is updated in Git.
4. Argo CD detects the change and reconciles Kubernetes resources.
5. Application and health status are checked in the cluster.

```bash
kubectl get applications -n argocd
```

The repository uses Conventional Commit messages. Team collaboration is organized through branches and pull requests.

## 12. Secrets Management

Doppler is the external source for application secrets. Its Kubernetes Operator synchronizes credentials into Kubernetes Secrets through version-controlled `DopplerSecret` resources. PostgreSQL, API connectivity, Grafana, and CI credentials are managed without storing secret values in the repository.

The Doppler service token must be supplied through the cluster's protected secret configuration, not embedded in YAML or Git history. API/web workflows use Doppler integration for CI.

**Never commit passwords, access tokens, kubeconfig credentials, or the k3s join token.**

## 13. Instructor Access

The laboratory uses Tailscale to provide access to the `192.168.1.0/24` subnet. The Proxmox node advertises the lab subnet route. To access services by domain:

1. Install Tailscale and join the approved laboratory network.
2. Enable/use the advertised subnet route for `192.168.1.0/24`.
3. Copy the host mappings from [`docs/hosts.txt`](docs/hosts.txt) into the operating system's hosts configuration (`/etc/hosts` on Linux/macOS; the system hosts file on Windows).
4. Open the URLs in the service access table above.
5. Use the appropriate read-only credentials, provided through a private channel rather than GitHub.

Read-only instructor accounts:

| System | Username | Permission |
|---|---|---|
| PostgreSQL | `profesor_lectura` | `SELECT` on existing tables in `public` |
| Grafana | `profesor_lectura` | `Viewer`, non-admin |
| Argo CD | `profesor_lectura` | `role:readonly` |

PostgreSQL connection: host `192.168.1.160`, port `5432`, database `tareasdb`, username `profesor_lectura`. The PostgreSQL login and a `SELECT COUNT(*)` query were successfully tested through Traefik. Argo CD permissions were checked: the account can list applications and cannot synchronize them.

These accounts use independent passwords, which must be delivered privately.

## 14. Rebuilding the Environment from Scratch

This section describes the deployment order. Resource definitions in Git are the source of truth. Before deployment, provide required private credentials securely and verify that network routes and the reserved MetalLB address are available.

### Phase A — Hypervisor and cluster

1. Install Proxmox and configure `vmbr0`, the management address, and upstream network connectivity (Section 3).
2. Create and configure the four Debian virtual machines using the recorded names, resources, and static addresses.
3. Install k3s on `kube-control`, join the three worker nodes, and verify all nodes are `Ready` (Section 4).
4. Configure application workload placement on workers and verify the available default `local-path` StorageClass.

### Phase B — Clone the monorepo

```bash
git clone https://github.com/GreciaFuent/Proyecto-de-Curso-Virtualizacion-.git
cd Proyecto-de-Curso-Virtualizacion-
```

### Phase C — Install platform dependencies

1. Install Argo CD and verify its namespace and application controller.
2. Install MetalLB and its CRDs, then deploy the Git-versioned Layer 2 pool and advertisement.
3. Install/configure Traefik and make its LoadBalancer service use `192.168.1.160`.
4. Install the Doppler Kubernetes Operator, configure its service token privately, and enable the DopplerSecret resources.
5. Ensure that required controllers and Secrets exist before application workloads depend on them.
6. Apply the Argo CD Application manifests from `argocd/` using `kubectl apply -f` on the appropriate YAML files. Argo CD subsequently manages the component resources through GitOps.

### Phase D — Deploy and initialize the applications

1. Confirm that Argo CD has synchronized the `plataforma`, `postgres`, `mi-api`, `mi-web`, `grafana`, and `prometheus` applications.
2. Check that PostgreSQL's PVC is `Bound`, the StatefulSet is `Ready`, and the database initialization Job has completed through the `PostSync` hook.
3. Confirm both API and web deployments have at least two available replicas.
4. Check the HTTP ingress routes and the PostgreSQL TCP route.

### Phase E — Confirm observability and availability

```bash
kubectl get nodes -o wide
kubectl get applications -n argocd
kubectl get deployments mi-api mi-web
kubectl get statefulset postgres
kubectl get pvc -A
kubectl get hpa
kubectl get pdb
kubectl get pods -n monitoring
kubectl get daemonsets -A
```

Open the Grafana dashboard, inspect the Prometheus metrics and Loki logs, and run the provided load-testing scripts to verify autoscaling and recovery.

### Phase F — Verify domain access

Apply `docs/hosts.txt` on a client with network access and open all URLs from Section 7. Test PostgreSQL with an authenticated SQL client using the database and port listed in Section 13.

## 15. Evidence

Selected screenshots documenting platform functionality are stored in [`docs/evidencias/`](docs/evidencias/).

| Requirement demonstrated | Evidence file |
|---|---|
| Proxmox virtual machines | `01-proxmox-vms.png` |
| Kubernetes nodes | `02-kubernetes-nodos.png` |
| Successful GitHub Actions workflow | `06-github-actions-exitoso.png` |
| Argo CD applications | `07-argocd-aplicaciones.png` |
| Automatic deployment | `10-despliegue-automatico-kubernetes.png` |
| Doppler Kubernetes integration | `12-doppler-kubernetes.png` |
| Prometheus metrics | `16-prometheus-metricas-nodos.png` |
| Loki logs | `17-loki-logs-kubernetes.png` |
| Web CRUD backed by PostgreSQL | `18-web-crud-postgresql.png` |
| API HPA scaled to six replicas | `20-hpa-api-escalado-6.png` |
| API HPA returned to two replicas | `21-hpa-api-regreso-2.png` |
| Web HPA scaling | `26-hpa-web-escalado.png` |
| Web HPA returned to two replicas | `30-hpa-web-regreso-2.png` |
| Web before pod deletion | `32-web-antes-eliminar-pod.png` |
| Pod recreation | `33-web-recreacion-pod.png` |
| Web recovery and HTTP 200 | `34-web-recuperada-http-200.png` |

The version-controlled Grafana dashboard provides additional visual monitoring evidence.

## 16. Delivery and AI Declaration

The project is delivered through a single GitHub repository, with conventional commits, application manifests, workflows, documentation, and evidence files. The short declaration of AI assistance required by the course is in [`docs/ia.md`](docs/ia.md).

Each team member is responsible for understanding the relevant infrastructure, configurations, and deployment workflow for the live defense.
