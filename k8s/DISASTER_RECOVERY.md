# Disaster recovery: rebuilding SmartHunt on a fresh OpenShift sandbox

Written 2026-08-12 because the current Red Hat Developer Sandbox account has ~3 days left before
it expires. When that happens the whole `a-badr-dev` project — every Deployment, Secret, ConfigMap,
PVC (with its data), Route, etc. — is gone. A new sandbox account starts with a completely empty
cluster/project. This doc is the ordered list of steps to get SmartHunt running again on that empty
project **without writing any new code** — everything here is either already in this repo, or backed
up locally on this machine (`/home/badr/openshift-backup-2026-08-12/`, **not** in git — it contains
real credentials and real user data).

Do not delete `/home/badr/openshift-backup-2026-08-12/` until the new sandbox is fully verified
working end-to-end.

## What's already safe (in this git repo, needs no action now)

- All application code (`backend/`, `frontend/`) — just needs a fresh `oc start-build`.
- `k8s/base/*.yaml` — ImageStreams, BuildConfigs, Deployments, Services, Routes, the two PVC specs
  (`backend-resume-pvc.yaml`, `backend-browser-profiles-pvc.yaml`), `backend-configmap.yaml` /
  `frontend-configmap.yaml` (both now verified to match the live cluster exactly, incl. the
  previously-missing `POSTGRES_HOST` key — fixed 2026-08-12), `keepalive-cronjob.yaml`,
  `github-actions-serviceaccount.yaml`. `backend-secret.yaml` / the postgres secret are templates
  only (placeholder values) — see below for the real values.
- `helm/smarthunt/` and `gitops/` — not the primary deploy path used day-to-day (see main
  CLAUDE.md), but present if ever needed.

## What is NOT in git and only exists live right now — this is what actually gets lost

1. **The postgres database itself** — was provisioned via OpenShift's built-in
   `postgresql-persistent` template (`oc new-app`), not a manifest in this repo. No
   DeploymentConfig/Secret/PVC/Service for it exists in `k8s/base/` at all. See "Recreate postgres"
   below for the exact command to reproduce it.
2. **Real secret values** — `smarthunt-secret` (`DATABASE_URL`, `REDIS_URL`, `VALKEY_URL`,
   `SECRET_KEY`, `JWT_SECRET_KEY`) and the postgres template's own `postgresql` secret
   (`database-user`/`database-password`/`database-name`). `k8s/base/backend-secret.yaml` in git is
   a placeholder template by design (see its own header comment on why — a real secret leaked into
   git once already, 2026-08-07). Real values backed up (raw `oc get secret -o yaml`, base64-encoded
   as usual) at:
   - `/home/badr/openshift-backup-2026-08-12/secrets/smarthunt-secret-RAW.yaml`
   - `/home/badr/openshift-backup-2026-08-12/secrets/postgres-secret-RAW.yaml`
3. **The actual database contents** — every job, application, resume record, note, tag, favorite,
   notification, audit log, etc. Dumped via `pg_dump` (28 tables, real data, verified non-empty) to:
   - `/home/badr/openshift-backup-2026-08-12/db/smarthunt-postgres-dump-2026-08-12.sql(.gz)`
4. **Uploaded resume files** (the actual PDF/DOCX bytes — the DB only has extracted text +
   metadata, not the file itself) — copied from the `smarthunt-resume-storage` PVC to:
   - `/home/badr/openshift-backup-2026-08-12/resume-files/resumes/` (original CV +
     `tailored/*.docx` — AI-tailored per-job resume versions)
5. **Browser session state** (LinkedIn login cookies, WhatsApp Web persistent Chromium profile) —
   copied from the `smarthunt-browser-profiles` PVC to:
   - `/home/badr/openshift-backup-2026-08-12/browser-profiles/browser-profiles/linkedin.json`
   - `/home/badr/openshift-backup-2026-08-12/browser-profiles/browser-profiles/whatsapp-persistent-profile/`
   Restoring these means not having to re-solve LinkedIn's device-approval checkpoint or re-scan a
   WhatsApp Web QR code — worth restoring, but not critical the way the DB/resume backups are; if the
   WhatsApp session is stale by the time you restore, it'll just prompt a fresh QR scan.
6. **The `keepalive-cli` service account** — the identity `~/smarthunt-keepalive.sh` and this whole
   session's `oc` CLI access use (`oc whoami` → `system:serviceaccount:a-badr-dev:keepalive-cli`).
   Has broad edit-level permissions on the project (create/patch/delete on secrets, deploymentconfigs,
   buildconfigs, routes, imagestreams, serviceaccounts — consistent with the standard `edit`
   ClusterRole). Its token lives at `~/.smarthunt-keepalive-token` and `~/.smarthunt-keepalive-server`
   on this machine — those files themselves will need regenerating against the new cluster (a token
   for a service account that no longer exists is useless), see below.
7. **Found while auditing, not previously known**: `smarthunt-secret`'s `REDIS_URL`/`VALKEY_URL`
   point at hostnames (`smarthunt-redis`, `valkey`) that **do not correspond to any real Service in
   this OpenShift project** — unlike local dev, there is no valkey/redis Deployment on OpenShift at
   all. Left as-is in the backup/template (matches the live cluster exactly, not a guess), but this
   means anything backend code path that depends on Redis/Valkey (rate limiting, caching,
   idempotency) has been silently running without it in production. Decide before/during rebuild
   whether to actually deploy a valkey pod on OpenShift (mirroring local's docker-compose one) or
   confirm the relevant code degrades gracefully without one — don't just carry the gap forward
   assuming it's fine because it "has been fine so far."

## Rebuild order

Run everything from the repo root unless noted. Replace `<PROJECT>` with whatever namespace the new
sandbox actually assigns you (`oc project` after logging in tells you) — Developer Sandbox project
names are tied to the account, so a new account may not reuse `a-badr-dev`. Every route hostname
below will also change to match — that's expected, not a bug; if OpenShift build stalls or the CLI
connection drops mid-upload, that's a known transient (see main CLAUDE.md's OpenShift build notes)
and usually keeps running server-side — check `oc get builds` before retrying.

### 1. Login and confirm the empty project

```bash
oc login --token=<new token from the sandbox web console> --server=<new API server URL>
oc project   # confirms the namespace name, e.g. <newname>-dev
oc get storageclass   # confirm `efs-sc` (RWX) still exists on this sandbox — it's a
                       # sandbox-provided class, not something added manually, so it should
                       # reappear, but verify before applying the two PVCs below. If it's missing,
                       # temporarily change accessModes to ReadWriteOnce on a gp3-class PVC instead —
                       # fine for initial single-replica bring-up, just don't do a rolling update
                       # (maxSurge: 1) with it until switched back to RWX (see main CLAUDE.md on why).
```

### 2. Recreate postgres (the piece with no manifest in this repo)

```bash
oc new-app postgresql-persistent \
  -p POSTGRESQL_USER=postgres \
  -p POSTGRESQL_DATABASE=smarthunt \
  -p DATABASE_SERVICE_NAME=smarthunt-postgres-internal \
  -p VOLUME_CAPACITY=1Gi \
  -p POSTGRESQL_VERSION=10-el8
# Let the template generate its own fresh POSTGRESQL_PASSWORD (more secure than reusing the old
# one) — read it back with:
oc get secret postgresql -o jsonpath='{.data.database-password}' | base64 -d; echo
oc rollout status dc/postgresql --timeout=180s
```

### 3. Restore the real database contents into the new (empty) postgres

```bash
oc rsync /home/badr/openshift-backup-2026-08-12/db/ $(oc get pods -l name=postgresql -o jsonpath='{.items[0].metadata.name}'):/tmp/restore/
POD=$(oc get pods -l name=postgresql -o jsonpath='{.items[0].metadata.name}')
oc exec "$POD" -- bash -c 'gunzip -c /tmp/restore/smarthunt-postgres-dump-2026-08-12.sql.gz | psql -U postgres -d smarthunt'
# Verify row counts landed for real, don't just trust a clean exit code:
oc exec "$POD" -- psql -U postgres -d smarthunt -c "select count(*) from jobs;"
```

### 4. ImageStreams, BuildConfigs, ConfigMaps

```bash
oc apply -f k8s/base/backend-imagestream.yaml -f k8s/base/frontend-imagestream.yaml
oc apply -f k8s/base/backend-buildconfig.yaml -f k8s/base/frontend-buildconfig.yaml
oc apply -f k8s/base/backend-configmap.yaml -f k8s/base/frontend-configmap.yaml
```

### 5. The real secret (decode from local backup, do NOT apply the git template as-is)

```bash
python3 - <<'EOF'
import base64, yaml
with open("/home/badr/openshift-backup-2026-08-12/secrets/smarthunt-secret-RAW.yaml") as f:
    doc = yaml.safe_load(f)
for k, v in doc["data"].items():
    print(k, "=", base64.b64decode(v).decode())
EOF
# Then, with the new postgres password from step 2 substituted into DATABASE_URL (the old one in
# the backup is stale — the new postgres has a freshly-generated password):
oc create secret generic smarthunt-secret \
  --from-literal=DATABASE_URL="postgresql+asyncpg://postgres:<NEW_PG_PASSWORD>@smarthunt-postgres-internal:5432/smarthunt" \
  --from-literal=REDIS_URL="redis://smarthunt-redis:6379/0" \
  --from-literal=VALKEY_URL="redis://valkey:6379/0" \
  --from-literal=SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  --from-literal=JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
# Generating fresh SECRET_KEY/JWT_SECRET_KEY rather than reusing the backed-up ones is deliberate —
# every existing session/JWT is invalid anyway once the whole project is gone, so there's no
# continuity benefit to reusing them, and a fresh keypair is better security hygiene.
```

**Confirmed live 2026-08-12: `backend-deployment.yaml`'s `envFrom` only wires `smarthunt-config`
(ConfigMap) + `smarthunt-secret` (Secret) into the container — nothing else.** The live
`smarthunt-secret` only ever had these 5 keys; there is no AI-provider/LinkedIn/Telegram credential
anywhere in the OpenShift deployment's env at all — those only exist in
`/home/badr/secrets/secret.env` on this machine, used for local dev. AI features are already known
to not work well on this cluster's hardware regardless (see main CLAUDE.md), so this is likely
intentional/accepted, not a gap to reflexively fix — but if LinkedIn auto-apply/monitoring should
work on the *new* OpenShift deployment too, add `LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD` (and whichever
other keys `smarthunt/core/config.py`'s `Settings` expects) as more `--from-literal=` flags on the
same `oc create secret generic smarthunt-secret` command above — a separate secret would need its
own `envFrom` entry added to `backend-deployment.yaml` first, since nothing else is wired in.
(Separately: the `linkedin.json` session file restored in step 8 below has a real, working LinkedIn
login session baked in *without* needing live credentials on OpenShift at all — it was carried over
from local, not established by the OpenShift pod logging in itself.)

### 6. PVCs, then trigger the first builds

```bash
oc apply -f k8s/base/backend-resume-pvc.yaml -f k8s/base/backend-browser-profiles-pvc.yaml
tar --exclude='.git' --exclude='frontend/node_modules' --exclude='frontend/.next' \
    --exclude='frontend/.turbo' --exclude='.venv' --exclude='backend/.venv' \
    --exclude='backend/__pycache__' -czf /tmp/smarthunt-build.tar.gz .
oc start-build smarthunt-backend --from-archive=/tmp/smarthunt-build.tar.gz --wait
oc start-build smarthunt-frontend --from-archive=/tmp/smarthunt-build.tar.gz --wait
# (--from-archive, not --from-dir=. — the latter uploads ~1.6GB incl. frontend/node_modules and
# routinely stalls; see main CLAUDE.md's OpenShift build notes for why.)
```

### 7. Deployments, Services, Routes, and the ImageChange triggers

```bash
oc apply -f k8s/base/backend-deployment.yaml -f k8s/base/frontend-deployment.yaml
oc apply -f k8s/base/backend-service.yaml -f k8s/base/frontend-service.yaml
oc apply -f k8s/base/backend-route.yaml -f k8s/base/frontend-route.yaml
oc set triggers deployment/smarthunt-backend --from-image=<PROJECT>/smarthunt-backend:latest -c backend
oc set triggers deployment/smarthunt-frontend --from-image=<PROJECT>/smarthunt-frontend:latest -c frontend
# Without this, a future `oc start-build` won't auto-restart the pod — see main CLAUDE.md's
# "successful build did NOT mean the fix was live" incident for why this bit specifically matters.
```

### 8. Restore uploaded resume files and browser session state

```bash
BACKEND_POD=$(oc get pods -l component=backend -o jsonpath='{.items[0].metadata.name}')
oc rsync /home/badr/openshift-backup-2026-08-12/resume-files/resumes/ "$BACKEND_POD:/data/resumes/"
oc rsync /home/badr/openshift-backup-2026-08-12/browser-profiles/browser-profiles/ "$BACKEND_POD:/data/browser-profiles/"
```

### 9. Recreate the `keepalive-cli` automation identity

```bash
oc create sa keepalive-cli
oc policy add-role-to-user edit -z keepalive-cli
oc create token keepalive-cli --duration=8760h > ~/.smarthunt-keepalive-token
oc whoami --show-server > ~/.smarthunt-keepalive-server
chmod 600 ~/.smarthunt-keepalive-token
oc apply -f k8s/base/keepalive-cronjob.yaml
# keepalive-cronjob.yaml's curl target URL is hardcoded to the *old* route hostname — edit it to
# match the new one (`oc get route smarthunt-backend -o jsonpath='{.spec.host}'`) before applying,
# or the keepalive ping will just 404/fail against a dead hostname forever without erroring loudly.
```

### 10. Verify for real, not just "pods are Running"

```bash
ROUTE=$(oc get route smarthunt-backend -o jsonpath='{.spec.host}')
curl -sS "https://$ROUTE/api/v1/health/ready"   # must be real DB connectivity, not just process alive
oc exec deploy/smarthunt-backend -- python -c \
  "from smarthunt.providers.registry import provider_registry; print([p.__class__.__name__ for p in provider_registry.providers()])"
FRONT=$(oc get route smarthunt-frontend -o jsonpath='{.spec.host}')
curl -sS -o /dev/null -w '%{http_code}\n' "https://$FRONT"
```

Then log in through the real UI and confirm the restored jobs/applications/resume actually show up —
a 200 on the route proves the frontend is serving, not that the DB restore actually worked.
