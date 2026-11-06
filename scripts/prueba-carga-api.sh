
#!/bin/bash
set -euo pipefail

# HA-05: prueba de carga HTTP para demostrar el HPA de la API.
# Uso: bash scripts/prueba-carga-api.sh [duracion_segundos] [concurrencia]

DURACION="${1:-90}"
CONCURRENCIA="${2:-6}"

if ! [[ "$DURACION" =~ ^[0-9]+$ && "$CONCURRENCIA" =~ ^[0-9]+$ ]] ||
   (( DURACION < 1 || CONCURRENCIA < 1 || CONCURRENCIA > 12 )); then
  echo "Uso: $0 [duracion_segundos] [concurrencia_1_a_12]"
  exit 1
fi

IP=$(kubectl get svc mi-api -n default -o jsonpath='{.spec.clusterIP}')
URL="http://${IP}:8000/metrics"

echo "Verificando API: $URL"
curl -fsS --max-time 5 -o /dev/null "$URL"

echo "Iniciando prueba HA-05"
echo "Duracion: ${DURACION}s"
echo "Concurrencia: $CONCURRENCIA"

FIN=$(( $(date +%s) + DURACION ))

for ((i=1; i<=CONCURRENCIA; i++)); do
  (
    EXITOS=0
    ERRORES=0

    while (( $(date +%s) < FIN )); do
      if curl -fsS --max-time 3 -o /dev/null "$URL"; then
        ((EXITOS+=1))
      else
        ((ERRORES+=1))
      fi
      sleep 0.1
    done

    echo "Cliente $i: $EXITOS exitosas, $ERRORES errores"
  ) &
done

wait
echo "Prueba finalizada"
