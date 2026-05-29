"""Exponer la API pública de configuración del paquete ``mlops.config``.

Este módulo centraliza los imports para los consumidores que necesitan acceder
al singleton global ``CASES_CONFIG``, al tipo ``CasesConfig`` o al helper de
acceso.
"""

from .cases_config_parser import CASES_CONFIG, CasesConfig, get_cases_config

# Nombres públicos reexportados para los consumidores del paquete.
__all__ = ["CasesConfig", "CASES_CONFIG", "get_cases_config"]
