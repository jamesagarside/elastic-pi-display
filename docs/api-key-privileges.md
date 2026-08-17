# API key privileges

The display is read-only. It searches two index patterns and calls one Kibana
API, so give it the least privilege that covers those.

| Data source | Call | Needs |
| --- | --- | --- |
| Alert severity counts and recent alerts | `POST <es>/.alerts-security.alerts-<space>/_search` | index `read` |
| Entity risk scores | `POST <es>/risk-score.risk-score-latest-<space>/_search` | index `read` (tile hides if the risk engine is off) |
| Attack Discovery | `GET <kibana>/api/attack_discovery/_find` | Kibana Security feature privileges, plus index `read` on the attack discovery alert indices on stacks that store discoveries as alerts |

Alerts are the only required source. A key with just the index privileges
runs the display fine; Attack Discovery stays hidden until the key also has
the Kibana feature privileges from the `applications` block below.

## Step 1: create the key in Dev Tools

This is the reliable path. Run the request below in **Kibana Dev Tools**
(change `default` in all three places if your alerts live in another space),
then copy the `encoded` value from the response into `elastic-display setup`:

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
            ".alerts-security.attack.discovery.alerts*",
            ".adhoc.alerts-security.attack.discovery.alerts*",
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
            "feature_securitySolutionAttackDiscovery.all",
            "feature_securitySolutionAssistant.read"
          ],
          "resources": ["space:default"]
        }
      ]
    }
  }
}
```

If this request itself is rejected, the user you are logged in as lacks
`manage_own_api_key` (or the privileges being granted; a key can never hold
more than its creator). Create the key as a more privileged user.

## Step 2: verify it from the Pi

```bash
sudo elastic-display test
```

This probes every source with the configured key and prints one line per
source, `OK` or `X` with the failure reason. `Security alerts` showing `OK`
is the minimum working state; `Attack Discovery` and `Entity risk scores`
showing `OK` mean the full display lights up. For anything marked `X`, find
the symptom below.

## Step 3: fix what the test reports

**Attack Discovery unavailable with a 403.** Read the full error first: on
recent stacks the 403 body names the exact privilege the API wants, for
example `this action is granted by the Kibana privileges
[securitySolution-attackDiscoveryAll]`. That one means the key needs
`feature_securitySolutionAttackDiscovery.all`: the Attack Discovery find
API is gated on the All level even though the display only reads, which is
why the request above grants `.all` for that feature and `.read` for the
rest.

A 403 naming missing `[read, view_index_metadata]` privileges for
`.alerts-security.attack.discovery.alerts` indices means the Kibana side is
fine but the key lacks the attack discovery alert indices in its `indices`
block; the request above includes them.

If the named privilege is something else, or there is no hint, the feature
IDs themselves probably do not match your stack version: the Security
feature has been `feature_siem` through `feature_siemV5` over time, and
older stacks do not have a separate `feature_securitySolutionAttackDiscovery`
ID at all. List the IDs your stack actually uses with

```
GET kbn:/api/security/privileges
```

in Dev Tools, find the entries whose names start with `siem`,
`securitySolutionAttackDiscovery`, and `securitySolutionAssistant`, and use
them as `feature_<name>.<level>`. On stacks without a separate Attack
Discovery feature, the `siem*` read privilege covers it.

To fix an existing key without touching the Pi, update it in place; the
encoded key value stays the same, so the display does not need
reconfiguring. Find the ID under **Stack Management > API keys**, then:

```
PUT /_security/api_key/<key-id>
{
  "role_descriptors": { ...the corrected block from step 1... }
}
```

The PUT replaces the whole `role_descriptors` object rather than merging
into it, so always send the complete block from step 1 with your change
applied. Sending only the part you are adding silently drops the rest.

After changing a key's privileges, restart the display backend so it
re-probes the sources and unhides the tiles:

```bash
sudo systemctl restart elastic-pi-display
```

(`elastic-display test` probes live and reflects the change immediately;
the running display only re-probes at startup.)

**Attack Discovery unavailable with a 404.** The stack predates the
Attack Discovery public API (8.x before 8.14, roughly). Not a key problem;
the tile hides itself and the rest of the display works.

**Entity risk scores unavailable.** Usually not a key problem either: the
`risk-score.risk-score-latest-<space>` index only exists once the risk
engine has been enabled (**Security > Manage > Entity Risk Score**) and it
needs a Platinum licence or better. The index is created by the engine's
first scoring run, so expect the 404 to persist for a while after
enabling; restart the backend once it exists. If the engine is on, the
index exists, and the test still fails, the key is missing `read` on that
index pattern.

**Security alerts failing.** Check the space: the key above grants access to the
`-default` index names, and a display configured for another space queries
`.alerts-security.alerts-<that-space>` instead. The space in the key's
`names`, in its `resources`, and in `elastic-display setup` must all match.

## Using the API keys UI instead of Dev Tools

The Stack Management form posts to a different (Kibana) endpoint with its
own request shape, so pasting the full request above is rejected with a
`role_descriptors.indices: expected a plain object` validation error. In
**Stack Management > API keys > Create API key > Control security
privileges**, paste only the inner object, everything from
`"elastic_pi_display_read": { ... }`, and set the name in the form field.

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
