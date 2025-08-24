# Design Document

## Overview

The Configuration Frontend is a Streamlit-based web application that provides a user-friendly interface for managing the traffic system's configuration and controlling microservices. The application will be integrated into the existing Poetry project structure and will interact directly with the `config.yaml` file and service processes.

The design follows a modular approach with separate components for configuration management, service control, and validation. The frontend will leverage Streamlit's native widgets and session state management to provide a responsive and intuitive user experience.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │◄──►│  Streamlit App   │◄──►│   config.yaml   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Service Manager  │
                       └──────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  Poetry Run Commands    │
                    │  (run_*.py scripts)     │
                    └─────────────────────────┘
```

### Technology Stack

- **Frontend Framework**: Streamlit 1.28+ for rapid web UI development
- **Configuration Management**: PyYAML for reading/writing config.yaml
- **Process Management**: subprocess module for controlling services
- **Validation**: Integration with existing Pydantic models from config_models.py
- **Backup System**: File system operations with timestamped backups

### Application Structure

```
src/traffic_system/frontend/
├── app.py                    # Main Streamlit application
├── components/
│   ├── config_editor.py     # Configuration editing components
│   ├── service_controller.py # Service management components
│   └── backup_manager.py    # Backup/restore functionality
├── utils/
│   ├── config_handler.py    # YAML file operations
│   ├── service_manager.py   # Process management utilities
│   └── validators.py        # Configuration validation
└── run_frontend.py          # Entry point script
```

## Components and Interfaces

### 1. Main Application (app.py)

**Purpose**: Central Streamlit application that orchestrates all components

**Key Features**:
- Multi-page layout with sidebar navigation
- Session state management for configuration changes
- Global error handling and user notifications
- Integration with existing config_loader for validation

**Interface**:
```python
def main() -> None:
    """Main Streamlit application entry point"""

def render_sidebar() -> str:
    """Render navigation sidebar, returns selected page"""

def handle_page_routing(page: str) -> None:
    """Route to appropriate page component"""
```

### 2. Configuration Editor (config_editor.py)

**Purpose**: Provides interactive widgets for editing all configuration sections

**Key Features**:
- Dynamic widget generation based on config structure
- Real-time validation feedback
- Collapsible sections for better organization
- Support for nested objects and arrays

**Interface**:
```python
def render_config_section(section_name: str, config_data: dict) -> dict:
    """Render configuration section with appropriate widgets"""

def render_nested_config(key: str, value: Any, path: str) -> Any:
    """Recursively render nested configuration objects"""

def validate_config_changes(config: dict) -> tuple[bool, list[str]]:
    """Validate configuration using Pydantic models"""
```

### 3. Service Controller (service_controller.py)

**Purpose**: Manages microservice lifecycle and status monitoring

**Key Features**:
- Real-time service status display
- Start/stop/restart operations
- Process monitoring and health checks
- Log output display for debugging

**Interface**:
```python
def render_service_panel() -> None:
    """Render service control interface"""

def get_service_status(service_name: str) -> ServiceStatus:
    """Get current status of a service"""

def start_service(service_name: str) -> bool:
    """Start a service using poetry run"""

def stop_service(service_name: str) -> bool:
    """Stop a running service"""
```

### 4. Backup Manager (backup_manager.py)

**Purpose**: Handles configuration backup and restore operations

**Key Features**:
- Automatic timestamped backups
- Backup listing and selection
- Safe restore with pre-restore backup
- Backup file management

**Interface**:
```python
def create_backup(config_path: str) -> str:
    """Create timestamped backup of configuration"""

def list_backups() -> list[BackupInfo]:
    """List available backup files"""

def restore_backup(backup_path: str, config_path: str) -> bool:
    """Restore configuration from backup"""
```

## Data Models

### Configuration Structure

The application will work directly with the existing config.yaml structure:

```yaml
# Base configuration
base_url: str
base_ip: str

# Service ports
services:
  simulation_port: int
  detection_port: int
  reporting_port: int

# Detection settings (nested object)
deteccion:
  detectar: bool
  modelo: str
  # ... (all existing detection settings)

# Decision/DQN settings (complex nested structure)
decision:
  decision: bool
  entrenamiento:
    entrenar: bool
    # ... (extensive training parameters)

# SUMO simulation settings
sumo:
  simular: bool
  gui: bool
  # ... (simulation parameters)

# Reporting settings
reporte:
  generar: bool
  # ... (reporting parameters)
```

### Service Status Model

```python
@dataclass
class ServiceStatus:
    name: str
    is_running: bool
    process_id: int | None
    start_time: datetime | None
    command: str
    port: int | None
```

### Backup Information Model

```python
@dataclass
class BackupInfo:
    filename: str
    timestamp: datetime
    file_path: str
    file_size: int
```

## Error Handling

### Configuration Validation

1. **Real-time Validation**: Use existing Pydantic models to validate changes as user types
2. **Save-time Validation**: Full configuration validation before writing to file
3. **Rollback Mechanism**: Automatic revert if validation fails after save
4. **User Feedback**: Clear error messages with specific field information

### Service Management Errors

1. **Process Errors**: Handle subprocess failures gracefully
2. **Port Conflicts**: Detect and report port availability issues
3. **Permission Errors**: Handle cases where services can't be started/stopped
4. **Timeout Handling**: Set reasonable timeouts for service operations

### File System Errors

1. **Permission Issues**: Handle read/write permission problems
2. **Disk Space**: Check available space before creating backups
3. **File Locking**: Handle concurrent access to config.yaml
4. **Backup Corruption**: Validate backup files before restore

## Testing Strategy

### Unit Testing

- **Configuration Handlers**: Test YAML read/write operations
- **Service Management**: Mock subprocess calls for testing
- **Validation Logic**: Test Pydantic integration
- **Backup Operations**: Test file system operations

### Integration Testing

- **End-to-End Configuration**: Test complete config save/load cycle
- **Service Integration**: Test actual service start/stop (in test environment)
- **Streamlit Components**: Test widget interactions and state management

### User Acceptance Testing

- **Configuration Workflows**: Test complete configuration editing scenarios
- **Service Management**: Test service control operations
- **Error Scenarios**: Test error handling and recovery
- **Cross-browser Testing**: Ensure compatibility across browsers

## User Interface Design

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Traffic System Config                    │
├─────────────┬───────────────────────────────────────────────┤
│  Sidebar    │                Main Content                   │
│             │                                               │
│ • Config    │  ┌─────────────────────────────────────────┐  │
│ • Services  │  │         Configuration Editor            │  │
│ • Backups   │  │                                         │  │
│ • About     │  │  ▼ Base Settings                        │  │
│             │  │    URL: [text input]                    │  │
│             │  │    IP:  [text input]                    │  │
│             │  │                                         │  │
│             │  │  ▼ Detection Settings                   │  │
│             │  │    Enable: [checkbox]                   │  │
│             │  │    Model:  [selectbox]                  │  │
│             │  │    ...                                  │  │
│             │  └─────────────────────────────────────────┘  │
└─────────────┴───────────────────────────────────────────────┘
```

### Widget Mapping Strategy

- **Boolean values**: `st.checkbox()`
- **String values**: `st.text_input()` or `st.text_area()` for long strings
- **Integer values**: `st.number_input()` with appropriate min/max
- **Float values**: `st.number_input()` with step parameter
- **Lists/Arrays**: `st.multiselect()` or dynamic add/remove interface
- **File paths**: `st.text_input()` with file browser button
- **Enums/Choices**: `st.selectbox()` or `st.radio()`

### Service Control Interface

```
┌─────────────────────────────────────────────────────────────┐
│                    Service Management                       │
├─────────────────────────────────────────────────────────────┤
│  Service Name        Status      Actions       Logs         │
│  ─────────────────────────────────────────────────────────  │
│  Simulation         ● Running    [Stop] [Restart] [View]    │
│  Decision Agent     ○ Stopped    [Start]         [View]     │
│  Detection          ● Running    [Stop] [Restart] [View]    │
│  Reporting          ○ Stopped    [Start]         [View]     │
└─────────────────────────────────────────────────────────────┘
```

## Security Considerations

### File System Access

- **Path Validation**: Ensure all file operations stay within project directory
- **Permission Checks**: Verify read/write permissions before operations
- **Backup Security**: Store backups in secure location with appropriate permissions

### Process Management

- **Command Injection**: Sanitize all inputs used in subprocess calls
- **Process Isolation**: Ensure services run with appropriate user permissions
- **Resource Limits**: Implement timeouts and resource limits for service operations

### Network Security

- **Local Access**: Default to localhost binding for security
- **Authentication**: Consider adding basic authentication for production use
- **HTTPS**: Support HTTPS for production deployments

## Performance Considerations

### Streamlit Optimization

- **Session State**: Efficient use of session state to minimize recomputation
- **Caching**: Use `@st.cache_data` for expensive operations
- **Lazy Loading**: Load configuration sections only when needed
- **Widget Keys**: Proper widget key management to prevent unnecessary reruns

### File Operations

- **Atomic Writes**: Use temporary files and atomic moves for config updates
- **File Watching**: Implement file change detection for external modifications
- **Backup Cleanup**: Automatic cleanup of old backup files

### Service Monitoring

- **Polling Optimization**: Efficient service status polling without overwhelming system
- **Background Tasks**: Use threading for non-blocking service operations
- **Resource Monitoring**: Monitor memory and CPU usage of managed services
