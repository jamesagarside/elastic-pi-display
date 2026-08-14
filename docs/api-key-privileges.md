# API key privileges

The display is read-only. It searches two index patterns and calls one Kibana
API, so give it the least privilege that covers those.

## What the key is used for

| Data source | Call | Needs |
| --- | --- | --- |
| Alert severity counts | `POST <es>/.alerts-security.alerts-<space>/_search` | index `read` |
| Entity risk scores | `POST <es>/risk-score.risk-score-latest-<space>/_search` | index `read` (tile hides if the risk engine is off) |
| Attack Discovery | `GET <kibana>/api/attack_discovery/_find` | Kibana Security read |

## Recommended: restricted key via Dev Tools

Create the key with explicit role descriptors so it can only read what the
display needs. Run this in Kibana Dev Tools (change `default` in both places
if you use another space), then copy the `encoded` value from the response
into `elastic-display setup`:

```json
POST /_security/api_key
{
  "name": "elastic-pi-display",
  "role_descriptors": {
    "elastic_pi_display_read": {
      "indices": [
        {
          "names": [
            ".alerts-security.alerts-default",
            "risk-score.risk-score-latest-default"
          ],
          "privileges": ["read", "view_index_metadata"]
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

An index-only key also works, but the Attack Discovery tile will hide itself
because that API needs the Kibana feature privileges in the `applications`
block.

### Using the API keys UI instead

The Stack Management form posts to a different (Kibana) endpoint with its own
request shape, so pasting the full request above is rejected with a
`role_descriptors.indices: expected a plain object` validation error. In
**Stack Management > API keys > Control security privileges**, paste only the
inner object, everything from `"elastic_pi_display_read": { ... }`, and set
the name in the form field.

### Feature privilege IDs change between versions

The Security feature IDs have changed across stack versions (`feature_siem`,
then `feature_siemV2`, then `feature_siemV3`). If `elastic-display test`
reports Attack Discovery as unavailable with a 403, list your version's IDs
with `GET kbn:/api/security/privileges` in Dev Tools and adjust the
`applications` block to match.

## Simple alternative

Create the key while logged in to Kibana as a user with a read-only security
analyst role; an API key snapshots the creating user's permissions:

1. In Kibana: **Stack Management > API keys > Create API key** (on
   serverless: **Project settings > Management > API keys**).
2. Name it (for example `elastic-pi-display`), no expiry or restriction.
3. Copy the encoded value; that goes into `elastic-display setup`.

Creating the key as a full admin also works, but the key can then do
everything the admin can. Fine for a home lab, not for a SOC wall.

## Rotating the key

```bash
sudo elastic-display setup      # re-enter the new key
sudo systemctl restart elastic-pi-display
```

The key is stored only in `/etc/elastic-pi-display/config.toml`, mode `0600`,
owned by the `elastic-display` service user.
