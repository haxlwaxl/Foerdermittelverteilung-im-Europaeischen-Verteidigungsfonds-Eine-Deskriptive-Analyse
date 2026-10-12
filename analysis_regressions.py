import math
from decimal import Decimal

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import chi2_contingency

from analysis_common import GROUP_ORDER, LEVEL_ORDER, load_json, participation_rows

GROUP_ORDER = ['SME', 'Bigcorp', 'OtherCorp', 'OtherBig', 'OtherSmall', 'OtherRest']


def build_frame():
    rows = participation_rows(load_json())
    df = pd.DataFrame(rows)
    df['eu_contribution'] = pd.to_numeric(df['eu_contribution'], errors='raise')
    df['ln_funding'] = np.log1p(df['eu_contribution'])
    df['part_share_pp'] = pd.to_numeric(df['part_share'], errors='coerce') * 100
    df['group'] = pd.Categorical(df['group'], categories=GROUP_ORDER)
    df['rd_type'] = pd.Categorical(df['rd_type'], categories=['Res', 'Dev'])
    df['integration_level'] = pd.Categorical(df['integration_level'], categories=LEVEL_ORDER)
    return df


def fit_clustered(formula, data):
    return smf.ols(formula, data=data).fit(cov_type='cluster', cov_kwds={'groups': data['project_id']})


def print_model_summary(label, model):
    print(f'MODEL_{label}')
    print('N', int(model.nobs))
    print('clusters', int(model_df_project_count(model)))
    print('r_squared', f'{model.rsquared:.8f}')
    print('adjusted_r_squared', f'{model.rsquared_adj:.8f}')


def model_df_project_count(model):
    return len(model.model.data.frame['project_id'].unique())


def print_selected_terms(model, terms):
    ci = model.conf_int(alpha=0.05)
    print('term|beta|clustered_se|t_value|p_value|ci_lower|ci_upper|pct_exp_beta_minus_1')
    for label, term in terms.items():
        beta = model.params[term]
        se = model.bse[term]
        t = model.tvalues[term]
        p = model.pvalues[term]
        lower, upper = ci.loc[term]
        transformed = 100 * (math.exp(beta) - 1)
        print(f'{label}|{beta:.8f}|{se:.8f}|{t:.6f}|{p:.8g}|{lower:.8f}|{upper:.8f}|{transformed:.6f}')


def crosstab_step(df):
    filtered = df[df['integration_level'].isin(LEVEL_ORDER)].copy()
    table = pd.crosstab(filtered['group'], filtered['integration_level']).reindex(index=GROUP_ORDER, columns=LEVEL_ORDER, fill_value=0)
    chi2, p_chi, dof, _ = chi2_contingency(table)
    n = table.values.sum()
    cramers_v = math.sqrt((chi2 / n) / min(table.shape[1] - 1, table.shape[0] - 1))
    print('CROSSTAB_GROUP_INTEGRATION_LEVEL')
    print('group|component_n|component_pct|subsystem_n|subsystem_pct|system_n|system_pct|total')
    for group in GROUP_ORDER:
        values = table.loc[group]
        total = int(values.sum())
        print(f'{group}|{int(values["COMPONENT"])}|{values["COMPONENT"] / total * 100:.2f}|{int(values["SUBSYSTEM"])}|{values["SUBSYSTEM"] / total * 100:.2f}|{int(values["SYSTEM"])}|{values["SYSTEM"] / total * 100:.2f}|{total}')
    print('TOTAL|' + '|'.join(str(int(table[level].sum())) for level in LEVEL_ORDER) + f'|||{n}')
    print('cramers_v', f'{cramers_v:.8f}')
    print('chi_square', f'{chi2:.8f}')
    print('chi_square_df', dof)
    print('chi_square_p_value', f'{p_chi:.8g}')


def nested_models(df):
    filtered = df[df['integration_level'].isin(LEVEL_ORDER)].copy()
    formulas = {
        'A': "ln_funding ~ C(group, Treatment(reference='SME'))",
        'B': "ln_funding ~ C(group, Treatment(reference='SME')) + C(rd_type, Treatment(reference='Res')) + C(integration_level, Treatment(reference='COMPONENT'))",
        'C': "ln_funding ~ C(group, Treatment(reference='SME')) + C(rd_type, Treatment(reference='Res')) + C(integration_level, Treatment(reference='COMPONENT')) + coordinator",
    }
    models = {key: fit_clustered(formula, filtered) for key, formula in formulas.items()}
    terms = {group: f"C(group, Treatment(reference='SME'))[T.{group}]" for group in GROUP_ORDER if group != 'SME'}
    print('NESTED_MODELS')
    print('model|N|projects|r_squared|adjusted_r_squared')
    for key, model in models.items():
        print(f'{key}|{int(model.nobs)}|{filtered["project_id"].nunique()}|{model.rsquared:.8f}|{model.rsquared_adj:.8f}')
    print('NESTED_GROUP_TERMS')
    print('model|group|beta|clustered_se|p_value|pct_exp_beta_minus_1')
    for key, model in models.items():
        print(f'{key}|SME|reference|reference|reference|reference')
        for group, term in terms.items():
            beta = model.params[term]
            se = model.bse[term]
            pval = model.pvalues[term]
            transformed = 100 * (math.exp(beta) - 1)
            print(f'{key}|{group}|{beta:.8f}|{se:.8f}|{pval:.8g}|{transformed:.6f}')
    print('NESTED_COEFFICIENT_CHANGES')
    print('group|beta_A|beta_B|change_A_to_B|beta_C|change_B_to_C')
    for group, term in terms.items():
        a = models['A'].params[term]
        b = models['B'].params[term]
        c = models['C'].params[term]
        print(f'{group}|{a:.8f}|{b:.8f}|{b - a:.8f}|{c:.8f}|{c - b:.8f}')


def fixed_effects_ln_funding(df):
    formula = "ln_funding ~ C(group, Treatment(reference='SME')) + coordinator + C(project_id)"
    model = fit_clustered(formula, df)
    fe_only = smf.ols("ln_funding ~ C(project_id)", data=df).fit()
    within_r2 = 1 - (np.sum(model.resid ** 2) / np.sum(fe_only.resid ** 2))
    terms = {
        'Bigcorp': "C(group, Treatment(reference='SME'))[T.Bigcorp]",
        'OtherCorp': "C(group, Treatment(reference='SME'))[T.OtherCorp]",
        'OtherBig': "C(group, Treatment(reference='SME'))[T.OtherBig]",
        'OtherSmall': "C(group, Treatment(reference='SME'))[T.OtherSmall]",
        'OtherRest': "C(group, Treatment(reference='SME'))[T.OtherRest]",
        'Coordinator': 'coordinator',
    }
    group_counts = df.groupby('project_id', observed=True)['group'].nunique()
    variation_projects = group_counts[group_counts >= 2].index
    variation_observations = int(df['project_id'].isin(variation_projects).sum())
    print('FE_LN_FUNDING_MODEL')
    print('N', int(model.nobs))
    print('projects', df['project_id'].nunique())
    print('clusters', df['project_id'].nunique())
    print('project_fixed_effects', df['project_id'].nunique())
    print('r_squared', f'{model.rsquared:.8f}')
    print('adjusted_r_squared', f'{model.rsquared_adj:.8f}')
    print('within_r_squared', f'{within_r2:.8f}')
    print('projects_with_at_least_two_groups', len(variation_projects))
    print('observations_in_projects_with_at_least_two_groups', variation_observations)
    print_selected_terms(model, terms)


def fixed_effects_part_share(df):
    valid = df[df['part_share_pp'].notna()].copy()
    formula = "part_share_pp ~ C(group, Treatment(reference='SME')) + coordinator + C(project_id)"
    model = fit_clustered(formula, valid)
    fe_only = smf.ols("part_share_pp ~ C(project_id)", data=valid).fit()
    within_r2 = 1 - (np.sum(model.resid ** 2) / np.sum(fe_only.resid ** 2))
    project_sums = valid.groupby('project_id', observed=True)['part_share'].sum()
    group_counts = valid.groupby('project_id', observed=True)['group'].nunique()
    variation_projects = group_counts[group_counts >= 2].index
    variation_observations = int(valid['project_id'].isin(variation_projects).sum())
    terms = {
        'Bigcorp': "C(group, Treatment(reference='SME'))[T.Bigcorp]",
        'OtherCorp': "C(group, Treatment(reference='SME'))[T.OtherCorp]",
        'OtherBig': "C(group, Treatment(reference='SME'))[T.OtherBig]",
        'OtherSmall': "C(group, Treatment(reference='SME'))[T.OtherSmall]",
        'OtherRest': "C(group, Treatment(reference='SME'))[T.OtherRest]",
        'Coordinator': 'coordinator',
    }
    print('FE_PART_SHARE_QA')
    print('original_project_participations', len(df))
    print('excluded_invalid_part_share', int(df['part_share_pp'].isna().sum()))
    print('final_observations', len(valid))
    print('final_projects', valid['project_id'].nunique())
    print('part_share_pp_min', f'{valid["part_share_pp"].min():.8f}')
    print('part_share_pp_median', f'{valid["part_share_pp"].median():.8f}')
    print('part_share_pp_mean', f'{valid["part_share_pp"].mean():.8f}')
    print('part_share_pp_max', f'{valid["part_share_pp"].max():.8f}')
    print('project_share_sum_min', f'{project_sums.min():.12f}')
    print('project_share_sum_median', f'{project_sums.median():.12f}')
    print('project_share_sum_max', f'{project_sums.max():.12f}')
    print('projects_share_sum_deviation_gt_0_0001', int((project_sums.sub(1).abs() > Decimal('0.0001')).sum()))
    print('part_share_values_gt_1', int((valid['part_share'] > 1).sum()))
    print('part_share_pp_values_gt_100', int((valid['part_share_pp'] > 100).sum()))
    print('FE_PART_SHARE_MODEL')
    print('N', int(model.nobs))
    print('projects', valid['project_id'].nunique())
    print('clusters', valid['project_id'].nunique())
    print('r_squared', f'{model.rsquared:.8f}')
    print('adjusted_r_squared', f'{model.rsquared_adj:.8f}')
    print('within_r_squared', f'{within_r2:.8f}')
    print('projects_with_at_least_two_groups', len(variation_projects))
    print('observations_in_projects_with_at_least_two_groups', variation_observations)
    ci = model.conf_int(alpha=0.05)
    print('term|beta_percentage_points|clustered_se|t_value|p_value|ci_lower|ci_upper')
    for label, term in terms.items():
        beta = model.params[term]
        se = model.bse[term]
        t = model.tvalues[term]
        p = model.pvalues[term]
        lower, upper = ci.loc[term]
        print(f'{label}|{beta:.8f}|{se:.8f}|{t:.6f}|{p:.8g}|{lower:.8f}|{upper:.8f}')


def main():
    df = build_frame()
    crosstab_step(df)
    nested_models(df)
    fixed_effects_ln_funding(df)
    fixed_effects_part_share(df)


if __name__ == '__main__':
    main()
