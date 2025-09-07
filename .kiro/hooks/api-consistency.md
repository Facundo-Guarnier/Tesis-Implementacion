# API Consistency Hook

## Trigger
- **File Changes**: `src/traffic_system/api/*.py`, `src/traffic_system/api_client/*.py`, `src/traffic_system/core/api_models.py`
- **Event**: On file save

## Description
Ensures consistency between API endpoints, DTOs, client implementations, and documentation when API-related files are modified. Validates the microservices architecture integrity.

## Validation Steps

### 1. DTO Model Consistency
- **API Models**: Verify all DTOs in `api_models.py` are properly defined with Pydantic
- **Type Safety**: Check that all fields have proper type annotations
- **Response Models**: Ensure all API endpoints return proper DTO objects
- **Request Models**: Validate request DTOs for POST/PUT endpoints

### 2. Endpoint Implementation Validation
- **Flask Routes**: Verify all routes follow the pattern `@app.route('/endpoint', methods=['GET'])`
- **Return Format**: Check that responses use `return jsonify(response.model_dump()), status_code`
- **Error Handling**: Ensure proper try/catch with `ErrorResponse` DTOs
- **Timeout Handling**: Verify client requests use `timeout=5`

### 3. Client-Server Synchronization
- **API Clients**: Verify that `DecisionAPI` and `ReportAPI` clients match server endpoints
- **Method Signatures**: Check that client methods return proper DTO types
- **Base URL Usage**: Ensure clients use configuration-based URLs
- **Error Propagation**: Validate that client errors are properly handled

### 4. Documentation Alignment
- **Data Flow**: Verify that `.github/DATA_FLOW.md` reflects current architecture
- **Response Examples**: Ensure documentation examples match actual DTO structures

## Microservices Architecture Validation

### Simulation API (Port 5000)
- **Endpoints**: `/simulacion`, `/reporte`, `/avanzar`, `/semaforo`, `/espera`, `/sincronizacion`
- **DTOs**: `SimulationStatusResponse`, `ReportResponse`, `WaitTimesResponse`, etc.
- **Client**: `DecisionAPI` in `data_source_client.py`

### Detection API (Port 5000 - shared)
- **Endpoints**: `/cantidad`, `/cantidad/{zona}`, `/espera`
- **DTOs**: `VehicleQuantitiesResponse`, `VehicleQuantityResponse`
- **Integration**: Shared server with simulation API

### Reporting API (Port 5001)
- **Endpoints**: Report generation and analytics
- **Client**: `ReportAPI` in `reporting_client.py`

## Expected Actions

### When API server files are modified:
1. **Validate Flask route definitions**
2. **Check DTO usage in responses**
3. **Verify error handling patterns**
4. **Test endpoint accessibility**

### When API client files are modified:
1. **Validate method signatures match server endpoints**
2. **Check return type annotations**
3. **Verify timeout and error handling**
4. **Test client-server communication**

### When DTO models are modified:
1. **Validate Pydantic model syntax**
2. **Check field types and validation rules**
3. **Verify usage in both servers and clients**
4. **Update documentation if needed**

## Integration Testing Triggers
- Suggest running `test_sincronizacion_completo.py` for simulation API changes
- Recommend `test_reinicio_api.py` for endpoint modifications
- Trigger API documentation updates when DTOs change

## Error Reporting
- Use structured logging with emojis: ✅ ❌ ⚠️ 🧪
- Reference specific files and line numbers
- Suggest fixes based on established patterns

## Project Standards Integration
- Follow Flask patterns established in the project
- Use Pydantic DTOs for all API communication
- Maintain absolute imports from `src/`
- Apply timeout patterns for HTTP requests
- Use configuration-based URLs and ports
