import pandas as pd
import numpy as np
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt

from matplotlib import cm
from scipy import stats
from itertools import permutations
from statsmodels.stats.multitest import multipletests

plt.rcParams['svg.fonttype'] = 'none'

meta = pd.read_table('data/metadata.tsv.gz')
syns = pd.read_table('data/general_envo_names.tsv.gz')

higher_level = {'sediment' : 'other',
        'bird gut' : 'other animal',
        'cat gut' : 'mammal gut',
        'insect associated' : 'other animal',
        'human urogenital tract' : 'other human',
        'dog gut' : 'mammal gut',
        'fermented food' : 'anthropogenic',
        'groundwater' : 'aquatic',
        'coral associated' : 'other animal',
        'rat gut' : 'mammal gut',
        'human associated' : 'other human',
        'cattle gut' : 'mammal gut',
        'deer gut' : 'mammal gut',
        'mouse gut' : 'mammal gut',
        'river associated' : 'aquatic',
        'primate gut' : 'mammal gut',
        'human respiratory tract' : 'other human',
        'cattle rumen' : 'other animal',
        'human saliva' : 'other human',
        'activated sludge' : 'anthropogenic',
        'lake associated' : 'aquatic',
        'wastewater' : 'anthropogenic',
        'chicken gut' : 'other animal',
        'air' : 'other',
        'human mouth' : 'other human',
        'plant associated' : 'soil/plant',
        'water associated' : 'aquatic',
        'pig gut' : 'mammal gut',
        'human skin' : 'other human',
        'marine' : 'aquatic',
        'soil' : 'soil/plant',
        'built environment' : 'anthropogenic',
        'human gut' : 'human gut',
        'anthropogenic': 'anthropogenic',
        'bear gut' : 'mammal gut'}

is_host_associated = {'human gut' : True,
        'soil/plant' : False,
        'aquatic' : False,
        'anthropogenic' : False,
        'other human' : True,
        'mammal gut' : True,
        'other animal' : True,
        'other' : False}

meta = meta.merge(syns[['general_envo_name', 'host_tax_id', 'microontology']], on=['microontology', 'host_tax_id'])
meta['higher'] = meta['general_envo_name'].map(lambda g: higher_level.get(g, 'other'))
meta.set_index('sample_accession', inplace=True)
nmeta = meta[['higher', 'latitude', 'longitude']].drop_duplicates()

fig, ax = plt.subplots(figsize=(8, 6))
countries = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
countries.plot(color="gainsboro", ax=ax)
color_map = {'human gut' : (0.8509803921568627, 0.37254901960784315, 0.00784313725490196),
        'soil/plant' : (0.10588235294117647, 0.6196078431372549, 0.4666666666666667),
        'aquatic' : (0.4588235294117647, 0.4392156862745098, 0.7019607843137254),
        'anthropogenic' : (0.9058823529411765, 0.1607843137254902, 0.5411764705882353),
        'other human' : (0.4, 0.6509803921568628, 0.11764705882352941),
        'mammal gut' : (0.9019607843137255, 0.6705882352941176, 0.00784313725490196),
        'other animal' : (0.6509803921568628, 0.4627450980392157, 0.11372549019607843),
        'other' : (0.4, 0.4, 0.4)}

for hab,c in color_map.items():
    sel = nmeta.query('higher == @hab')
    sel.plot(x="longitude", y="latitude", kind="scatter",
        c=[c for _ in range(len(sel))], label=hab,
        colormap="YlOrRd", s=4.5, ax=ax)

sns.despine(fig, trim=True)
ax.set_xlabel(None)
ax.set_ylabel(None)
ax.set_xticks([])
ax.set_yticks([])
ax.tick_params(left=False,
               labelleft=False,
               bottom=False,
               labelbottom=False)
#fig.show()
fig.tight_layout()
ax.legend(loc=1)
fig.savefig('map_habitat.png', dpi=1200)
fig.savefig('map_habitat.svg', dpi=1200)

fig,ax = plt.subplots()
general = meta['general_envo_name'].value_counts()
general = general[general > 100]
general['other'] = len(meta) - general.sum()
general.plot(kind='barh', ax=ax)
ax.set_xlabel('Number of samples')
sns.despine(fig, trim=True)
fig.tight_layout()
fig.savefig('samples_per_habitat.svg')

samples = pd.read_table('data/samples-min500k-assembly-prodigal-stats.tsv.gz', index_col=0)
gmsc = pd.read_table("data/gmsc_amp_genes_envohr_source.tsv.gz")
gmsc = gmsc[gmsc.is_metagenomic == True]
gmsc = gmsc[['amp', 'sample']].drop_duplicates().groupby('sample').agg('size')
samples = pd.concat([samples, gmsc], axis=1).rename({0: 'ampsphere_amps'}, axis=1)

for c in ['inserts_filtered', 'smORFs', 'assembly_total_length', 'ampsphere_amps']:
    meta[c] = samples[c]

meta['smorfs_per_assembly_mbps'] = meta.eval('1_000_000 * smORFs/assembly_total_length')
meta['ampsphere_amps_per_assembly_mbps'] = meta.eval('1_000_000 * ampsphere_amps/assembly_total_length')

inserts_filtered = meta.groupby('general_envo_name').sum()['inserts_filtered']
inserts_filtered = inserts_filtered.reindex(general.index)
inserts_filtered['other'] = meta['inserts_filtered'].sum() - inserts_filtered.sum()
inserts_filtered //= 1000_000_000

fig, ax = plt.subplots()
inserts_filtered.plot(kind='barh', ax=ax)
ax.set_xlabel('Reads after filtering (billions)')
sns.despine(fig, trim=True)
fig.tight_layout()
fig.savefig('hq_inserts_per_habitat.svg')

smORFs = meta.groupby('general_envo_name').sum()['smORFs']
smORFs = smORFs.reindex(general.index)
smORFs['other'] = meta['smORFs'].sum() - smORFs.sum()

fig, ax = plt.subplots()
(smORFs // 1000_000).plot(kind='barh', ax=ax)
ax.set_xlabel('smORFs (raw, millions)')
sns.despine(fig, trim=True)
fig.tight_layout()
fig.savefig('smORFs_raw_millions.svg')

assembly_total_length = meta.groupby('general_envo_name').sum()['assembly_total_length']
assembly_total_length = assembly_total_length.reindex(general.index)
assembly_total_length['other'] = meta['assembly_total_length'].sum() - assembly_total_length.sum()

meta['is_host_associated'] = meta['general_envo_name'].map(lambda c : is_host_associated[higher_level.get(c, 'other')])
meta['is_host_associated'] = meta.is_host_associated.map(lambda i: 'host' if i else 'non-host')

c_general_envo_name = meta['general_envo_name'].value_counts()
sel = meta[meta.general_envo_name.map(lambda e: c_general_envo_name[e] >= 100)]
sel = sel.query('assembly_total_length > 1_000_000')
sel = sel.query('ampsphere_amps_per_assembly_mbps < 4')
meta.groupby('general_envo_name').median()['ampsphere_amps_per_assembly_mbps'].sort_values().reindex(general.index).drop('other').sort_values()
order = sel.groupby('general_envo_name').median()['ampsphere_amps_per_assembly_mbps'].sort_values().index

sels = []
for h in order:
    cur = sel[sel.general_envo_name == h]
    sels.append(cur.sample(100, replace=True))

sell2000=pd.concat(sels)

fig,ax = plt.subplots()
ax.set_xlim(-1,2)

sns.boxplot(x='is_host_associated',
        y='ampsphere_amps_per_assembly_mbps',
        order=['host', 'non-host'],
        ax=ax,
        showfliers=False,
        data=meta.sample(2000),
        color='white',
        )
sns.swarmplot(x='is_host_associated',
        y='ampsphere_amps_per_assembly_mbps',
        order=['host', 'non-host'],
        ax=ax,
        data=meta.sample(1000),
        s=3,
        )
plt.xlabel('')
plt.ylabel('AMPs per assembled Mbp')
fig.savefig('host_vs_nonhost.svg')

ax.clear()
sns.boxplot(x='general_envo_name',
        y='ampsphere_amps_per_assembly_mbps',
        order=order,
        ax=ax,
        #data=sell.loc[np.random.choice(sell.index, 2000)],
        color='white',
        showfliers=False,
        data=sell2000)
sns.swarmplot(x='general_envo_name',
        y='ampsphere_amps_per_assembly_mbps',
        hue='is_host_associated',
        order=order,
        ax=ax,
        #data=sell.loc[np.random.choice(sell.index, 2000)],
        data=sell2000,
        s=2.0)

for x in ax.get_xticklabels():
    x.set_rotation(90)

ax.set_xlabel('Habitat')
ax.set_ylabel('AMPs per assembled Mbp')
fig.tight_layout()
sns.despine(fig, trim=True)
fig.savefig('ampsphere_amps_per_assembly_mbps.svg')
fig.savefig('ampsphere_amps_per_assembly_mbps.png', dpi=150)

sel = sel.query('higher == "anthropogenic"')
sel.groupby('general_envo_name').mean()['ampsphere_amps_per_assembly_mbps'].sort_values()
meta = meta[~meta.ampsphere_amps_per_assembly_mbps.isna()]

sps = ['human gut', 'cat gut', 'dog gut', 'chicken gut', 'pig gut', 'cattle gut', 'mouse gut', 'rat gut', 'primate gut']
tests = []
for s, sn in permutations(sps, 2):
    u, p = stats.mannwhitneyu(meta[meta.general_envo_name == s]['ampsphere_amps_per_assembly_mbps'],
                              meta[meta.general_envo_name == sn]['ampsphere_amps_per_assembly_mbps'])
    tests.append((s, sn, u, p))

tests = pd.DataFrame(tests, columns=['s1', 's2', 'U', 'pval'])
_, tests['p_adj'], _, _ = multipletests(tests['pval'], method='hs')
tests.to_csv('mannwhitneyu_test_mammalguts.tsv', sep='\t', header=True, index=None)

c = sel.smorfs_per_assembly_mbps.copy()
fig,ax = plt.subplots()
ax.clear()
ax.hist(c, bins=1000)
fig.savefig('smorfs_per_assembly_mbps.svg')
plt.close()

d = sel.ampsphere_amps_per_assembly_mbps.copy()
sns.kdeplot(data=c, label='smORFs')
sns.kdeplot(data=d*1000, label='AMPSphere AMPs * 1000')
plt.xlabel('Per assembly mbps')
plt.ylabel('Density AU')
plt.legend()
plt.savefig('amp_smorfs_sample.svg')

m = meta[['ena_ers_sample_id', 'database', 'access_status', 'study', 'study_accession',
          'general_envo_name', 'higher', 'inserts_filtered', 'assembly_total_length',
          'smORFs', 'ampsphere_amps', 'is_host_associated']]

m.rename({'higher': 'macro_environment',
          'general_envo_name': 'micro_environment'},
         axis=1,
         inplace=True)
          
m.to_csv('table_S2.tsv', sep='\t', header=True, index=True)

