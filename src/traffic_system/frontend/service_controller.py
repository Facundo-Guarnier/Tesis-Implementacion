"""
Controlador de servicios simplificado para gestión de procesos.

Maneja inicio, parada y estado de los servicios del sistema de tráfico.
"""

import subprocess
import time
from pathlib import Path
from typing import Any

import psutil

from src.traffic_system.frontend.utils import (
    log_error,
    log_info,
    log_success,
    log_warning,
)


class ServiceController:
    """Controlador simplificado para los servicios del sistema."""

    # Mapeo de servicios a archivos ejecutables
    SERVICES = {
        "simulation": "run_simulation_provider.py",
        "decision": "run_decision_agent.py",
        "detection": "run_detection_provider.py",
        "reporting": "run_reporting_service.py",
    }

    # Nombres amigables para mostrar en UI
    SERVICE_NAMES = {
        "simulation": "🚗 Simulación",
        "decision": "🧠 Decisión",
        "detection": "👁️ Detección",
        "reporting": "📊 Reportes",
    }

    def __init__(self) -> None:
        """Inicializar el controlador de servicios."""
        self._process_cache: dict[str, psutil.Process | None] = {}
        self._last_check_time: float = 0
        self._cache_duration = 30  # Cache por 30 segundos (optimizado para UI)

        # Crear directorio de logs para servicios
        self.logs_dir = Path("logs/services")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Procesos activos para captura de logs
        self._active_processes: dict[str, dict[str, Any]] = {}

    def get_service_status(self, service_name: str) -> bool:
        """
        Verificar si un servicio está ejecutándose.

        Args:
            service_name: Nombre del servicio (simulation, decision, etc.)

        Returns:
            True si el servicio está activo, False en caso contrario
        """
        if service_name not in self.SERVICES:
            log_error(f"Servicio desconocido: {service_name}")
            return False

        try:
            # Usar cache si es reciente
            current_time = time.time()
            if current_time - self._last_check_time < self._cache_duration:
                cached_process = self._process_cache.get(service_name)
                if cached_process is not None:
                    try:
                        return bool(cached_process.is_running())
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Proceso cached ya no existe, limpiar cache
                        self._process_cache[service_name] = None

            # Buscar proceso por nombre de archivo (optimizado)
            script_name = self.SERVICES[service_name]
            found_process = None

            # Filtrar solo procesos Python para eficiencia
            try:
                for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                    try:
                        # Saltar procesos que claramente no son Python
                        proc_name = proc.info.get("name", "").lower()
                        if "python" not in proc_name and "py" not in proc_name:
                            continue

                        cmdline = proc.info.get("cmdline", [])
                        if cmdline and any(script_name in arg for arg in cmdline):
                            # Verificar que sea un proceso Python válido
                            if any("python" in arg.lower() for arg in cmdline):
                                found_process = proc
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            except Exception as e:
                log_warning(f"Error iterando procesos para {service_name}: {e}")

            # Actualizar cache y resultado
            if found_process:
                self._process_cache[service_name] = found_process
                self._last_check_time = current_time
                return True
            else:
                self._process_cache[service_name] = None
                return False

        except Exception as e:
            log_error(f"Error verificando estado de {service_name}: {e}")
            return False

    def start_service(self, service_name: str) -> tuple[bool, str]:
        """
        Iniciar un servicio específico.

        Args:
            service_name: Nombre del servicio a iniciar

        Returns:
            Tupla (éxito, mensaje)
        """
        if service_name not in self.SERVICES:
            error_msg = f"Servicio desconocido: {service_name}"
            log_error(error_msg)
            return False, error_msg

        # Verificar si ya está ejecutándose
        if self.get_service_status(service_name):
            warning_msg = f"El servicio {service_name} ya está ejecutándose"
            log_warning(warning_msg)
            return False, warning_msg

        try:
            script_path = self.SERVICES[service_name]

            # Verificar que el archivo existe
            if not Path(script_path).exists():
                error_msg = f"Archivo no encontrado: {script_path}"
                log_error(error_msg)
                return False, error_msg

            # Crear archivos de log para este servicio
            log_file_path = self.logs_dir / f"{service_name}.log"

            # Ejecutar con poetry run
            cmd = ["poetry", "run", "python", script_path]

            log_info(f"Iniciando servicio {service_name}: {' '.join(cmd)}")
            log_info(f"Logs del servicio {service_name} en: {log_file_path}")

            # Abrir archivo de log para escribir con manejo seguro de recursos
            try:
                log_file = open(log_file_path, "w", encoding="utf-8")
            except Exception as e:
                error_msg = f"Error creando archivo de log para {service_name}: {e}"
                log_error(error_msg)
                return False, error_msg

            try:
                # Iniciar proceso en background con logs capturados
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,  # Redirigir stderr a stdout para capturar todo junto
                    text=True,
                )

                # Guardar referencia al proceso y archivo para limpieza posterior
                self._active_processes[service_name] = {
                    "process": process,
                    "log_file": log_file,
                }
            except Exception as e:
                # Si falla al crear el proceso, cerrar el archivo inmediatamente
                log_file.close()
                error_msg = f"Error iniciando proceso para {service_name}: {e}"
                log_error(error_msg)
                return False, error_msg

            # Esperar un momento para verificar que inició correctamente
            time.sleep(2)

            if process.poll() is None:
                # Proceso sigue ejecutándose
                success_msg = f"Servicio {service_name} iniciado correctamente"
                log_success(success_msg)

                # Limpiar cache para forzar actualización
                self._last_check_time = 0

                return True, success_msg
            else:
                # Proceso terminó inmediatamente, probablemente error
                stderr_output = (
                    process.stderr.read() if process.stderr else "Sin detalles"
                )
                error_msg = (
                    f"El servicio {service_name} falló al iniciar: {stderr_output}"
                )
                log_error(error_msg)
                return False, error_msg

        except FileNotFoundError:
            error_msg = "Poetry no encontrado. Asegúrate de que Poetry esté instalado y en el PATH"
            log_error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Error iniciando servicio {service_name}: {e}"
            log_error(error_msg)
            return False, error_msg

    def stop_service(self, service_name: str) -> tuple[bool, str]:
        """
        Detener un servicio específico.

        Args:
            service_name: Nombre del servicio a detener

        Returns:
            Tupla (éxito, mensaje)
        """
        if service_name not in self.SERVICES:
            error_msg = f"Servicio desconocido: {service_name}"
            log_error(error_msg)
            return False, error_msg

        try:
            # Buscar y terminar el proceso
            script_name = self.SERVICES[service_name]
            processes_terminated = 0

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = proc.info.get("cmdline", [])
                    if cmdline and any(script_name in arg for arg in cmdline):
                        if any("python" in arg.lower() for arg in cmdline):
                            log_info(
                                f"Terminando proceso {proc.pid} para servicio {service_name}"
                            )
                            proc.terminate()

                            # Esperar terminación graceful
                            try:
                                proc.wait(timeout=5)
                            except psutil.TimeoutExpired:
                                log_warning(
                                    f"Forzando terminación del proceso {proc.pid}"
                                )
                                proc.kill()

                            processes_terminated += 1

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Limpiar cache
            self._process_cache[service_name] = None
            self._last_check_time = 0

            # Cerrar archivo de log si existe
            if service_name in self._active_processes:
                try:
                    log_file = self._active_processes[service_name]["log_file"]
                    log_file.close()
                    log_info(f"Archivo de log cerrado para servicio {service_name}")
                except Exception as e:
                    log_warning(
                        f"Error cerrando archivo de log para {service_name}: {e}"
                    )
                finally:
                    del self._active_processes[service_name]

            if processes_terminated > 0:
                success_msg = f"Servicio {service_name} detenido correctamente ({processes_terminated} procesos)"
                log_success(success_msg)
                return True, success_msg
            else:
                success_msg = f"No se encontraron procesos para {service_name} - servicio ya detenido"
                log_info(success_msg)
                return True, success_msg

        except Exception as e:
            error_msg = f"Error deteniendo servicio {service_name}: {e}"
            log_error(error_msg)
            return False, error_msg

    def get_all_services_status(self) -> dict[str, bool]:
        """
        Obtener estado de todos los servicios.

        Returns:
            Diccionario con estado de cada servicio
        """
        status = {}

        for service_name in self.SERVICES:
            status[service_name] = self.get_service_status(service_name)

        return status

    def get_service_display_name(self, service_name: str) -> str:
        """
        Obtener nombre amigable para mostrar en UI.

        Args:
            service_name: Nombre interno del servicio

        Returns:
            Nombre amigable para mostrar
        """
        return self.SERVICE_NAMES.get(service_name, service_name.title())

    def get_service_name_for_logs(self, service_name: str) -> str:
        """
        Obtener nombre sin emoji para logs.

        Args:
            service_name: Nombre interno del servicio

        Returns:
            Nombre sin emoji para logs
        """
        # Mapeo directo sin emojis
        clean_names = {
            "simulation": "Simulación",
            "decision": "Decisión",
            "detection": "Detección",
            "reporting": "Reportes",
        }
        return clean_names.get(service_name, service_name.title())

    def get_running_services_count(self) -> tuple[int, int]:
        """
        Obtener conteo de servicios activos vs total.

        Returns:
            Tupla (servicios_activos, total_servicios)
        """
        status = self.get_all_services_status()
        running_count = sum(1 for is_running in status.values() if is_running)
        total_count = len(status)

        return running_count, total_count

    def start_service_with_retry(
        self, service_name: str, max_retries: int = 2
    ) -> tuple[bool, str]:
        """
        Iniciar servicio con reintentos en caso de fallo.

        Args:
            service_name: Nombre del servicio
            max_retries: Número máximo de reintentos

        Returns:
            Tupla (éxito, mensaje)
        """
        for attempt in range(max_retries + 1):
            success, message = self.start_service(service_name)

            if success:
                return True, message

            if attempt < max_retries:
                log_warning(
                    f"Reintentando inicio de {service_name} (intento {attempt + 2}/{max_retries + 1})"
                )
                time.sleep(1)
            else:
                log_error(
                    f"Falló inicio de {service_name} después de {max_retries + 1} intentos"
                )

        return (
            False,
            f"Servicio {service_name} falló después de {max_retries + 1} intentos",
        )

    def stop_service_graceful(
        self, service_name: str, timeout: int = 10
    ) -> tuple[bool, str]:
        """
        Detener servicio con terminación graceful y timeout.

        Args:
            service_name: Nombre del servicio
            timeout: Tiempo de espera en segundos

        Returns:
            Tupla (éxito, mensaje)
        """
        if service_name not in self.SERVICES:
            error_msg = f"Servicio desconocido: {service_name}"
            log_error(error_msg)
            return False, error_msg

        try:
            script_name = self.SERVICES[service_name]
            processes_found = []

            # Encontrar todos los procesos del servicio
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = proc.info.get("cmdline", [])
                    if cmdline and any(script_name in arg for arg in cmdline):
                        if any("python" in arg.lower() for arg in cmdline):
                            processes_found.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if not processes_found:
                success_msg = f"No se encontraron procesos para {service_name} - servicio ya detenido"
                log_info(success_msg)
                return True, success_msg

            # Terminar procesos gracefully
            for proc in processes_found:
                try:
                    log_info(f"Enviando SIGTERM a proceso {proc.pid}")
                    proc.terminate()
                except psutil.NoSuchProcess:
                    continue

            # Esperar terminación
            terminated_count = 0
            for proc in processes_found:
                try:
                    proc.wait(timeout=timeout)
                    terminated_count += 1
                    log_info(f"Proceso {proc.pid} terminado gracefully")
                except psutil.TimeoutExpired:
                    log_warning(
                        f"Proceso {proc.pid} no respondió, forzando terminación"
                    )
                    try:
                        proc.kill()
                        proc.wait(timeout=2)
                        terminated_count += 1
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        log_error(f"No se pudo terminar proceso {proc.pid}")
                except psutil.NoSuchProcess:
                    terminated_count += 1

            # Limpiar cache
            self._process_cache[service_name] = None
            self._last_check_time = 0

            # Cerrar archivo de log si existe
            if service_name in self._active_processes:
                try:
                    log_file = self._active_processes[service_name]["log_file"]
                    log_file.close()
                    log_info(f"Archivo de log cerrado para servicio {service_name}")
                except Exception as e:
                    log_warning(
                        f"Error cerrando archivo de log para {service_name}: {e}"
                    )
                finally:
                    del self._active_processes[service_name]

            if terminated_count == len(processes_found):
                success_msg = f"Servicio {service_name} detenido correctamente ({terminated_count} procesos)"
                log_success(success_msg)
                return True, success_msg
            else:
                warning_msg = f"Servicio {service_name} parcialmente detenido ({terminated_count}/{len(processes_found)} procesos)"
                log_warning(warning_msg)
                return False, warning_msg

        except Exception as e:
            error_msg = f"Error en terminación graceful de {service_name}: {e}"
            log_error(error_msg)
            return False, error_msg

    def get_service_info(self, service_name: str) -> dict[str, Any]:
        """
        Obtener información detallada de un servicio.

        Args:
            service_name: Nombre del servicio

        Returns:
            Diccionario con información del servicio
        """
        info = {
            "name": service_name,
            "display_name": self.get_service_display_name(service_name),
            "script_file": self.SERVICES.get(service_name, ""),
            "is_running": False,
            "pid": None,
            "memory_usage": None,
            "cpu_percent": None,
        }

        if service_name not in self.SERVICES:
            return info

        try:
            script_name = self.SERVICES[service_name]

            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "memory_info", "cpu_percent"]
            ):
                try:
                    cmdline = proc.info.get("cmdline", [])
                    if cmdline and any(script_name in arg for arg in cmdline):
                        if any("python" in arg.lower() for arg in cmdline):
                            info["is_running"] = True
                            info["pid"] = proc.info["pid"]

                            # Información de recursos (opcional)
                            try:
                                memory_info = proc.info.get("memory_info")
                                if memory_info:
                                    info["memory_usage"] = (
                                        memory_info.rss / 1024 / 1024
                                    )  # MB

                                info["cpu_percent"] = proc.info.get("cpu_percent", 0)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass

                            break

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            log_error(f"Error obteniendo información de {service_name}: {e}")

        return info

    def start_all_services(self) -> dict[str, tuple[bool, str]]:
        """
        Iniciar todos los servicios secuencialmente.

        Returns:
            Diccionario con resultados por servicio
        """
        results = {}

        log_info("Iniciando todos los servicios...")

        # Orden recomendado de inicio (simulación primero, luego agentes)
        service_order = ["simulation", "decision", "detection", "reporting"]

        for service_name in service_order:
            if service_name in self.SERVICES:
                log_info(f"Iniciando servicio: {service_name}")

                # Verificar si ya está ejecutándose
                if self.get_service_status(service_name):
                    results[service_name] = (
                        True,
                        f"Servicio {service_name} ya estaba ejecutándose",
                    )
                    log_info(f"Servicio {service_name} ya estaba activo")
                else:
                    # Intentar iniciar
                    success, message = self.start_service_with_retry(service_name)
                    results[service_name] = (success, message)

                    if success:
                        log_success(f"Servicio {service_name} iniciado exitosamente")
                        # Esperar un poco antes del siguiente servicio
                        time.sleep(1)
                    else:
                        log_error(f"Falló inicio de servicio {service_name}: {message}")

        # Resumen de resultados
        successful = sum(1 for success, _ in results.values() if success)
        total = len(results)

        log_info(
            f"Operación masiva completada: {successful}/{total} servicios iniciados"
        )

        return results

    def stop_all_services(self) -> dict[str, tuple[bool, str]]:
        """
        Detener todos los servicios activos.

        Returns:
            Diccionario con resultados por servicio
        """
        results = {}

        log_info("Deteniendo todos los servicios...")

        # Orden inverso para detener (agentes primero, simulación al final)
        service_order = ["reporting", "detection", "decision", "simulation"]

        for service_name in service_order:
            if service_name in self.SERVICES:
                log_info(f"Deteniendo servicio: {service_name}")

                # Verificar si está ejecutándose
                if not self.get_service_status(service_name):
                    results[service_name] = (
                        True,
                        f"Servicio {service_name} ya estaba detenido",
                    )
                    log_info(f"Servicio {service_name} ya estaba inactivo")
                else:
                    # Intentar detener
                    success, message = self.stop_service_graceful(service_name)
                    results[service_name] = (success, message)

                    if success:
                        log_success(f"Servicio {service_name} detenido exitosamente")
                        # Esperar un poco antes del siguiente servicio
                        time.sleep(0.5)
                    else:
                        log_error(
                            f"Falló detención de servicio {service_name}: {message}"
                        )

        # Resumen de resultados
        successful = sum(1 for success, _ in results.values() if success)
        total = len(results)

        log_info(
            f"Operación masiva completada: {successful}/{total} servicios detenidos"
        )

        return results

    def restart_all_services(self) -> dict[str, tuple[bool, str]]:
        """
        Reiniciar todos los servicios (detener y luego iniciar).

        Returns:
            Diccionario con resultados por servicio
        """
        log_info("Reiniciando todos los servicios...")

        # Primero detener todos
        stop_results = self.stop_all_services()

        # Esperar un momento para asegurar terminación completa
        time.sleep(2)

        # Luego iniciar todos
        start_results = self.start_all_services()

        # Combinar resultados
        combined_results = {}
        for service_name in self.SERVICES:
            stop_success, stop_msg = stop_results.get(
                service_name, (False, "No procesado")
            )
            start_success, start_msg = start_results.get(
                service_name, (False, "No procesado")
            )

            if stop_success and start_success:
                combined_results[service_name] = (True, "Reiniciado exitosamente")
            else:
                error_details = []
                if not stop_success:
                    error_details.append(f"Detención: {stop_msg}")
                if not start_success:
                    error_details.append(f"Inicio: {start_msg}")

                combined_results[service_name] = (False, " | ".join(error_details))

        # Resumen final
        successful = sum(1 for success, _ in combined_results.values() if success)
        total = len(combined_results)

        log_info(
            f"Reinicio masivo completado: {successful}/{total} servicios reiniciados"
        )

        return combined_results

    def get_services_summary(self) -> dict[str, Any]:
        """
        Obtener resumen completo del estado de todos los servicios.

        Returns:
            Diccionario con resumen de servicios
        """
        running_count, total_count = self.get_running_services_count()

        summary = {
            "total_services": total_count,
            "running_services": running_count,
            "stopped_services": total_count - running_count,
            "status_text": f"{running_count}/{total_count} servicios activos",
            "all_running": running_count == total_count,
            "all_stopped": running_count == 0,
            "services": {},
        }

        # Información detallada por servicio
        services_info: dict[str, dict[str, Any]] = {}
        for service_name in self.SERVICES:
            services_info[service_name] = self.get_service_info(service_name)

        summary["services"] = services_info

        return summary

    def get_service_logs(self, service_name: str, max_lines: int = 100) -> list[str]:
        """
        Obtener las últimas líneas de log de un servicio específico.

        Args:
            service_name: Nombre del servicio
            max_lines: Número máximo de líneas a retornar

        Returns:
            Lista de líneas de log (más recientes primero)
        """
        if service_name not in self.SERVICES:
            return [f"Servicio desconocido: {service_name}"]

        log_file_path = self.logs_dir / f"{service_name}.log"

        if not log_file_path.exists():
            return [f"No se encontró archivo de log para {service_name}"]

        try:
            # Intentar leer con diferentes encodings para manejar caracteres especiales
            encodings_to_try = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

            for encoding in encodings_to_try:
                try:
                    with open(log_file_path, encoding=encoding, errors="replace") as f:
                        lines = f.readlines()

                    # Si llegamos aquí, la lectura fue exitosa
                    # Retornar las últimas max_lines líneas
                    return [line.rstrip() for line in lines[-max_lines:]]

                except UnicodeDecodeError:
                    # Intentar con el siguiente encoding
                    continue
                except Exception as e:
                    # Si hay otro tipo de error, reportarlo y salir
                    log_error(
                        f"Error leyendo logs de {service_name} con encoding {encoding}: {e}"
                    )
                    break

            # Si todos los encodings fallaron, intentar leer como binario y convertir
            try:
                with open(log_file_path, "rb") as f:
                    content = f.read()

                # Decodificar usando utf-8 con reemplazo de caracteres problemáticos
                text_content = content.decode("utf-8", errors="replace")
                lines = text_content.splitlines()

                return lines[-max_lines:]

            except Exception as e:
                log_error(f"Error leyendo logs de {service_name} como binario: {e}")
                return [f"Error leyendo logs: {e}"]

        except Exception as e:
            log_error(f"Error leyendo logs de {service_name}: {e}")
            return [f"Error leyendo logs: {e}"]

    def get_service_log_path(self, service_name: str) -> str:
        """
        Obtener la ruta del archivo de log de un servicio.

        Args:
            service_name: Nombre del servicio

        Returns:
            Ruta del archivo de log
        """
        if service_name not in self.SERVICES:
            return ""

        return str(self.logs_dir / f"{service_name}.log")

    def clear_service_logs(self, service_name: str) -> bool:
        """
        Limpiar los logs de un servicio específico.

        Args:
            service_name: Nombre del servicio

        Returns:
            True si se limpiaron exitosamente, False en caso contrario
        """
        if service_name not in self.SERVICES:
            return False

        log_file_path = self.logs_dir / f"{service_name}.log"

        try:
            # Si el servicio está activo, no podemos limpiar el archivo abierto
            if service_name in self._active_processes:
                log_warning(
                    f"No se puede limpiar log de {service_name}: servicio activo"
                )
                return False

            # Crear archivo vacío
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("")

            log_info(f"Logs de {service_name} limpiados exitosamente")
            return True

        except Exception as e:
            log_error(f"Error limpiando logs de {service_name}: {e}")
            return False

    def get_all_services_logs(self, max_lines: int = 50) -> dict[str, list[str]]:
        """
        Obtener logs de todos los servicios.

        Args:
            max_lines: Número máximo de líneas por servicio

        Returns:
            Diccionario con logs por servicio
        """
        all_logs = {}

        for service_name in self.SERVICES:
            all_logs[service_name] = self.get_service_logs(service_name, max_lines)

        return all_logs

    def cleanup_resources(self) -> None:
        """
        Limpia todos los recursos abiertos (archivos de log y procesos).
        Debe ser llamado antes de cerrar la aplicación.
        """
        log_info("🧹 Iniciando limpieza de recursos...")

        services_to_clean = list(self._active_processes.keys())

        for service_name in services_to_clean:
            try:
                process_info = self._active_processes.get(service_name)
                if process_info:
                    # Cerrar archivo de log si está abierto
                    log_file = process_info.get("log_file")
                    if log_file and not log_file.closed:
                        log_file.close()
                        log_info(f"✅ Archivo de log cerrado para {service_name}")

                    # Terminar proceso si sigue activo
                    process = process_info.get("process")
                    if process and process.poll() is None:
                        process.terminate()
                        log_info(f"✅ Proceso terminado para {service_name}")

            except Exception as e:
                log_warning(f"⚠️ Error limpiando recursos de {service_name}: {e}")
            finally:
                # Remover de la lista de procesos activos
                if service_name in self._active_processes:
                    del self._active_processes[service_name]

        log_info("✅ Limpieza de recursos completada")

    def __del__(self) -> None:
        """Destructor que asegura la limpieza de recursos."""
        try:
            self.cleanup_resources()
        except Exception:
            # Silenciar errores en el destructor para evitar problemas en el shutdown
            pass
