# Retrieve OCI Policies

Read-only backup tool for selected OCI IAM policies and dynamic groups in an OCI tenancy.

## What It Reads

The script uses OCI config profile auth and calls only read/list/get APIs:

- `get_tenancy`
- `get_dynamic_group`
- `list_compartments`
- `list_policies`
- `list_dynamic_groups`

It does not create, update, or delete OCI resources.

## Configure Owners

Create a local `owners.env` from the committed example:

```bash
cp owners.env.example owners.env
```

Minimal config:

```bash
OCI_PROFILE=DEFAULT

# Enter comma-separated email addresses when backing up more than one person.
OWNER_EMAILS=owner.one@example.com,owner.two@example.com
```

For each email, the script checks these tag values:

- `oracleidentitycloudservice/<email>`
- `<email>`

Tag keys checked:

- `Oracle_Tags.CreatedBy`
- `CCA_Basic_Tag.email`

The script discovers active compartments automatically. No compartment OCIDs are required in the config.

## Run

```bash
cd tenancy-mgmt/retrieve-policies
python3 -m pip install -r requirements.txt
cp owners.env.example owners.env
python3 retrieve_policies.py
```

By default, the script reads `owners.env` from this directory.

Use `--config` only when you want to use a different config file:

```bash
python3 retrieve_policies.py --config owners-prod.env
python3 retrieve_policies.py --config owners-test.env
```

## Output Structure

Each run creates a timestamped snapshot folder so repeated backups do not overwrite earlier backups:

```text
backups/20260528T093012Z/
  metadata.json
  README.md
  owner.one/
    policies-root.json
    policies-compartment.json
    dynamic-groups.json
    README.md
    report.html
  owner.two/
    policies-root.json
    policies-compartment.json
    dynamic-groups.json
    README.md
    report.html
```

`metadata.json` records provenance: tenancy, profile, generated timestamp, owner tag filters, read-only APIs used, per-owner counts, and warnings.

The top-level `README.md` is an index for the run. Each owner folder has its own `README.md` with policy names, policy OCIDs, creator tag value, and numbered statements for easy reading.

Each owner folder also has `report.html`, a self-contained readable report with cards, JSON links, policy statements, dynamic-group matching rules, and copy buttons. Open it in a browser when you want to review or copy policy text cleanly.

The JSON files are the machine-readable backup. The README and HTML files are the human-readable backup.
