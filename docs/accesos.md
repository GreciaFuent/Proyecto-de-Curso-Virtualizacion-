# Accesos al laboratorio — Grupo 4

## Requisitos de conexión

El laboratorio utiliza Tailscale para permitir acceso remoto a la red
192.168.1.0/24.

El servidor Proxmox anuncia la ruta de subred mediante Tailscale.
El acceso remoto requiere autorización para utilizar dicha ruta.

Los dominios del proyecto están documentados en docs/hosts.txt
y apuntan a la IP 192.168.1.160 de MetalLB / Traefik.

## Servicios disponibles

| Servicio | Dirección | Usuario del profesor | Permisos |
|---|---|---|---|
| Aplicación web | http://app.grupo4.lab | No requiere cuenta | Uso de la aplicación |
| API | http://api.grupo4.lab/health | No requiere cuenta | Consulta |
| Grafana | http://grafana.grupo4.lab | profesor_lectura | Viewer |
| Prometheus | http://prometheus.grupo4.lab | No requiere cuenta | Consulta |
| Argo CD | https://argocd.grupo4.lab | profesor_lectura | Readonly |
| PostgreSQL | 192.168.1.160:5432 | profesor_lectura | SELECT |

## PostgreSQL

Base de datos: tareasdb

Permisos del profesor: CONNECT, USAGE y SELECT sobre las tablas
existentes del esquema public.

## Seguridad

Las contraseñas se entregan por un canal privado.
No se almacenan contraseñas en el repositorio Git.

Las cuentas de Grafana, Argo CD y PostgreSQL utilizan
contraseñas independientes.
