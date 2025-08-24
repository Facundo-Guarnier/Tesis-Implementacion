"""
Backup Management Components

Advanced backup and restore functionality with metadata display,
validation, and user-friendly management interface.
"""

import logging
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.traffic_system.frontend.utils.config_handler import ConfigHandler

logger = logging.getLogger(__name__)


class BackupManagerUI:
    """User interface for backup management."""

    def __init__(self, config_handler: ConfigHandler):
        """
        Initialize the backup manager UI.

        Args:
            config_handler: Configuration handler instance
        """
        self.config_handler = config_handler

    def render_backup_creation_section(self) -> None:
        """Render the backup creation interface."""
        st.subheader("📦 Crear Nuevo Backup")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            backup_name = st.text_input(
                "Nombre del backup (opcional)",
                placeholder="ej: antes_cambio_dqn",
                help="Si no especificas un nombre, se usará 'backup' por defecto",
            )

        with col2:
            backup_type = st.selectbox(
                "Tipo de backup",
                options=["manual", "auto", "pre_change"],
                index=0,
                help="Tipo de backup para organización",
            )

        with col3:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("📦 Crear Backup", use_container_width=True, type="primary"):
                self._create_backup_action(backup_name, backup_type)

        # Quick backup buttons
        st.markdown("**Acciones Rápidas:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⚡ Backup Rápido", use_container_width=True):
                self._create_backup_action(None, "manual")

        with col2:
            if st.button("🔄 Pre-Cambio", use_container_width=True):
                self._create_backup_action("pre_cambio", "pre_change")

        with col3:
            if st.button("🧹 Limpiar Antiguos", use_container_width=True):
                self._cleanup_old_backups_action()

    def render_backup_list_section(self) -> None:
        """Render the backup list and management interface."""
        st.subheader("📋 Backups Disponibles")

        try:
            backups = self.config_handler.list_backups()

            if not backups:
                st.info("📭 No hay backups disponibles. Crea tu primer backup arriba.")
                return

            # Backup statistics
            self._render_backup_statistics(backups)

            st.markdown("---")

            # Filter and sort options
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                search_term = st.text_input(
                    "🔍 Buscar backups",
                    placeholder="Buscar por nombre...",
                    key="backup_search",
                )

            with col2:
                sort_by = st.selectbox(
                    "Ordenar por",
                    options=["Fecha (nuevo)", "Fecha (antiguo)", "Nombre", "Tamaño"],
                    index=0,
                )

            with col3:
                show_count = st.selectbox(
                    "Mostrar", options=[10, 25, 50, "Todos"], index=0
                )

            # Filter and sort backups
            filtered_backups = self._filter_and_sort_backups(
                backups, search_term, sort_by, show_count
            )

            # Render backup list
            self._render_backup_items(filtered_backups)

        except Exception as e:
            st.error(f"❌ Error listando backups: {e}")
            logger.error(f"Error listing backups: {e}")

    def _render_backup_statistics(self, backups: list[dict]) -> None:
        """Render backup statistics."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Backups", len(backups))

        with col2:
            total_size = sum(backup["size"] for backup in backups)
            st.metric("Tamaño Total", f"{total_size / 1024:.1f} KB")

        with col3:
            if backups:
                latest = max(backups, key=lambda x: x["created"])
                days_ago = (datetime.now() - latest["created"]).days
                st.metric("Último Backup", f"Hace {days_ago} días")
            else:
                st.metric("Último Backup", "N/A")

        with col4:
            # Count backups from last 7 days
            recent_count = sum(
                1
                for backup in backups
                if (datetime.now() - backup["created"]).days <= 7
            )
            st.metric("Esta Semana", recent_count)

    def _filter_and_sort_backups(
        self, backups: list[dict], search_term: str, sort_by: str, show_count: int | str
    ) -> list[dict]:
        """Filter and sort backup list."""
        filtered = backups

        # Apply search filter
        if search_term:
            filtered = [
                backup
                for backup in filtered
                if search_term.lower() in backup["filename"].lower()
            ]

        # Apply sorting
        if sort_by == "Fecha (nuevo)":
            filtered.sort(key=lambda x: x["created"], reverse=True)
        elif sort_by == "Fecha (antiguo)":
            filtered.sort(key=lambda x: x["created"])
        elif sort_by == "Nombre":
            filtered.sort(key=lambda x: x["filename"])
        elif sort_by == "Tamaño":
            filtered.sort(key=lambda x: x["size"], reverse=True)

        # Apply count limit
        if show_count != "Todos":
            filtered = filtered[: int(show_count)]

        return filtered

    def _render_backup_items(self, backups: list[dict]) -> None:
        """Render individual backup items."""
        for i, backup in enumerate(backups):
            with st.container():
                # Backup item header
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    # Backup name with icon
                    backup_icon = self._get_backup_icon(backup["filename"])
                    st.write(f"{backup_icon} **{backup['filename']}**")

                with col2:
                    # Creation date
                    date_str = backup["created"].strftime("%Y-%m-%d %H:%M")
                    st.write(f"📅 {date_str}")

                with col3:
                    # File size
                    size_kb = backup["size"] / 1024
                    st.write(f"💾 {size_kb:.1f} KB")

                with col4:
                    # Actions dropdown
                    action = st.selectbox(
                        "Acción",
                        options=["---", "🔄 Restaurar", "👁️ Ver", "🗑️ Eliminar"],
                        key=f"backup_action_{i}",
                        label_visibility="collapsed",
                    )

                    if action == "🔄 Restaurar":
                        self._restore_backup_action(backup)
                    elif action == "👁️ Ver":
                        self._view_backup_action(backup)
                    elif action == "🗑️ Eliminar":
                        self._delete_backup_action(backup)

                # Backup details (expandable)
                with st.expander(f"Detalles de {backup['filename']}", expanded=False):
                    self._render_backup_details(backup)

                st.markdown("---")

    def _get_backup_icon(self, filename: str) -> str:
        """Get appropriate icon for backup based on filename."""
        if "manual" in filename.lower():
            return "👤"
        elif "auto" in filename.lower():
            return "🤖"
        elif "pre_change" in filename.lower() or "pre_" in filename.lower():
            return "⚠️"
        elif "restore" in filename.lower():
            return "🔄"
        else:
            return "📄"

    def _render_backup_details(self, backup: dict) -> None:
        """Render detailed backup information."""
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Información del Archivo:**")
            st.write(f"• **Ruta**: `{backup['path']}`")
            st.write(f"• **Tamaño**: {backup['size']} bytes")
            st.write(f"• **Creado**: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(
                f"• **Modificado**: {backup['modified'].strftime('%Y-%m-%d %H:%M:%S')}"
            )

        with col2:
            st.write("**Acciones Disponibles:**")

            col_a, col_b = st.columns(2)

            with col_a:
                if st.button(
                    "🔄 Restaurar", key=f"detail_restore_{backup['filename']}"
                ):
                    self._restore_backup_action(backup)

            with col_b:
                if st.button("🗑️ Eliminar", key=f"detail_delete_{backup['filename']}"):
                    self._delete_backup_action(backup)

    def _create_backup_action(self, custom_name: str | None, backup_type: str) -> None:
        """Create a backup with the specified parameters."""
        try:
            # Generate backup name
            if custom_name:
                backup_name = f"{backup_type}_{custom_name}"
            else:
                backup_name = backup_type

            with st.spinner("Creando backup..."):
                backup_path = self.config_handler.create_backup(backup_name)

            st.success(f"✅ Backup creado exitosamente: `{backup_path.name}`")
            st.balloons()  # Celebration effect

            # Auto-refresh the page to show new backup
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error creando backup: {e}")
            logger.error(f"Error creating backup: {e}")

    def _restore_backup_action(self, backup: dict) -> None:
        """Handle backup restoration with confirmation."""
        st.warning("⚠️ **Confirmación de Restauración**")
        st.write(
            f"¿Estás seguro de que quieres restaurar el backup `{backup['filename']}`?"
        )
        st.write("**Esta acción:**")
        st.write("• Creará un backup automático de la configuración actual")
        st.write("• Reemplazará la configuración actual con el backup seleccionado")
        st.write("• No se puede deshacer fácilmente")

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button(
                "✅ Confirmar",
                key=f"confirm_restore_{backup['filename']}",
                type="primary",
            ):
                self._perform_restore(backup)

        with col2:
            if st.button("❌ Cancelar", key=f"cancel_restore_{backup['filename']}"):
                st.info("Restauración cancelada")
                st.rerun()

    def _perform_restore(self, backup: dict) -> None:
        """Perform the actual backup restoration."""
        try:
            # Step 1: Validate backup before restore
            st.info("🔍 Validando backup...")
            if not self._validate_backup_before_restore(backup):
                st.error("❌ El backup no es válido y no se puede restaurar")
                return

            # Step 2: Create pre-restore backup
            st.info("📦 Creando backup de seguridad...")
            pre_restore_backup = self.config_handler.create_backup("pre_restore")
            st.success(f"✅ Backup de seguridad creado: {pre_restore_backup.name}")

            # Step 3: Perform restore
            with st.spinner("🔄 Restaurando configuración..."):
                success = self.config_handler.restore_backup(backup["path"])

            if success:
                st.success(f"✅ Backup `{backup['filename']}` restaurado exitosamente")

                # Step 4: Validate restored configuration
                st.info("🔍 Validando configuración restaurada...")
                if self._validate_restored_config():
                    st.success("✅ Configuración restaurada y validada correctamente")

                    # Update session state
                    if "current_config" in st.session_state:
                        st.session_state.current_config = (
                            self.config_handler.read_config()
                        )
                        st.session_state.config_modified = False

                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ La configuración restaurada no es válida")
                    st.warning("🔄 Restaurando backup de seguridad...")
                    self._rollback_restore(pre_restore_backup)
            else:
                st.error("❌ Error durante la restauración del backup")

        except Exception as e:
            st.error(f"❌ Error restaurando backup: {e}")
            logger.error(f"Error restoring backup: {e}")

            # Try to rollback if we have a pre-restore backup
            if "pre_restore_backup" in locals():
                st.warning("🔄 Intentando restaurar backup de seguridad...")
                self._rollback_restore(pre_restore_backup)

    def _view_backup_action(self, backup: dict) -> None:
        """Display backup content preview."""
        try:
            # Read backup content
            backup_path = Path(backup["path"])
            with open(backup_path, encoding="utf-8") as file:
                content = file.read()

            st.subheader(f"👁️ Vista Previa: {backup['filename']}")

            # Show content in code block
            st.code(content, language="yaml")

            # Content statistics
            lines = content.count("\n") + 1
            chars = len(content)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Líneas", lines)
            with col2:
                st.metric("Caracteres", chars)
            with col3:
                st.metric("Tamaño", f"{len(content.encode('utf-8'))} bytes")

        except Exception as e:
            st.error(f"❌ Error leyendo backup: {e}")
            logger.error(f"Error reading backup: {e}")

    def _delete_backup_action(self, backup: dict) -> None:
        """Handle backup deletion with confirmation."""
        st.warning("⚠️ **Confirmación de Eliminación**")
        st.write(
            f"¿Estás seguro de que quieres eliminar el backup `{backup['filename']}`?"
        )
        st.write("**Esta acción no se puede deshacer.**")

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button(
                "🗑️ Eliminar", key=f"confirm_delete_{backup['filename']}", type="primary"
            ):
                self._perform_delete(backup)

        with col2:
            if st.button("❌ Cancelar", key=f"cancel_delete_{backup['filename']}"):
                st.info("Eliminación cancelada")
                st.rerun()

    def _perform_delete(self, backup: dict) -> None:
        """Perform the actual backup deletion."""
        try:
            backup_path = Path(backup["path"])
            backup_path.unlink()  # Delete the file

            st.success(f"✅ Backup `{backup['filename']}` eliminado exitosamente")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error eliminando backup: {e}")
            logger.error(f"Error deleting backup: {e}")

    def _cleanup_old_backups_action(self) -> None:
        """Handle cleanup of old backups."""
        st.subheader("🧹 Limpieza de Backups Antiguos")

        col1, col2 = st.columns(2)

        with col1:
            keep_count = st.number_input(
                "Número de backups a mantener",
                min_value=1,
                max_value=100,
                value=10,
                help="Se mantendrán los N backups más recientes",
            )

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("🧹 Limpiar Antiguos", type="primary"):
                self._perform_cleanup(keep_count)

    def _perform_cleanup(self, keep_count: int) -> None:
        """Perform the actual cleanup of old backups."""
        try:
            with st.spinner("Limpiando backups antiguos..."):
                deleted_count = self.config_handler.cleanup_old_backups(keep_count)

            if deleted_count > 0:
                st.success(f"✅ {deleted_count} backups antiguos eliminados")
                st.rerun()
            else:
                st.info("ℹ️ No hay backups antiguos para eliminar")

        except Exception as e:
            st.error(f"❌ Error durante limpieza: {e}")
            logger.error(f"Error during cleanup: {e}")

    def _validate_backup_before_restore(self, backup: dict) -> bool:
        """Validate backup file before restoration."""
        try:
            import yaml

            backup_path = Path(backup["path"])

            # Check if file exists
            if not backup_path.exists():
                st.error(f"❌ Archivo de backup no encontrado: {backup_path}")
                return False

            # Check if file is readable
            with open(backup_path, encoding="utf-8") as file:
                content = file.read()

            # Check if content is valid YAML
            try:
                config_data = yaml.safe_load(content)
                if not config_data:
                    st.error("❌ El backup está vacío o no contiene datos válidos")
                    return False
            except yaml.YAMLError as e:
                st.error(f"❌ El backup no contiene YAML válido: {e}")
                return False

            # Basic structure validation
            required_sections = ["services", "deteccion", "decision", "sumo", "reporte"]
            missing_sections = [
                section for section in required_sections if section not in config_data
            ]

            if missing_sections:
                st.warning(
                    f"⚠️ Secciones faltantes en el backup: {', '.join(missing_sections)}"
                )
                # Don't fail, just warn - might be an older backup format

            return True

        except Exception as e:
            st.error(f"❌ Error validando backup: {e}")
            logger.error(f"Error validating backup: {e}")
            return False

    def _validate_restored_config(self) -> bool:
        """Validate the restored configuration."""
        try:
            # Try to load the restored configuration
            restored_config = self.config_handler.read_config()

            # Basic validation - check if config loaded successfully
            if not restored_config:
                return False

            # Check for required sections
            required_sections = ["services", "deteccion", "decision", "sumo", "reporte"]
            for section in required_sections:
                if section not in restored_config:
                    st.warning(f"⚠️ Sección faltante: {section}")

            return True

        except Exception as e:
            st.error(f"❌ Error validando configuración restaurada: {e}")
            logger.error(f"Error validating restored config: {e}")
            return False

    def _rollback_restore(self, pre_restore_backup: Path) -> None:
        """Rollback to pre-restore backup in case of failure."""
        try:
            st.warning("🔄 Ejecutando rollback...")
            success = self.config_handler.restore_backup(str(pre_restore_backup))

            if success:
                st.success("✅ Rollback completado exitosamente")
                # Update session state
                if "current_config" in st.session_state:
                    st.session_state.current_config = self.config_handler.read_config()
                    st.session_state.config_modified = False
            else:
                st.error(
                    "❌ Error durante rollback - configuración puede estar corrupta"
                )
                st.error("🚨 Revisa manualmente el archivo config.yaml")

        except Exception as e:
            st.error(f"❌ Error crítico durante rollback: {e}")
            st.error("🚨 Configuración puede estar corrupta - revisa manualmente")
            logger.error(f"Critical error during rollback: {e}")


def render_advanced_backup_manager(config_handler: ConfigHandler) -> None:
    """
    Render the advanced backup management interface.

    Args:
        config_handler: Configuration handler instance
    """
    backup_ui = BackupManagerUI(config_handler)

    # Backup creation section
    backup_ui.render_backup_creation_section()

    st.markdown("---")

    # Backup list section
    backup_ui.render_backup_list_section()
