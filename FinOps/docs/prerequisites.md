# Prerequisites

Before deploying the OCI FinOps solution, ensure you have the following:

## Required Access

### OCI Tenancy Permissions

Your user or group needs these permissions:

```
# Compartment management
allow group <your-group> to manage compartments in tenancy

# Object Storage
allow group <your-group> to manage buckets in compartment <compartment>
allow group <your-group> to manage objects in compartment <compartment>

# Functions
allow group <your-group> to manage functions-family in compartment <compartment>
allow group <your-group> to use virtual-network-family in compartment <compartment>

# Log Analytics
allow group <your-group> to manage loganalytics-family in compartment <compartment>

# Streaming
allow group <your-group> to manage stream-family in compartment <compartment>

# IAM (for Terraform to create dynamic groups and policies)
allow group <your-group> to manage dynamic-groups in tenancy
allow group <your-group> to manage policies in tenancy
```

### Usage Report Access

OCI usage reports are stored in a special Oracle-managed tenancy. No additional permissions are needed—the Terraform configuration creates the necessary cross-tenancy policies.

## Required Tools

### For Terraform Deployment

| Tool | Version | Installation |
|------|---------|--------------|
| Terraform | >= 1.0.0 | [terraform.io/downloads](https://developer.hashicorp.com/terraform/downloads) |
| OCI CLI | >= 3.0.0 | [docs.oracle.com/iaas/tools/oci-cli](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm) |
| OCI Provider | >= 5.0.0 | Installed automatically by Terraform |

### For Function Deployment

| Tool | Version | Installation |
|------|---------|--------------|
| Fn CLI | Latest | [fnproject.io/tutorials/install](https://fnproject.io/tutorials/install/) |
| Docker | >= 20.0 | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |

## OCI CLI Configuration

Ensure your OCI CLI is configured:

```bash
# Check configuration
oci setup config

# Verify connectivity
oci iam region list

# Check your tenancy OCID
oci iam tenancy get --tenancy-id <your-tenancy-ocid>
```

## Fn CLI Configuration

Set up Fn CLI context for your OCI region:

```bash
# Create context
fn create context <context-name> --provider oracle

# Configure context
fn use context <context-name>
fn update context oracle.compartment-id <compartment-ocid>
fn update context oracle.profile <oci-profile-name>
fn update context registry <region-key>.ocir.io/<tenancy-namespace>

# Verify
fn list apps
```

## Compartment Setup

Create or identify a compartment for FinOps resources:

```bash
# List existing compartments
oci iam compartment list --compartment-id <tenancy-ocid>

# Create new compartment (optional)
oci iam compartment create \
  --compartment-id <parent-compartment-ocid> \
  --name "finops" \
  --description "FinOps cost analysis resources"
```

## Log Analytics Namespace

Log Analytics must be enabled in your region:

```bash
# Check if enabled
oci log-analytics namespace list --compartment-id <tenancy-ocid>

# If empty, onboard via OCI Console:
# Observability & Management > Log Analytics > Get Started
```

## Network Requirements (For Functions)

OCI Functions require a subnet. Options:

1. **Use existing VCN**: Provide `subnet_id` in Terraform variables
2. **Create new VCN**: Terraform can create a minimal VCN (not included by default)

Minimum subnet requirements:
- Private subnet (recommended) or public subnet
- NAT Gateway or Internet Gateway for outbound access
- Security list allowing HTTPS outbound (port 443)

## Checklist

- [ ] OCI CLI installed and configured
- [ ] Terraform installed
- [ ] Fn CLI installed (for function deployment)
- [ ] Docker running
- [ ] Tenancy OCID identified
- [ ] Compartment OCID identified
- [ ] Subnet OCID identified (for Functions)
- [ ] Log Analytics enabled in region
- [ ] IAM permissions verified

## Next Steps

Once all prerequisites are met, proceed to:
- [Quick Start](../README.md#quick-start) for Terraform deployment
- [Manual Setup](manual-setup.md) for step-by-step deployment without Terraform
