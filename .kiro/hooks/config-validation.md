# Configuration Validation Hook

## Trigger
- **File Changes**: `config.yaml`, `src/traffic_system/core/config_models.py`
- **Event**: On file save

## Description
Validates that configuration files are synchronized and valid when modified. Ensures `config_models.py` is updated before `config.yaml` and that all configuration is type-safe.

## Validation Steps

### 1. Check Pydantic Model Sync
- Verify that all fields in `config.yaml` have corresponding Pydantic models
- Ensure no missing required fields
- Validate type consistency between YAML and Python models

### 2. Configuration Loading Test
- Attempt to load configuration using `load_app_settings()`
- Catch and report any `ConfigValidationError`
- Verify all services can access their configuration sections

### 3. Critical Configuration Checks
- **DQN Training Parameters**: Validate learning rates, batch sizes, network architecture
- **API Endpoints**: Ensure ports and URLs are valid
- **File Paths**: Verify model paths, SUMO paths, and asset directories exist
- **Boolean Flags**: Check service activation flags are consistent

### 4. Multi-Platform Validation
- Verify TensorFlow configuration for Linux (GPU) vs Windows (CPU)
- Check SUMO path configuration for different platforms
- Validate Poetry dependency specifications

## Expected Actions

### When `config.yaml` is modified:
1. **Validate against existing Pydantic models**
2. **Check for new fields** that need model updates
3. **Test configuration loading** with error reporting
4. **Suggest model updates** if new fields detected

### When `config_models.py` is modified:
1. **Validate Pydantic model syntax**
2. **Check field types and defaults**
3. **Verify inheritance from BaseModel**
4. **Test model validation** with sample data

## Error Reporting
- Use emoji logging: ✅ ❌ ⚠️ 🧪
- Provide specific field names and error descriptions
- Suggest fixes based on common configuration patterns
- Reference `.github/instructions/config-files.instructions.md`

## Integration with Project Standards
- Follow Poetry dependency management
- Use absolute imports from `src/`
- Apply type hints and Pydantic validation
- Maintain Spanish error messages for user-facing errors
