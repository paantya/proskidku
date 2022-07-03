import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from utils import load


def ger_plot_st(file='log_upd.json'):
    log_upd = load(file=file)

    upd_dict = {k: (v['add'] if 'add' in v.keys() else 0, v['del'] if 'del' in v.keys() else 0) for k, v in log_upd.items()}

    list_seaborn = []
    for k in sorted(upd_dict.keys()):
        if upd_dict[k][0] != 0:
            list_seaborn.append([float(k), int(upd_dict[k][0]), 1])
        if upd_dict[k][1] != 0:
            list_seaborn.append([float(k), int(upd_dict[k][1]), -1])

    dframe = pd.DataFrame(np.array(list_seaborn), columns=['date', 'count', 'product_flag'])

    dframe['product'] = dframe['product_flag'].astype(int).map({1: 'add', -1: 'del'})

    dframe['datetimes'] = pd.to_datetime(dframe['date'], unit='s').dt.tz_localize(tz=pytz.timezone('UTC')).dt.tz_convert(
        tz=pytz.timezone('Europe/Moscow'))

    dframe['weekday'] = dframe['datetimes'].dt.day_name()
    dframe['weekdayn'] = dframe['datetimes'].dt.weekday
    dframe.loc[dframe['product'] == 'add', ('weekdayn')] = dframe[dframe['product'] == 'add']['weekdayn'] + 7
    dframe['weekofyear'] = dframe['datetimes'].dt.weekofyear
    dframe['hours'] = dframe['datetimes'].dt.hour

    fig, axes = plt.subplots(3, 1, figsize=(10, 12))

    fig.suptitle('Statistics for adding and removing items')
    stat = 'percent'  # percent density
    multiple = 'dodge'
    g = sns.histplot(data=dframe,
                     x='hours',
                     weights='count',
                     hue="product",
                     multiple=multiple,
                     shrink=1.7,
                     bins=48,
                     stat=stat,
                     kde=True,
                     ax=axes[0],
                     )

    stat = 'percent'
    sns.histplot(data=dframe,
                     x='weekday',
                     weights='count',
                     hue="product",
                     multiple="dodge",
                     shrink=.9,
                     stat=stat,
                     kde=True,
                     ax=axes[1],
                     )
    plt.xticks(rotation=45);

    stat = 'percent'
    sns.histplot(data=dframe,
                     x='weekofyear',
                     y='weekdayn',
                     weights='count',
                     hue="product",
                     bins=[dframe['weekofyear'].unique().shape[0], 14],
                     stat=stat,
                     cbar=True, cbar_kws=dict(shrink=.9),
                     ax=axes[2],
                     )
    plt.xticks(rotation=45);
    plt.savefig('Statistics.png')