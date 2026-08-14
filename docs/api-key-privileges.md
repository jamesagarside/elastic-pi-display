# API key privileges

The display is read-only: it needs to search two index patterns and call one
Kibana API. Give it the least privilege that covers those.

## What the key is used for

| Data source | Call | Needs |
|---|---|---|
| Alert severity counts | `POST <es>/.alerts-security.alerts-<space>/_search` | index `read` |
| Entity risk scores | `POST <es>/risk-score.risk-score-latest-<space>/_search` | index `read` (tile hides if the risk engine is off) |
| Attack Discovery | `GET <kibana>/api/attack_discovery/_find` | Kibana Security read |

## Simple path (recommended)

Create the key while logged in to Kibana as a user with a **read-only security
analyst** role — an API key snapshots the creating user's permissions:

1. In Kibana: **Stack Management → API keys → Create API key** (on serverless:
   **Project settings → Management → API keys**).
2. Name it (e.g. `security-display`), no expiry or role restriction.
3. Copy the **Base64/encoded** value — that goes into `elastic-display setup`.

If you create it as a full admin instead, it works but the key can do
everything the admin can. Fine for a home lab; not for a SOC wall.

## Hardened path: restricted role descriptors

Create the key with explicit `role_descriptors` so it can only read what the
display needs. Run in **Dev Tools** (adjust `default` if you use another
space):

```json
POST /_security/api_key
{
  "name": "security-display",
  "role_descriptors": {
    "security_display_read": {
      "indices": [
        {
          "names": [
            ".alerts-security.alerts-default",
            "risk-score.risk-score-latest-default"
          ],
          "privileges": ["read", "view_index_metadata"],
          "allow_restricted_indices": false
        }
      ],
      "applications": [
        {
          "application": "kibana-.kibana",
          "privileges": [
            "feature_siemV3.read",
            "feature_securitySolutionAttackDiscovery.read",
            "feature_securitySolutionAssistant.read"
          ],
          "resources": ["space:default"]
        }
      ]
    }
  }
}
```

Notes:

- The alerts alias is not a restricted index, so plain index privileges are
  enough for the severity counts.
- The `applications` block grants Kibana feature privileges to the key; the
  feature ID for the Security solution has changed across stack versions
  (`feature_siem` → `feature_siemV2` → `feature_siemV3`). If Attack Discovery
  shows as unavailable with a 403 in `elastic-display test`, check your
  version's feature ID with `GET <kibana>/api/security/privileges` and adjust —
  or fall back to the simple path above.
- On serverless projects, prefer creating the key in the project's API keys UI;
  unified Cloud API keys also work.

## Rotating the key

```bash
elastic-display setup        # re-enter the new key (other answers keep their defaults)
sudo systemctl restart elastic-pi-display
```

The key is stored only in `/etc/elastic-pi-display/config.toml`, mode
`0600`, owned by the `elastic-display` service user.
