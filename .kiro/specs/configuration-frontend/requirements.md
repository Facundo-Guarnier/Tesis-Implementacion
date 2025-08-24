# Requirements Document

## Introduction

This feature provides a web-based frontend interface for managing the traffic system configuration and controlling microservices. The system currently requires manual editing of the `config.yaml` file and manual execution of service scripts via command line. This frontend will provide a user-friendly interface to modify configuration settings across all system sections (detection, decision, SUMO, reporting) and manage service lifecycle (start/stop/restart) through a simple web interface.

The frontend will be built using Streamlit for rapid development and will integrate with the existing Poetry-based project structure, allowing users to manage the entire traffic system through a single interface without requiring technical knowledge of YAML syntax or command-line operations.

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to edit configuration settings through a web interface, so that I can modify system behavior without manually editing YAML files.

#### Acceptance Criteria

1. WHEN the user accesses the configuration frontend THEN the system SHALL display all current configuration sections from config.yaml
2. WHEN the user modifies any configuration value THEN the system SHALL validate the input according to the expected data type
3. WHEN the user saves configuration changes THEN the system SHALL update the config.yaml file with the new values
4. WHEN the user saves configuration changes THEN the system SHALL preserve the original file structure and comments
5. IF a configuration value is invalid THEN the system SHALL display an error message and prevent saving

### Requirement 2

**User Story:** As a system administrator, I want to organize configuration settings by logical sections, so that I can easily find and modify related settings.

#### Acceptance Criteria

1. WHEN the user opens the configuration interface THEN the system SHALL display settings organized in collapsible sections (Base, Services, Detection, Decision, SUMO, Reporting)
2. WHEN the user expands a configuration section THEN the system SHALL show all relevant settings with appropriate input controls (text fields, checkboxes, sliders, dropdowns)
3. WHEN the user views nested configuration objects THEN the system SHALL display them in sub-sections with clear hierarchy
4. WHEN the user views array/list configurations THEN the system SHALL provide controls to add, remove, and modify list items

### Requirement 3

**User Story:** As a system administrator, I want to control microservices from the web interface, so that I can start, stop, and restart services without using command line.

#### Acceptance Criteria

1. WHEN the user accesses the service control panel THEN the system SHALL display the status of all four microservices (simulation, decision, detection, reporting)
2. WHEN the user clicks "Start Service" for a stopped service THEN the system SHALL execute the corresponding run_*.py script using "poetry run"
3. WHEN the user clicks "Stop Service" for a running service THEN the system SHALL terminate the corresponding process gracefully
4. WHEN the user clicks "Restart Service" THEN the system SHALL stop the service if running and then start it again
5. WHEN a service operation is in progress THEN the system SHALL display loading indicators and disable controls to prevent multiple operations

### Requirement 4

**User Story:** As a system administrator, I want to see real-time service status, so that I can monitor which services are running and their health.

#### Acceptance Criteria

1. WHEN the user views the service control panel THEN the system SHALL display current status (Running/Stopped) for each service
2. WHEN a service status changes THEN the system SHALL update the display within 5 seconds
3. WHEN a service fails to start THEN the system SHALL display error information and logs
4. WHEN services are running THEN the system SHALL show process IDs and runtime duration
5. IF a service crashes THEN the system SHALL detect the status change and update the display

### Requirement 5

**User Story:** As a system administrator, I want to backup and restore configuration settings, so that I can safely experiment with different configurations.

#### Acceptance Criteria

1. WHEN the user clicks "Backup Configuration" THEN the system SHALL create a timestamped backup of the current config.yaml
2. WHEN the user views available backups THEN the system SHALL display a list of all backup files with timestamps
3. WHEN the user selects a backup to restore THEN the system SHALL replace the current config.yaml with the backup content
4. WHEN the user restores a backup THEN the system SHALL create an automatic backup of the current configuration before restoring
5. WHEN backup operations complete THEN the system SHALL display success/failure messages

### Requirement 6

**User Story:** As a system administrator, I want to validate configuration changes before applying them, so that I can prevent system errors from invalid configurations.

#### Acceptance Criteria

1. WHEN the user modifies configuration values THEN the system SHALL validate them against the Pydantic models in real-time
2. WHEN the user attempts to save invalid configuration THEN the system SHALL display specific validation errors
3. WHEN the user saves valid configuration THEN the system SHALL test-load the configuration using the existing config_loader
4. IF configuration loading fails THEN the system SHALL revert changes and display the error message
5. WHEN configuration is successfully validated THEN the system SHALL display a success confirmation

### Requirement 7

**User Story:** As a system administrator, I want to access the configuration frontend through a web browser, so that I can manage the system from any device on the network.

#### Acceptance Criteria

1. WHEN the frontend application starts THEN the system SHALL be accessible via web browser on the configured port
2. WHEN the user accesses the frontend from a remote device THEN the system SHALL function identically to local access
3. WHEN multiple users access the frontend simultaneously THEN the system SHALL handle concurrent access safely
4. WHEN the frontend application starts THEN the system SHALL display the access URL and port information
5. WHEN the user closes the browser THEN the system SHALL maintain service states and configuration changes
