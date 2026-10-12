from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

from analysis_common import BIG_GROUPS_PATH, D0, GROUPS, JV_LIST_PATH, KONZERNFUND_PATH, OTHER_GROUPS_PATH, load_json, money, pct4


def dec(value):
    return Decimal(str(value or 0))


def current_konzernfund_metrics():
    data = load_json(KONZERNFUND_PATH)
    actors = [row for row in data if row.get('rank') is not None]
    actors.sort(key=lambda row: int(row['rank']))
    total = sum((dec(row['final_funding']) for row in actors), D0)
    print('CURRENT_KONZERNFUND_METRICS')
    print('actors', len(actors))
    print('total_final_funding', money(total))
    print('metric|ranks|final_funding|funding_share_pct')
    for label, n in [('CR1', 1), ('CR4', 4), ('CR10', 10), ('CR20', 20)]:
        subtotal = sum((dec(row['final_funding']) for row in actors[:n]), D0)
        share = subtotal / total
        print(f'{label}|{"1" if n == 1 else "1-" + str(n)}|{money(subtotal)}|{pct4(share * 100)}')
    hhi = sum((dec(row['final_funding']) / total) ** 2 for row in actors)
    print('HHI', hhi.quantize(Decimal('0.00000001')))
    print('HHI_10000', (hhi * 10000).quantize(Decimal('0.01')))
    print('top20_current')
    print('rank|actor_id|actor_name|actor_type|n_legal_entities|final_funding|funding_share_pct')
    for row in actors[:20]:
        print(f'{row["rank"]}|{row["actor_id"]}|{row["actor_name"]}|{row["actor_type"]}|{row["n_legal_entities"]}|{money(dec(row["final_funding"]))}|{pct4(dec(row["funding_share"]))}')


def unadjusted_jv_metrics():
    all_data = load_json()
    big_groups = load_json(BIG_GROUPS_PATH)
    other_groups = load_json(OTHER_GROUPS_PATH)
    jv_list = load_json(JV_LIST_PATH)
    org_by_id = {str(org['org_id']): org for org in all_data if org.get('org_id') is not None}
    jv_ids = {str(row['org_id']) for row in jv_list}
    actors = []

    def add(actor_id, actor_name, actor_type, n_legal_entities, final_funding):
        actors.append({
            'actor_id': str(actor_id),
            'actor_name': actor_name,
            'actor_type': actor_type,
            'n_legal_entities': n_legal_entities,
            'final_funding': final_funding,
        })

    for org in all_data:
        oid = str(org.get('org_id'))
        if oid in jv_ids:
            continue
        actor_type = None
        for label, field in GROUPS:
            if org.get(field) is True:
                actor_type = label
                break
        if actor_type in {'Bigcorp', 'OtherCorp'}:
            continue
        if actor_type is not None:
            add(oid, org.get('org_name'), actor_type, 1, dec(org.get('total_eu_contribution')))

    for group in big_groups:
        org_ids = [str(oid) for oid in group.get('org_ids', [])]
        funding = sum((dec(org_by_id[oid].get('total_eu_contribution')) for oid in org_ids if oid in org_by_id and oid not in jv_ids), D0)
        add(group['Bigcorp_group_id'], group['Bigcorp_group_name'], 'Bigcorp', len(org_ids), funding)

    for group in other_groups:
        org_ids = [str(oid) for oid in group.get('org_ids', [])]
        funding = sum((dec(org_by_id[oid].get('total_eu_contribution')) for oid in org_ids if oid in org_by_id and oid not in jv_ids), D0)
        add(group['Ocorp_group_id'], group['Ocorp_group_name'], 'OtherCorp', len(org_ids), funding)

    for row in jv_list:
        oid = str(row['org_id'])
        add(oid, row.get('org_name') or org_by_id[oid].get('org_name'), 'JointVenture', 1, dec(org_by_id[oid].get('total_eu_contribution')))

    actors.sort(key=lambda actor: (-actor['final_funding'], actor['actor_name'] or '', actor['actor_id']))
    for index, actor in enumerate(actors, start=1):
        actor['rank'] = index
    total = sum((actor['final_funding'] for actor in actors), D0)
    print('UNADJUSTED_JV_METRICS')
    print('actors', len(actors))
    print('total_final_funding', money(total))
    print('matches_expected_total', money(total) == Decimal('3171545781.05'))
    print('metric|ranks|final_funding|funding_share_pct')
    for label, n in [('CR1', 1), ('CR4', 4), ('CR10', 10), ('CR20', 20)]:
        subtotal = sum((actor['final_funding'] for actor in actors[:n]), D0)
        share = subtotal / total
        print(f'{label}|{"1" if n == 1 else "1-" + str(n)}|{money(subtotal)}|{pct4(share * 100)}')
    hhi = sum((actor['final_funding'] / total) ** 2 for actor in actors)
    print('HHI', hhi.quantize(Decimal('0.00000001')))
    print('HHI_10000', (hhi * 10000).quantize(Decimal('0.01')))
    print('top20_unadjusted')
    print('rank|actor_id|actor_name|actor_type|n_legal_entities|final_funding|funding_share_pct')
    for actor in actors[:20]:
        share = actor['final_funding'] / total
        print(f'{actor["rank"]}|{actor["actor_id"]}|{actor["actor_name"]}|{actor["actor_type"]}|{actor["n_legal_entities"]}|{money(actor["final_funding"])}|{pct4(share * 100)}')


def main():
    current_konzernfund_metrics()
    unadjusted_jv_metrics()


if __name__ == '__main__':
    main()
