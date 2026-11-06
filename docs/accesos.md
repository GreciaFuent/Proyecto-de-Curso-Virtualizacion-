# Laboratory Access Guide — Group 4

## Network Access

The laboratory uses Tailscale to provide remote access to the
192.168.1.0/24 network.

The Proxmox server advertises the subnet route through Tailscale.
Remote users must be authorized to access this route.

Service domains are listed in docs/hosts.txt and point to
192.168.1.160, the MetalLB / Traefik IP address.

## Services

| Service | Address | Instructor Account | Permissions |
|---|---|---|---|
| Web application | http://app.grupo4.lab | Not required | Application access |
| API | http://api.grupo4.lab/health | Not required | Read access |
| Grafana | http://grafana.grupo4.lab | profesor_lectura | Viewer |
| Prometheus | http://prometheus.grupo4.lab | Not required | Read access |
| Argo CD | https://argocd.grupo4.lab | profesor_lectura | Read-only |
| PostgreSQL | 192.168.1.160:5432 | profesor_lectura | SELECT |

## PostgreSQL

Database: tareasdb

The instructor account has CONNECT, USAGE, and SELECT permissions
on existing tables in the public schema.

## Security

Passwords are delivered through a private channel.
Credentials must not be committed to the Git repository.

Grafana, Argo CD, and PostgreSQL use separate passwords.
