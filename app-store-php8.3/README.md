# PHP 8.3 Mini-Storefront with OCI APM

This is a PHP 8.3 application consisting of a storefront (with login) and a payment service, both instrumented for OpenTelemetry tracing to OCI APM.

## Features
- User authentication with session-based login
- Product browsing, cart management, checkout
- Mock payment processing
- Chaos engineering toggles
- Structured JSON logging
- OCI APM tracing

## Setup for Local Development

1. Ensure Docker and Docker Compose are installed.

2. Clone or navigate to the `app-store-php8.3` directory.

3. Build and run the services:
   ```
   docker-compose up --build
   ```

4. Access the application:
   - Storefront: http://localhost:8080
   - Payment (API): http://localhost:8081

## Credentials
- Username: `admin`
- Password: `securePass123`

## APM Configuration
To enable OCI APM tracing, set the following environment variables in `docker-compose.yml` or your deployment:

For Storefront:
```
OTEL_SERVICE_NAME=storefront
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=dev,service.version=0.1.0
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=https://trace-ingestion.eu-frankfurt-1.oci.oraclecloud.com/20200101/opentelemetry/v1/traces
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <YOUR_APM_TOKEN>
```

For Payment:
```
OTEL_SERVICE_NAME=payment
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=dev,service.version=0.1.0
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=https://trace-ingestion.eu-frankfurt-1.oci.oraclecloud.com/20200101/opentelemetry/v1/traces
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <YOUR_APM_TOKEN>
```

## Testing
- Login with the provided credentials.
- Browse products, add to cart, checkout.
- Check logs in `storefront/logs/storefront.log` and `payment/logs/payment.log`.
- View traces in OCI APM console.

## Chaos Testing
Use headers like `X-Chaos-Latency: 500` to simulate delays.
