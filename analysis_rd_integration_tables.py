from collections import defaultdict
from decimal import Decimal

from analysis_common import D0, GROUP_ORDER, LEVEL_ORDER, RD_ORDER, load_json, money, participation_rows, pct2, pct4

CATEGORIES = [(rd, level) for rd in RD_ORDER for level in LEVEL_ORDER]


def main():
    data = load_json()
    rows = participation_rows(data)
    projects = {}
    for row in rows:
        pid = row['project_id']
        projects.setdefault(pid, row)
    valid_projects = {
        pid: row for pid, row in projects.items()
        if row['rd_type'] in RD_ORDER and row['integration_level'] in LEVEL_ORDER
    }

    counts = defaultdict(int)
    sums = defaultdict(lambda: D0)
    group_cell_funding = defaultdict(lambda: D0)

    for row in rows:
        pid = row['project_id']
        if pid not in valid_projects:
            continue
        category = (valid_projects[pid]['rd_type'], valid_projects[pid]['integration_level'])
        counts[category] += 0
        group_cell_funding[(row['group'], category)] += row['eu_contribution']

    counts = defaultdict(int)
    for pid, row in valid_projects.items():
        category = (row['rd_type'], row['integration_level'])
        counts[category] += 1
        sums[category] += row['eu_contribution_prc']

    grand_total = sum(sums.values(), D0)

    print('TABLE_A_COUNTS')
    print('rd_type|COMPONENT|SUBSYSTEM|SYSTEM|ROW_TOTAL')
    for rd in RD_ORDER:
        row = [counts[(rd, level)] for level in LEVEL_ORDER]
        print(f'{rd}|' + '|'.join(str(value) for value in row) + f'|{sum(row)}')
    col_totals = [sum(counts[(rd, level)] for rd in RD_ORDER) for level in LEVEL_ORDER]
    print('COL_TOTAL|' + '|'.join(str(value) for value in col_totals) + f'|{sum(col_totals)}')

    print('TABLE_B_SUM_EU_CONTRIBUTION_PRC')
    print('rd_type|COMPONENT|SUBSYSTEM|SYSTEM|ROW_TOTAL')
    for rd in RD_ORDER:
        row = [sums[(rd, level)] for level in LEVEL_ORDER]
        print(f'{rd}|' + '|'.join(str(money(value)) for value in row) + f'|{money(sum(row, D0))}')
    col_sum_totals = [sum((sums[(rd, level)] for rd in RD_ORDER), D0) for level in LEVEL_ORDER]
    print('COL_TOTAL|' + '|'.join(str(money(value)) for value in col_sum_totals) + f'|{money(sum(col_sum_totals, D0))}')

    print('TABLE_B_SHARE_OF_TOTAL_PCT')
    print('rd_type|COMPONENT|SUBSYSTEM|SYSTEM|ROW_TOTAL')
    for rd in RD_ORDER:
        row = [sums[(rd, level)] for level in LEVEL_ORDER]
        print(f'{rd}|' + '|'.join(str(pct2(value * 100 / grand_total)) for value in row) + f'|{pct2(sum(row, D0) * 100 / grand_total)}')
    col_share_totals = [sum((sums[(rd, level)] for rd in RD_ORDER), D0) for level in LEVEL_ORDER]
    print('COL_TOTAL|' + '|'.join(str(pct2(value * 100 / grand_total)) for value in col_share_totals) + f'|{pct2(sum(col_share_totals, D0) * 100 / grand_total)}')

    print('TABLE_C_MEAN_FUNDING_PER_PROJECT')
    print('rd_type|COMPONENT|SUBSYSTEM|SYSTEM|ROW_AVG')
    for rd in RD_ORDER:
        row_c = sum(counts[(rd, level)] for level in LEVEL_ORDER)
        row_s = sum((sums[(rd, level)] for level in LEVEL_ORDER), D0)
        cells = [str(money(sums[(rd, level)] / counts[(rd, level)])) if counts[(rd, level)] else 'n/a' for level in LEVEL_ORDER]
        print(f'{rd}|' + '|'.join(cells) + f'|{money(row_s / row_c)}')
    col_line = []
    for level in LEVEL_ORDER:
        col_c = sum(counts[(rd, level)] for rd in RD_ORDER)
        col_s = sum((sums[(rd, level)] for rd in RD_ORDER), D0)
        col_line.append(str(money(col_s / col_c)) if col_c else 'n/a')
    print('COL_AVG|' + '|'.join(col_line) + f'|{money(grand_total / Decimal(len(valid_projects)))}')

    print('TABLE_D_FUNDING_SHARE_OVER_PROJECT_SHARE')
    print('rd_type|COMPONENT|SUBSYSTEM|SYSTEM|ROW_RATIO')
    total_projects = Decimal(len(valid_projects))
    for rd in RD_ORDER:
        cells = []
        for level in LEVEL_ORDER:
            project_share = Decimal(counts[(rd, level)]) * 100 / total_projects
            funding_share = sums[(rd, level)] * 100 / grand_total
            cells.append(str(pct4(funding_share / project_share)) if project_share else 'n/a')
        row_c = sum(counts[(rd, level)] for level in LEVEL_ORDER)
        row_s = sum((sums[(rd, level)] for level in LEVEL_ORDER), D0)
        row_ratio = (row_s * 100 / grand_total) / (Decimal(row_c) * 100 / total_projects)
        print(f'{rd}|' + '|'.join(cells) + f'|{pct4(row_ratio)}')
    col_ratios = []
    for level in LEVEL_ORDER:
        col_c = sum(counts[(rd, level)] for rd in RD_ORDER)
        col_s = sum((sums[(rd, level)] for rd in RD_ORDER), D0)
        col_ratios.append((col_s * 100 / grand_total) / (Decimal(col_c) * 100 / total_projects))
    print('COL_RATIO|' + '|'.join(str(pct4(value)) for value in col_ratios) + '|1.0000')

    print('TABLE_E_GROUP_FUNDING_BY_CATEGORY')
    print('group|' + '|'.join(f'{rd}-{level.capitalize()}' for rd, level in CATEGORIES) + '|ROW_TOTAL')
    col_totals = {category: D0 for category in CATEGORIES}
    for group in GROUP_ORDER:
        row = [group_cell_funding[(group, category)] for category in CATEGORIES]
        for category, value in zip(CATEGORIES, row):
            col_totals[category] += value
        print(f'{group}|' + '|'.join(str(money(value)) for value in row) + f'|{money(sum(row, D0))}')
    print('COL_TOTAL|' + '|'.join(str(money(col_totals[category])) for category in CATEGORIES) + f'|{money(sum(col_totals.values(), D0))}')

    print('TABLE_F_GROUP_SHARE_BY_CATEGORY')
    print('group|' + '|'.join(f'{rd}-{level.capitalize()}' for rd, level in CATEGORIES))
    for group in GROUP_ORDER:
        cells = [str(pct2(group_cell_funding[(group, category)] * 100 / col_totals[category])) if col_totals[category] else '0.00' for category in CATEGORIES]
        print(f'{group}|' + '|'.join(cells))
    print('COL_CHECK_SUM_PCT|' + '|'.join(str(pct2(sum((group_cell_funding[(group, category)] * 100 / col_totals[category] for group in GROUP_ORDER), D0))) for category in CATEGORIES))


if __name__ == '__main__':
    main()
