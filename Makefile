NEEDS_ENV_TARGETS := init build start stop destroy

ifneq ($(filter $(NEEDS_ENV_TARGETS),$(MAKECMDGOALS)),)
ifeq (,$(wildcard .env))
$(error ERROR: el fichero obligatorio ".env" no existe")
endif

include .env
export

ifeq ($(strip $(JUPYTERHUB_IMAGE)),)
$(error ERROR: la variable obligatoria "JUPYTERHUB_IMAGE" no existe o está vacía en ".env")
endif

ifeq ($(strip $(PIP_TOOLS_VERSION)),)
$(error ERROR: la variable obligatoria "PIP_TOOLS_VERSION" no existe o está vacía en ".env")
endif
endif

SERVICE_NAME ?= jupyterhub
TLS_CERT_DIR ?= docker/nginx/certs
TLS_CERT_DAYS ?= 365
TLS_CERT_CN ?= localhost

.DEFAULT_GOAL := help

.PHONY: help init build start stop destroy qabot-up qabot-down qabot-logs ingauge-up ingauge-down ingauge-logs

help:
	@echo "Targets disponibles:"
	@echo "  init          Inicializa el proyecto generando requeriments.txt y certificados TLS"
	@echo "  build         Construye la imagen de los servicios MLOps"
	@echo "  start         Levanta todos los contenedores de todos los servicios MLOps"
	@echo "  stop          Elimina todos los contenedores manteniendo los volúmenes MLOps"
	@echo "  destroy       Elimina todos los contenedores y volúmenes MLOps"
	@echo "  qabot-up      Levanta QA Bot con Docker Compose"
	@echo "  qabot-down    Para los contenedores de Docker Compose de QA Bot"
	@echo "  qabot-logs    Muestra logs de QA Bot"
	@echo "  ingauge-up    Levanta In-Gauge and En-Gage con Docker Compose"
	@echo "  ingauge-down  Para los contenedores de Docker Compose de In-Gauge and En-Gage"
	@echo "  ingauge-logs  Muestra logs de In-Gauge and En-Gage"

init:
	docker run --rm -v "$(CURDIR)/docker/$(SERVICE_NAME):/work" -w /work $(JUPYTERHUB_IMAGE) sh -c "pip install --no-cache-dir pip-tools==$(PIP_TOOLS_VERSION) && pip-compile requirements.in"
	docker run --rm -v "$(CURDIR)/$(TLS_CERT_DIR):/certs" alpine/openssl req -x509 -nodes -newkey rsa:4096 -sha256 -days $(TLS_CERT_DAYS) -subj "/CN=$(TLS_CERT_CN)" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" -keyout /certs/tls.key -out /certs/tls.crt

build:
	docker compose build

start:
	docker compose up --wait

stop:
	docker compose down

destroy:
	docker compose down --volumes

qabot-up:
	docker compose -f apps/qabot/docker-compose.yml up --build -d

qabot-down:
	docker compose -f apps/qabot/docker-compose.yml down

qabot-logs:
	docker compose -f apps/qabot/docker-compose.yml logs -f

ingauge-up:
	docker compose -f apps/In-gauge-and-en-gage/docker-compose.yml up --build -d

ingauge-down:
	docker compose -f apps/In-gauge-and-en-gage/docker-compose.yml down

ingauge-logs:
	docker compose -f apps/In-gauge-and-en-gage/docker-compose.yml logs -f
