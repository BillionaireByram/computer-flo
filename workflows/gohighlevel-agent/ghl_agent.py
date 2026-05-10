#!/usr/bin/env python3
"""Digital Flow GHL Agent framework.

Canonical home:
/Users/puregeniushq/projects/businesses/digitalflo/automation/ghl-agent

This is reusable Digital Flow infrastructure. Client-specific data lives in
client profiles and blueprints, not in the framework itself.
"""
from __future__ import annotations

import argparse, json, os, subprocess, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DIGITALFLOW_AUTOMATION_ROOT = HERE.parent
DEFAULT_PROFILE_DIR = Path.home() / '.hermes/browser-profiles/gohighlevel-isolated'
BASE_URL = os.environ.get('GHL_BASE_URL', 'https://services.leadconnectorhq.com').rstrip('/')
API_VERSION = os.environ.get('GHL_API_VERSION', '2021-07-28')
SECRET_KEYS = ('TOKEN', 'KEY', 'SECRET', 'PASSWORD', 'AUTHORIZATION')


def load_env_file(path: Path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_profile(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    if not path.exists():
        raise SystemExit(f'Client profile not found: {path}')
    data = json.loads(path.read_text(encoding='utf-8'))
    mapping = {
        'company_id': 'GHL_COMPANY_ID',
        'source_location_id': 'GHL_SOURCE_LOCATION_ID',
        'snapshot_location_id': 'GHL_SNAPSHOT_LOCATION_ID',
        'blueprint_path': 'GHL_BLUEPRINT_PATH',
        'build_cards_path': 'GHL_BUILD_CARDS_PATH',
        'credential_map_path': 'GHL_CREDENTIAL_MAP_PATH',
    }
    for src, env_key in mapping.items():
        if data.get(src):
            os.environ.setdefault(env_key, str(data[src]))
    return data


def default_location_id() -> str:
    return os.environ.get('GHL_SOURCE_LOCATION_ID') or 'REPLACE_WITH_LOCATION_ID'


def default_company_id() -> str:
    return os.environ.get('GHL_COMPANY_ID') or 'REPLACE_WITH_COMPANY_ID'


def default_blueprint_path() -> Path:
    return Path(os.environ.get('GHL_BLUEPRINT_PATH', str(HERE / 'examples/ghl-workflow-blueprints.example.json')))


def default_build_cards_path() -> Path:
    return Path(os.environ.get('GHL_BUILD_CARDS_PATH', str(HERE / 'AI_BUILDER_PROMPT_TEMPLATE.md')))


def inventory_dir() -> Path:
    return Path(os.environ.get('GHL_INVENTORY_DIR', str(HERE / 'runs/api-inventory')))


def profile_dir() -> Path:
    return Path(os.environ.get('GHL_AGENT_CHROME_PROFILE', str(DEFAULT_PROFILE_DIR)))


class GHLClient:
    def __init__(self, token: str | None = None, base_url: str = BASE_URL, version: str = API_VERSION):
        self.token = token or os.environ.get('GHL_API_TOKEN') or os.environ.get('GHL_AGENCY_KEY')
        self.base_url = base_url.rstrip('/')
        self.version = version

    def headers(self) -> dict[str, str]:
        if not self.token:
            raise SystemExit('Missing GHL_API_TOKEN or GHL_AGENCY_KEY. Fill env.local or another local .env; never paste secrets into docs/chat.')
        return {
            'Authorization': f'Bearer {self.token}',
            'Version': self.version,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def request(self, method: str, path: str, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> tuple[int, Any]:
        qs = ('?' + urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})) if params else ''
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path + qs, data=data, method=method.upper(), headers=self.headers())
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read().decode('utf-8', 'replace')
                return r.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            raw = e.read().decode('utf-8', 'replace')
            try:
                payload = json.loads(raw)
            except Exception:
                payload = raw
            return e.code, {'error': payload}


def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: ('[REDACTED]' if any(s in k.upper() for s in SECRET_KEYS) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


def workflow_url(location_id: str | None = None, workflow_id: str | None = None) -> str:
    lid = location_id or default_location_id()
    if workflow_id:
        return f'https://app.gohighlevel.com/v2/location/{lid}/automation/workflows/{workflow_id}'
    return f'https://app.gohighlevel.com/v2/location/{lid}/automation/workflows?listTab=all'


def chrome_js_check() -> int:
    script = """tell application \"Google Chrome\"
    if not (exists window 1) then make new window
    set resultText to execute active tab of front window javascript \"'AE_JS_OK_' + (1 + 1)\"
end tell
return resultText
"""
    p = subprocess.run(['osascript'], input=script, text=True, capture_output=True)
    print(p.stdout.strip() or p.stderr.strip())
    return p.returncode


def enable_chrome_js_pref() -> None:
    subprocess.run(['osascript', '-e', 'tell application "Google Chrome" to quit'], capture_output=True)
    time.sleep(2)
    root = Path.home() / 'Library/Application Support/Google/Chrome'
    changed = []
    for pref in sorted(root.glob('*/Preferences')):
        try:
            data = json.loads(pref.read_text(encoding='utf-8'))
        except Exception as e:
            print(f'SKIP {pref}: {e}')
            continue
        backup = pref.with_name('Preferences.hermes-backup-before-allow-js-apple-events')
        if not backup.exists():
            backup.write_text(pref.read_text(encoding='utf-8'), encoding='utf-8')
        old = data.setdefault('browser', {}).get('allow_javascript_apple_events')
        data['browser']['allow_javascript_apple_events'] = True
        pref.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        changed.append((pref, old))
    for pref, old in changed:
        print(f'SET {pref}: {old!r} -> True')
    subprocess.run(['open', '-a', 'Google Chrome'])


def isolated_open(url: str, app: str = 'Google Chrome', chrome_profile_dir: Path | None = None, new_instance: bool = True) -> None:
    pdir = chrome_profile_dir or profile_dir()
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / 'HERMES_GHL_AGENT_ISOLATED_PROFILE.txt').write_text(
        'Reserved for Digital Flow GHL agents. Do not browse personal tabs here.\n', encoding='utf-8'
    )
    args = [f'--user-data-dir={pdir}', '--no-first-run', '--new-window', url]
    cmd = ['open']
    if new_instance:
        cmd.append('-na')
    else:
        cmd += ['-a']
    cmd += [app, '--args'] + args
    print('Opening isolated browser profile:', pdir)
    print('URL:', url)
    subprocess.run(cmd, check=False)


def api_inventory(client: GHLClient, location_id: str, company_id: str, outdir: Path, execute: bool) -> dict[str, Any]:
    calls = {
        'locations-search': ('GET', '/locations/search', {'limit': 100, 'companyId': company_id}),
        'workflows': ('GET', '/workflows/', {'locationId': location_id}),
        'tags': ('GET', f'/locations/{location_id}/tags', {}),
        'custom-values': ('GET', f'/locations/{location_id}/customValues', {}),
        'custom-fields': ('GET', f'/locations/{location_id}/customFields', {}),
        'forms': ('GET', '/forms/', {'locationId': location_id}),
        'surveys': ('GET', '/surveys/', {'locationId': location_id}),
        'products': ('GET', '/products/', {'locationId': location_id}),
        'calendars': ('GET', '/calendars/', {'locationId': location_id}),
        'pipelines': ('GET', '/opportunities/pipelines', {'locationId': location_id}),
    }
    result = {}
    outdir.mkdir(parents=True, exist_ok=True)
    for name, (method, path, params) in calls.items():
        if not execute:
            result[name] = {'planned': True, 'method': method, 'path': path, 'params': params}
            continue
        status, payload = client.request(method, path, params=params)
        result[name] = {'status': status, 'payload': redact(payload)}
        (outdir / f'{name}.json').write_text(json.dumps(result[name], indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'{name}: HTTP {status}')
    return result


def compile_blueprint(path: Path, workflow_name: str | None = None) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    groups = ['funnelWorkflows', 'deliveryWorkflows', 'snapshotClientWorkflows']
    workflows = []
    for group in groups:
        for wf in data.get(group, []):
            if workflow_name and wf.get('name') != workflow_name:
                continue
            workflows.append({'group': group, **wf})
    if workflow_name and not workflows:
        raise SystemExit(f'Workflow not found in {path}: {workflow_name}')
    return {
        'source': str(path),
        'locationId': data.get('locationId', default_location_id()),
        'workflow_count': len(workflows),
        'official_api_capability': 'list workflows only; body create/update/publish is UI/private-adapter lane',
        'ui_macro_required': True,
        'workflows': workflows,
    }


def doctor(args, profile: dict[str, Any]) -> int:
    checks = {
        'canonical_owner': 'Digital Flow',
        'framework_root': str(HERE),
        'client_profile': profile.get('profile') if profile else None,
        'GHL_API_TOKEN_or_GHL_AGENCY_KEY': bool(os.environ.get('GHL_API_TOKEN') or os.environ.get('GHL_AGENCY_KEY')),
        'GHL_COMPANY_ID': default_company_id(),
        'GHL_SOURCE_LOCATION_ID': default_location_id(),
        'blueprint_path': str(default_blueprint_path()),
        'blueprint_exists': default_blueprint_path().exists(),
        'build_cards_path': str(default_build_cards_path()),
        'build_cards_exists': default_build_cards_path().exists(),
        'isolated_profile': str(profile_dir()),
    }
    print(json.dumps(checks, indent=2))
    if args.check_chrome_js:
        return chrome_js_check()
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description='Digital Flow GHL Agent framework: API-first assets + isolated browser UI lane')
    p.add_argument('--env-file', default=str(HERE / 'env.local'), help='optional env file; secrets are never printed')
    p.add_argument('--profile', default=os.environ.get('GHL_CLIENT_PROFILE'), help='client profile JSON, e.g. client-profiles/tax-mogul-os.json')
    sub = p.add_subparsers(dest='cmd', required=True)

    d = sub.add_parser('doctor')
    d.add_argument('--check-chrome-js', action='store_true')

    sub.add_parser('enable-chrome-js-pref')

    o = sub.add_parser('open')
    o.add_argument('--location-id')
    o.add_argument('--workflow-id')
    o.add_argument('--url')
    o.add_argument('--same-instance', action='store_true')

    inv = sub.add_parser('inventory')
    inv.add_argument('--location-id')
    inv.add_argument('--company-id')
    inv.add_argument('--outdir')
    inv.add_argument('--execute', action='store_true')

    c = sub.add_parser('compile')
    c.add_argument('--blueprint')
    c.add_argument('--workflow-name')
    c.add_argument('--out')

    a = p.parse_args(argv)
    load_env_file(Path(a.env_file))
    profile_path = Path(a.profile) if a.profile else None
    if profile_path and not profile_path.is_absolute():
        profile_path = HERE / profile_path
    profile = load_profile(profile_path)

    if a.cmd == 'doctor':
        return doctor(a, profile)
    if a.cmd == 'enable-chrome-js-pref':
        enable_chrome_js_pref()
        return 0
    if a.cmd == 'open':
        isolated_open(a.url or workflow_url(a.location_id, a.workflow_id), new_instance=not a.same_instance)
        return 0
    if a.cmd == 'inventory':
        outdir = Path(a.outdir) if a.outdir else inventory_dir()
        print(json.dumps(api_inventory(GHLClient(), a.location_id or default_location_id(), a.company_id or default_company_id(), outdir, a.execute), indent=2, ensure_ascii=False))
        return 0
    if a.cmd == 'compile':
        blueprint = Path(a.blueprint) if a.blueprint else default_blueprint_path()
        res = compile_blueprint(blueprint, a.workflow_name)
        text = json.dumps(res, indent=2, ensure_ascii=False)
        if a.out:
            Path(a.out).write_text(text, encoding='utf-8')
        print(text)
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
