import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALL_DATA_PATH = ROOT / 'allpwporbis.json'
JV_LIST_PATH = ROOT / 'JVList.json'
BIG_GROUPS_PATH = ROOT / 'BigCorpGroup.json'
OTHER_GROUPS_PATH = ROOT / 'OtherCorpGroup.json'
KONZERNFUND_PATH = ROOT / 'Konzernfund.json'

GROUPS = [
    ('SME', 'sme'),
    ('Bigcorp', 'Bigcorp'),
    ('OtherCorp', 'OtherCorp'),
    ('OtherBig', 'OtherBig'),
    ('OtherSmall', 'OtherSmall'),
    ('OtherRest', 'OtherRest'),
]
GROUP_ORDER = [name for name, _ in GROUPS]
LEVEL_ORDER = ['COMPONENT', 'SUBSYSTEM', 'SYSTEM']
RD_ORDER = ['Res', 'Dev']
D0 = Decimal('0')


def load_json(path=ALL_DATA_PATH):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dec(value):
    return Decimal(str(value or 0))


def money(value):
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def pct2(value):
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def pct4(value):
    return value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def median(values):
    values = list(values)
    if not values:
        raise ValueError('median requires at least one value')
    ordered = sorted(values)
    n = len(ordered)
    if n % 2:
        return ordered[n // 2]
    return (ordered[n // 2 - 1] + ordered[n // 2]) / Decimal(2)


def org_group(org):
    active = [label for label, field in GROUPS if org.get(field) is True]
    if len(active) != 1:
        raise ValueError(f'Expected exactly one active group for org_id {org.get("org_id")}, got {active}')
    return active[0]


def participation_rows(data=None):
    data = load_json() if data is None else data
    rows = []
    for org in data:
        oid = str(org.get('org_id'))
        group = org_group(org)
        for part in org.get('participations') or []:
            if not isinstance(part, dict) or part.get('project_id') is None:
                continue
            rows.append({
                'org_id': oid,
                'org_name': org.get('org_name'),
                'group': group,
                'project_id': str(part['project_id']),
                'role': part.get('role'),
                'coordinator': 1 if part.get('role') == 'coordinator' else 0,
                'eu_contribution': dec(part.get('eu_contribution')),
                'eu_contribution_prc': dec(part.get('eu_contribution_prc')),
                'eu_contribution_tot': dec(part.get('eu_contribution_tot')),
                'part_share': None if part.get('part_share') is None else dec(part.get('part_share')),
                'eligible': part.get('eligible'),
                'rd_type': part.get('rd_type'),
                'integration_level': part.get('integration_level'),
                'edf_call_year': part.get('edf_call_year'),
            })
    return rows


def project_table(rows=None):
    rows = participation_rows() if rows is None else rows
    projects = {}
    for row in rows:
        pid = row['project_id']
        if pid not in projects:
            projects[pid] = {
                'project_id': pid,
                'rd_type': row['rd_type'],
                'integration_level': row['integration_level'],
                'edf_call_year': row['edf_call_year'],
                'eu_contribution_prc': row['eu_contribution_prc'],
                'eu_contribution_tot': row['eu_contribution_tot'],
            }
        else:
            current = projects[pid]
            for field in ['rd_type', 'integration_level', 'eu_contribution_prc', 'eu_contribution_tot']:
                if current[field] != row[field]:
                    raise ValueError(f'Inconsistent project-level value for {pid}.{field}: {current[field]} vs {row[field]}')
    return projects
