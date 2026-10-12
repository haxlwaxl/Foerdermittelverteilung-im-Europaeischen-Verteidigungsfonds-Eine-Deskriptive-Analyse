from collections import defaultdict
from decimal import Decimal

from analysis_common import D0, GROUP_ORDER, LEVEL_ORDER, load_json, median, money, org_group, participation_rows, pct2, pct4


def print_table_1(data):
    orgs_by_group = defaultdict(set)
    pairs_by_group = defaultdict(set)
    projects_by_group = defaultdict(set)
    for org in data:
        group = org_group(org)
        oid = str(org.get('org_id'))
        orgs_by_group[group].add(oid)
        for part in org.get('participations') or []:
            if isinstance(part, dict) and part.get('project_id') is not None:
                pid = str(part['project_id'])
                pairs_by_group[group].add((oid, pid))
                projects_by_group[group].add(pid)
    total_orgs = len(data)
    total_pairs = len(set().union(*pairs_by_group.values()))
    print('TABLE_1')
    print('group|legal_entities|share_legal_entities_pct|project_participations|share_project_participations_pct|projects')
    for group in GROUP_ORDER:
        print(f'{group}|{len(orgs_by_group[group])}|{pct2(Decimal(len(orgs_by_group[group])) * 100 / total_orgs)}|{len(pairs_by_group[group])}|{pct2(Decimal(len(pairs_by_group[group])) * 100 / total_pairs)}|{len(projects_by_group[group])}')
    total_projects = len(set().union(*projects_by_group.values()))
    print(f'TOTAL|{total_orgs}|100.00|{total_pairs}|100.00|{total_projects}')


def print_table_2(data):
    org_values = defaultdict(dict)
    pair_values = defaultdict(dict)
    for org in data:
        group = org_group(org)
        oid = str(org.get('org_id'))
        org_values[group][oid] = Decimal(str(org.get('total_eu_contribution', 0)))
        for part in org.get('participations') or []:
            if isinstance(part, dict) and part.get('project_id') is not None:
                pair_values[group][(oid, str(part['project_id']))] = Decimal(str(part.get('eu_contribution', 0)))
    print('TABLE_2')
    print('group|legal_entities|total_funding|mean_per_entity|median_per_entity|project_participations|mean_per_participation|median_per_participation')
    all_org = {}
    all_pairs = {}
    for group in GROUP_ORDER:
        entities = org_values[group]
        pairs = pair_values[group]
        total = sum(entities.values(), D0)
        mean_entity = total / Decimal(len(entities))
        med_entity = median(list(entities.values()))
        mean_pair = total / Decimal(len(pairs))
        med_pair = median(list(pairs.values()))
        all_org.update(entities)
        all_pairs.update(pairs)
        print(f'{group}|{len(entities)}|{money(total)}|{money(mean_entity)}|{money(med_entity)}|{len(pairs)}|{money(mean_pair)}|{money(med_pair)}')
    total = sum(all_org.values(), D0)
    print(f'TOTAL|{len(all_org)}|{money(total)}|{money(total / Decimal(len(all_org)))}|{money(median(list(all_org.values())))}|{len(all_pairs)}|{money(total / Decimal(len(all_pairs)))}|{money(median(list(all_pairs.values())))}')


def print_table_3(data):
    funding = defaultdict(lambda: D0)
    pairs = defaultdict(set)
    for org in data:
        group = org_group(org)
        funding[group] += Decimal(str(org.get('total_eu_contribution', 0)))
        oid = str(org.get('org_id'))
        for part in org.get('participations') or []:
            if isinstance(part, dict) and part.get('project_id') is not None:
                pairs[group].add((oid, str(part['project_id'])))
    total_funding = sum(funding.values(), D0)
    total_pairs = len(set().union(*pairs.values()))
    print('TABLE_3')
    print('group|funding_share_pct|participation_share_pct|rfr')
    for group in GROUP_ORDER:
        fs = funding[group] * 100 / total_funding
        ps = Decimal(len(pairs[group])) * 100 / Decimal(total_pairs)
        rfr = fs / ps
        print(f'{group}|{pct2(fs)}|{pct2(ps)}|{pct4(rfr)}')
    print('TOTAL|100.00|100.00|1.0000')


def print_table_4(data):
    participations = defaultdict(set)
    coordinators = defaultdict(set)
    for org in data:
        group = org_group(org)
        oid = str(org.get('org_id'))
        for part in org.get('participations') or []:
            if not isinstance(part, dict) or part.get('project_id') is None:
                continue
            pair = (oid, str(part['project_id']))
            participations[group].add(pair)
            if part.get('role') == 'coordinator':
                coordinators[group].add(pair)
    total_participations = len(set().union(*participations.values()))
    total_coordinators = len(set().union(*coordinators.values()))
    print('TABLE_4')
    print('group|project_participations|coordinator_roles|share_all_coordinator_roles_pct|coordinator_rate_within_group_pct')
    for group in GROUP_ORDER:
        n_part = len(participations[group])
        n_coord = len(coordinators[group])
        print(f'{group}|{n_part}|{n_coord}|{pct2(Decimal(n_coord) * 100 / total_coordinators)}|{pct2(Decimal(n_coord) * 100 / n_part)}')
    print(f'TOTAL|{total_participations}|{total_coordinators}|100.00|{pct2(Decimal(total_coordinators) * 100 / total_participations)}')


def print_prc_participation_table(rows):
    values = defaultdict(dict)
    for row in rows:
        values[row['group']][(row['org_id'], row['project_id'])] = None if row['part_share'] is None else row['part_share'] * 100
    print('PRC_SHARE_PER_PARTICIPATION')
    print('group|project_participations|valid_part_share_n|missing_part_share_n|average_prc_share_pct|median_prc_share_pct')
    all_values = [value for group_values in values.values() for value in group_values.values()]
    for group in GROUP_ORDER:
        all_group_values = list(values[group].values())
        valid = [value for value in all_group_values if value is not None]
        print(f'{group}|{len(all_group_values)}|{len(valid)}|{len(all_group_values) - len(valid)}|{pct2(sum(valid, D0) / len(valid))}|{pct2(median(valid))}')
    valid = [value for value in all_values if value is not None]
    print(f'TOTAL|{len(all_values)}|{len(valid)}|{len(all_values) - len(valid)}|{pct2(sum(valid, D0) / len(valid))}|{pct2(median(valid))}')


def print_project_share_table(rows):
    projects = {}
    group_funding = {group: defaultdict(lambda: D0) for group in GROUP_ORDER}
    group_projects = {group: set() for group in GROUP_ORDER}
    for row in rows:
        pid = row['project_id']
        projects.setdefault(pid, row['eu_contribution_prc'])
        if projects[pid] != row['eu_contribution_prc']:
            raise ValueError(f'Inconsistent eu_contribution_prc for {pid}')
        group = row['group']
        group_projects[group].add(pid)
        group_funding[group][pid] += row['eu_contribution']
    valid_projects = {pid for pid, total in projects.items() if total > 0}
    print('PROJECT_LEVEL_GROUP_SHARE_ALL_PROJECTS')
    print('group|mean_share_all_projects_pct|median_share_all_projects_pct|projects_with_group|share_projects_with_group_pct')
    for group in GROUP_ORDER:
        shares = [group_funding[group][pid] / projects[pid] for pid in valid_projects]
        mean_share = sum(shares, D0) / Decimal(len(shares)) * 100
        median_share = median(shares) * 100
        present = len(group_projects[group] & valid_projects)
        project_share = Decimal(present) * 100 / Decimal(len(valid_projects))
        print(f'{group}|{pct2(mean_share)}|{pct2(median_share)}|{present}|{pct2(project_share)}')


def main():
    data = load_json()
    rows = participation_rows(data)
    print_table_1(data)
    print_table_2(data)
    print_table_3(data)
    print_table_4(data)
    print_prc_participation_table(rows)
    print_project_share_table(rows)


if __name__ == '__main__':
    main()
