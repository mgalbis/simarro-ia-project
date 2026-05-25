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

SERVICE_NAME ?= jupyterhub

.DEFAULT_GOAL := help

.PHONY: help requeriments build start stop destroy

help:
	@echo "Targets disponibles:"
	@echo "  requeriments  Genera requirements.txt con pip-compile en Python Linux"
	@echo "  build         Construye la imagen de los servicios"
	@echo "  start         Levanta todos los contenedores de todos los servicios"
	@echo "  stop          Elimina todos los contenedores manteniendo los volúmenes"
	@echo "  destroy       Elimina todos los contenedores y volúmenes"

requeriments:
	docker run --rm -v "$(CURDIR)/docker/$(SERVICE_NAME):/work" -w /work $(JUPYTERHUB_IMAGE) sh -c "pip install --no-cache-dir pip-tools==$(PIP_TOOLS_VERSION) && pip-compile requirements.in"

build:
	docker compose build

start:
	docker compose up --wait

stop:
	docker compose down

destroy:
	docker compose down --volumes
