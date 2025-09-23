"""
Helper utilities para clientes de API con manejo robusto de errores.

Este módulo implementa el principio DRY para requests HTTP con validación
y manejo de errores consistente a través de todo el proyecto.
"""

import logging
import time
from typing import Any, TypeVar

import requests
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class APIRequestHelper:
    """
    Helper class para realizar requests HTTP con manejo robusto de errores.

    Implementa timeout estándar, logging apropiado y manejo de excepciones
    de forma consistente para todos los clientes API del proyecto.
    """

    DEFAULT_TIMEOUT = 30

    @staticmethod
    def safe_request(
        base_url: str,
        endpoint: str,
        method: str = "GET",
        timeout: int = DEFAULT_TIMEOUT,
        infinite_retry: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """
        Realizar request HTTP con manejo robusto de errores.

        Args:
            base_url: URL base del servicio
            endpoint: Endpoint específico (ej: "/data")
            method: Método HTTP ("GET", "PUT", "POST", etc.)
            timeout: Timeout en segundos (default: 30)
            infinite_retry: Si debe reintentar indefinidamente en caso de error (default: False)
            **kwargs: Argumentos adicionales para requests (params, json, etc.)

        Returns:
            dict | None: JSON response si es exitoso, None si hay error
        """
        logger = logging.getLogger("APIRequestHelper.safe_request")
        full_url = base_url + endpoint

        while True:  # Bucle infinito cuando infinite_retry=True
            try:
                if method == "GET":
                    response = requests.get(full_url, timeout=timeout, **kwargs)
                elif method == "PUT":
                    response = requests.put(full_url, timeout=timeout, **kwargs)
                elif method == "POST":
                    response = requests.post(full_url, timeout=timeout, **kwargs)
                elif method == "DELETE":
                    response = requests.delete(full_url, timeout=timeout, **kwargs)
                else:
                    logger.error(f"Método HTTP no soportado: {method}")
                    return None

                if response.status_code == 200:
                    if "application/json" in response.headers.get("Content-Type", ""):
                        json_data: dict[str, Any] = response.json()
                        return json_data
                    else:
                        logger.warning(
                            f"Respuesta con Content-Type inválido en {endpoint}: {response.headers.get('Content-Type')}"
                        )
                        if not infinite_retry:
                            return None
                else:
                    logger.warning(
                        f"Respuesta no exitosa en {endpoint}: {response.status_code}"
                    )
                    if not infinite_retry:
                        return None

            except requests.Timeout:
                #! No loguear timeouts para evitar spam en logs
                if not infinite_retry:
                    return None

            except requests.ConnectionError:
                logger.error(f"Error de conexión al endpoint {endpoint}")
                if not infinite_retry:
                    return None

            except requests.RequestException as e:
                logger.error(f"Error de request al endpoint {endpoint}: {e}")
                if not infinite_retry:
                    return None

            # Si infinite_retry=True, continuar el bucle con una pausa
            if infinite_retry:
                time.sleep(2)
            else:
                # Si infinite_retry=False, salir del bucle
                break

        return None

    @staticmethod
    def safe_request_with_validation(
        base_url: str,
        endpoint: str,
        response_model: type[T],
        method: str = "GET",
        timeout: int = DEFAULT_TIMEOUT,
        infinite_retry: bool = False,
        **kwargs: Any,
    ) -> T | None:
        """
        Realizar request HTTP con validación automática de Pydantic.

        Args:
            base_url: URL base del servicio
            endpoint: Endpoint específico
            response_model: Modelo Pydantic para validar la respuesta
            method: Método HTTP
            timeout: Timeout en segundos
            infinite_retry: Si debe reintentar indefinidamente en caso de error
            **kwargs: Argumentos adicionales para requests

        Returns:
            T | None: Instancia validada del modelo o None si hay error
        """
        logger = logging.getLogger("APIRequestHelper.safe_request_with_validation")

        # Hacer el request
        response_data = APIRequestHelper.safe_request(
            base_url, endpoint, method, timeout, infinite_retry, **kwargs
        )

        if response_data is None:
            return None

        # Validar con Pydantic
        try:
            validated_response: T = response_model.model_validate(response_data)
            return validated_response
        except ValidationError as e:
            logger.error(f"Error validando respuesta de {endpoint}: {e}")
            return None
