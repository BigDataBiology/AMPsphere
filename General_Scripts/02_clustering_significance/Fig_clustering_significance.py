import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from math import log

lv1 = pd.read_table('outputs/output_clustering_significance_levelI.tsv')
lv2 = pd.read_table('outputs/output_clustering_significance_levelII.tsv')
lv3 = pd.read_table('outputs/output_clustering_significance_levelIII.tsv')

cl = ['I', 'II', 'III']

lv1['min_id'] = lv1[['identity', 'gap_identity']].min(axis=1)
lv2['min_id'] = lv2[['identity', 'gap_identity']].min(axis=1)
lv3['min_id'] = lv3[['identity', 'gap_identity']].min(axis=1)

lv1['Log(E-value)'] = lv1.evalue.apply(lambda x: log(x, 10))
lv2['Log(E-value)'] = lv2.evalue.apply(lambda x: log(x, 10))
lv3['Log(E-value)'] = lv3.evalue.apply(lambda x: log(x, 10))

fig, axarr = plt.subplot_mosaic([['a)', 'b)', 'c)']], constrained_layout=True)
sns.scatterplot(ax=axarr['a)'], data=lv1, x='min_id', y='Log(E-value)', s=2.5, alpha=0.5)
sns.scatterplot(ax=axarr['b)'], data=lv2, x='min_id', y='Log(E-value)', s=2.5, alpha=0.5, legend=False)
sns.scatterplot(ax=axarr['c)'], data=lv3, x='min_id', y='Log(E-value)', s=2.5, alpha=0.5, legend=False)

for idx, (label, ax) in enumerate(axarr.items()):
    ax.set_ylim(20, -80)
    ax.set_title(f'Clstr. Lv. {cl[idx]}', fontfamily='Sans Serif', fontstyle='italic')
    ax.axhline(y=log(1e-5, 10), color='black', linestyle='dashed', linewidth=1.0)
    ax.set_xlabel('Identity (%)')
    if idx > 0:
        ax.set_ylabel(None)
fig.tight_layout()

fig.savefig('outputs/clustering_significance.svg')

