import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import urllib.request
import json
import datetime as dt

plt.style.use('ggplot')

# get default days back
def get_days_back():
    return 91

def get_residents():
    return 10701777

def get_token():
    with open('token.json') as token_file:
        data = json.load(token_file)
        token = data['token']
    return token

# days_back = get_days_back()


def autolabel(rects, ax, val_prec=0):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        if height!=height:height=0
        if val_prec == 0:
            height_str = f'{height:.0f}'
        elif val_prec == 1:
            height_str = f'{height:.1f}'            
        else:
            height_str = f'{height:.2f}'
        ax.annotate(height_str,
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
        
        
def get_epidemic_data(vaxs, days_back):
    # získání základních dat   
    token = get_token()
    
    dfs = []
    for d in range(days_back,0,-1):
        data_date = (dt.date.today() - dt.timedelta(days=d)).strftime("%Y-%m-%d")
        with urllib.request.urlopen(f'https://onemocneni-aktualne.mzcr.cz/api/v3/nakazeni-vyleceni-umrti-testy/{data_date}?apiToken={token}') as url:

            json_data = pd.json_normalize(json.loads(url.read().decode()))
            dfs.append(json_data)
    df = pd.concat(dfs, ignore_index=True)  
    df = df.drop(['@context', '@id', '@type'], axis=1)
    df['datum'] = pd.to_datetime(df['datum'], errors='coerce')
    df['datum'] = df['datum'].dt.date


    # získání dat o incidenci
    data_date = (dt.date.today() - dt.timedelta(days=days_back)).strftime("%Y-%m-%d")

    with urllib.request.urlopen(f'https://onemocneni-aktualne.mzcr.cz/api/v3/incidence-7-14-cr?datum%5Bafter%5D={data_date}&apiToken={token}') as url:
        data = json.loads(url.read().decode())


    df_incidence = pd.json_normalize(data['hydra:member'])
    df_incidence = df_incidence.drop(['@id', '@type', 'id'], axis=1)
    df_incidence['datum'] = pd.to_datetime(df_incidence['datum'], errors='coerce')
    df_incidence['datum'] = df_incidence['datum'].dt.date

    with urllib.request.urlopen(f'https://onemocneni-aktualne.mzcr.cz/api/v3/incidence-7-14-okresy?page=1&datum%5Bafter%5D={data_date}&okres_lau_kod=CZ0100&apiToken={token}') as url:
        data = json.loads(url.read().decode())

    df_incidence_praha = pd.json_normalize(data['hydra:member'])
    df_incidence_praha = df_incidence_praha.drop(['@id', '@type', 'id'], axis=1)
    df_incidence_praha['datum'] = pd.to_datetime(df_incidence_praha['datum'], errors='coerce')
    df_incidence_praha['datum'] = df_incidence_praha['datum'].dt.date
    
    # add daily counts + other params

    df.rename(columns={'datum': 'date', 
                       'kumulativni_pocet_nakazenych': 'positive_total',
                      'kumulativni_pocet_vylecenych': 'recovered_total', 
                      'kumulativni_pocet_umrti': 'deceased_total',
                      'kumulativni_pocet_testu': 'tested_pcr_total',
                      'kumulativni_pocet_ag_testu': 'tested_ag_total',
                      'prirustkovy_pocet_nakazenych': 'positive_daily',
                      'prirustkovy_pocet_vylecenych': 'recovered_daily',
                      'prirustkovy_pocet_umrti': 'deceased_daily',
                      'prirustkovy_pocet_provedenych_testu': 'tested_pcr_daily',
                      'prirustkovy_pocet_provedenych_ag_testu': 'tested_ag_daily',}, inplace=True)

    df['tested_total'] = df['tested_pcr_total'] + df['tested_ag_total']
    df['tested_daily'] = df['tested_pcr_daily'] + df['tested_ag_daily']
    df['positive_ratio'] = df['positive_daily'] / df['tested_daily']
    df['active'] = df['positive_total'] - df['recovered_total'] - df['deceased_total'] 
    
    
    # přidání vaxs do df
    df = pd.merge(df, vaxs, how='left', on='date')
    df = df.fillna(0)
    
    # save data for later use
    df.to_csv('data-' + df.iloc[-1, 0].strftime('%Y-%m-%d') + '.csv', index=False)
    
    return df, df_incidence, df_incidence_praha


def plot_positive_incidence(df, df_incidence, df_incidence_praha, days_back):
    fig = plt.figure(figsize=(22,30))
    ax1 = fig.add_subplot(313)
    ax2 = fig.add_subplot(311)
    ax3 = fig.add_subplot(312)

    df.plot(x='date', 
            y='positive_total', 
            kind='line', 
            style='tomato',
            marker='o',
            linewidth=2,                   
            legend=False,
            grid=True, 
            ax=ax1,
            title=f'Kumulativní počet pozitivně testovaných od zařátku testování - posledních {days_back} dní')

    x = np.arange(days_back)
    x_labels = np.array(df.iloc[-days_back:, df.columns.get_loc('date')])
    y = np.array(df.iloc[-days_back:, df.columns.get_loc('positive_daily')])

    z = np.polyfit(x,y,5)
    p = np.poly1d(z)
    xnew = np.linspace(x[0], x[-1], 1000)

    rects1 = ax2.bar(x, y, width=.5, color='tomato')
    ax2.set_xticks(np.arange(len(x)))
    ax2.set_xticklabels(x_labels, rotation=45)
    autolabel(rects1, ax2)

    ax2.plot(xnew, p(xnew), 'dimgray', linewidth=3)

    ax2.grid(True)
    ax2.set_title(f'Denní počet pozitivně testovaných za posledních {days_back} dní')


    df_incidence["incidence_7_100000"]=df_incidence["incidence_7_100000"].astype(float)
    df_incidence.plot(x='datum', 
                        y='incidence_7_100000', 
                        kind='line', 
                        style='tomato',
                        marker='o',
                        linewidth=2,
                        label='ČR', 
                        legend=True,
                        grid=True, 
                        ax=ax3,
                        title='Incidence - nově nakažení za týden na 100 000 obyvatel - posledních '+str(days_back)+' dní')

    df_incidence_praha["incidence_7_100000"]=df_incidence_praha["incidence_7_100000"].astype(float)
    df_incidence_praha.plot(x='datum', 
                            y='incidence_7_100000', 
                            kind='line', 
                            style='tab:blue',
                            marker='o',
                            linewidth=2,                                                      
                            label='Praha', 
                            legend=True,
                            grid=True, 
                            ax=ax3,
                        )

    plt.show()    

def plot_tests(df, days_back):
    fig = plt.figure(figsize=(22,20))
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)

    df.plot(x='date', 
            y=['tested_pcr_daily','tested_ag_daily'], 
            kind='bar',
            style=['tomato', 'dimgray'],
            linewidth=3,
            stacked=True,
            grid=True, 
            legend=True,
            label=['PCR','antigen'],
            ax=ax1,                        
            title='Denní počet PCR/antigen testovaných')
    ax1.tick_params(axis="x", rotation=45) 

    x = np.arange(days_back)
    x_labels = np.array(df.iloc[-days_back:, df.columns.get_loc('date')])
    y = np.array(100*df['positive_ratio'])

    z = np.polyfit(x,y,5)
    p = np.poly1d(z)
    xnew = np.linspace(x[0], x[-1], 1000)

    rects1 = ax2.bar(x, y, width=.5, color='tomato')
    ax2.set_xticks(np.arange(len(x)))
    ax2.set_xticklabels(x_labels, rotation=45)
    autolabel(rects1, ax2, val_prec=2)

    ax2.plot(xnew, p(xnew), 'dimgray', linewidth=3)

    ax2.grid(True)
    ax2.set_title(f'Denní poměr pozitivních k počtu testovaných - v %, posledních {days_back} dní')
    plt.show()  
    
    
def plot_rd(df, days_back):
    fig = plt.figure(figsize=(22,20))
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)

    x = np.arange(days_back)
    x_labels = np.array(df['date'])
    y = np.array(df['recovered_daily'])

    z = np.polyfit(x,y,5)
    p = np.poly1d(z)
    xnew = np.linspace(x[0], x[-1], 1000)

    rects1 = ax1.bar(x, y, width=.5, color='tab:green')
    ax1.set_xticks(np.arange(len(x)))
    ax1.set_xticklabels(x_labels, rotation=45)
    autolabel(rects1, ax1)

    ax1.plot(xnew, p(xnew), 'tab:blue', linewidth=3)
    ax1.set_title(f'Denní počet uzdravených za posledních {days_back} dní')
    plt.subplots_adjust(hspace=0.3)


    x = np.arange(days_back)
    y = np.array(df['deceased_daily'])

    z = np.polyfit(x,y,5)
    p = np.poly1d(z)
    xnew = np.linspace(x[0], x[-1], 1000)

    rects2 = ax2.bar(x, y, width=.5, color='tomato')
    ax2.set_xticks(np.arange(len(x)))
    ax2.set_xticklabels(x_labels, rotation=45)
    autolabel(rects2, ax2)

    ax2.plot(xnew, p(xnew), 'dimgray', linewidth=3)
    ax2.set_title(f'Denní počet úmrtí za posledních {days_back} dní')

    plt.show()    

    
    
def get_vax_data():
    # získání dataframu s počtem lidí s aktivním očkováním po dnech

    url ='https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani-demografie.csv'
    dfv = pd.read_csv(url)
    dfv['datum'] = pd.to_datetime(dfv['datum'], errors='coerce')
    dfv['datum'] = dfv['datum'].dt.date

    # všechno kromě Johnsona

    vax01 = dfv[( (dfv['vakcina_kod']=='CO01') |  ### vyfiltrovani jen vakcin a davek ktere nas zajimaji
        (dfv['vakcina_kod']=='CO02') |
        (dfv['vakcina_kod']=='CO03') |
        (dfv['vakcina_kod']=='CO04') |            
        (dfv['vakcina_kod']=='CO06')) & 
        (dfv['poradi_davky']==2)]

    vax01 = vax01.drop(['id', 'vakcina',  ### odstraneni prebytecnych sloupcu
                        'vakcina_kod', 'vekova_skupina', 
                        'poradi_davky', 'pohlavi'], axis=1) 
    vax01 = vax01.groupby(['datum']).sum()  ### secteni po datumech
    vax01 = vax01.rolling(min_periods=1, window=182).sum()  ### soucet poslednich 182 dni
    vax01 = vax01.reset_index()
    vax01.rename(columns={'datum': 'date', 
                       'pocet_davek': 'vax_active',}, inplace=True)

    # Johnson
    vax02 = dfv[(dfv['vakcina_kod']=='CO04')]  ### vyfiltrovani jen vakcin a davek ktere nas zajimaji

    vax02 = vax02.drop(['id', 'vakcina',  ### odstraneni prebytecnych sloupcu
                        'vakcina_kod', 'vekova_skupina', 
                        'poradi_davky', 'pohlavi'], axis=1) 
    vax02 = vax02.groupby(['datum']).sum()  ### secteni po datumech
    vax02 = vax02.rolling(min_periods=1, window=61).sum()  ### soucet poslednich 61 dni
    vax02 = vax02.reset_index()
    vax02.rename(columns={'datum': 'date', 
                       'pocet_davek': 'vax_active',}, inplace=True)

    # Booster
    boost = dfv[dfv['poradi_davky']==3]  ### vyfiltrovani jen vakcin a davek ktere nas zajimaji

    boost = boost.drop(['id', 'vakcina',  ### odstraneni prebytecnych sloupcu
                        'vakcina_kod', 'vekova_skupina', 
                        'poradi_davky', 'pohlavi'], axis=1) 
    boost = boost.groupby(['datum']).sum()  ### secteni po datumech
    boost = boost.rolling(min_periods=1, window=122).sum()  ### soucet poslednich 91 dni (nebo 4 měsíce=122 dní)
    boost = boost.reset_index()
    boost.rename(columns={'datum': 'date', 
                       'pocet_davek': 'vax_active',}, inplace=True)

    # sloučení všech tří dataframe do jednoho 
    vaxs = pd.merge(vax01, vax02, how='outer', on='date')
    vaxs = pd.merge(vaxs, boost, how='outer', on='date')
    vaxs = vaxs.fillna(0)
    vaxs['vaxs_active'] = vaxs['vax_active_x'] + vaxs['vax_active_y'] + vaxs['vax_active']
    vaxs = vaxs.drop(['vax_active_x', 'vax_active_y', 'vax_active', ], axis=1) 
    
    residents = get_residents()
    vaxs['vaxs_active_prcs'] = vaxs['vaxs_active'] / residents

    return vaxs

def plot_vax_data(vaxs, days_back):
    # graf vývoje aktivního očkování
    fig = plt.figure(figsize=(22,20))
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)    
    
    ax1.ticklabel_format(useOffset=False, style='plain', axis='y')
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    vaxs.plot(x='date', 
            y='vaxs_active_prcs', 
            kind='line', 
            style='tomato',
            marker='o',
            linewidth=2,                   
            legend=False,
            grid=True, 
            ax=ax1,  
            title=f'Denní procentní poměr aktivně očkovaných od počátku očkování.');

    
    ax2.ticklabel_format(useOffset=False, style='plain', axis='y')
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    vaxs[-days_back:].plot(x='date', 
            y='vaxs_active_prcs', 
            kind='line', 
            style='tomato',
            marker='o',
            linewidth=2,                   
            legend=False,
            grid=True, 
            ax=ax2,  
            title=f'Denní procentní poměr aktivně očkovaných za posledních {days_back} dní.');
    
    #x = np.arange(days_back)
    #x_labels = np.array(vaxs.iloc[-days_back:, vaxs.columns.get_loc('date')])
    #y = np.array(vaxs.iloc[-days_back:, vaxs.columns.get_loc('vaxs_active_prcs')])

    #z = np.polyfit(x,y,5)
    #p = np.poly1d(z)
    #xnew = np.linspace(x[0], x[-1], 1000)

    #rects1 = ax2.bar(x, y, width=.5, color='tomato')
    #ax2.set_xticks(np.arange(len(x)))
    #ax2.set_xticklabels(x_labels, rotation=45)
    #autolabel(rects1, ax2, val_prec=2)

    #ax2.plot(xnew, p(xnew), 'dimgray', linewidth=3)

    #ax2.grid(True)
    #ax2.set_title(f'Denní procentní poměr aktivně očkovaných za posledních {days_back} dní')

    
    
def get_epidemic_vax_data(vaxs, days_back):

    residents = get_residents()
    
    # data o úmrtí, jip, poztivitě podle očkování
    token = get_token()
    data_date = (dt.date.today() - dt.timedelta(days=days_back)).strftime("%Y-%m-%d")

    with urllib.request.urlopen(f'https://onemocneni-aktualne.mzcr.cz/api/v3/ockovani-umrti?page=1&datum%5Bafter%5D={data_date}&apiToken={token}') as url:
        data = json.loads(url.read().decode())


    df_ocko_umrti = pd.json_normalize(data['hydra:member'])
    df_ocko_umrti = df_ocko_umrti.drop(['@id', '@type', 'id'], axis=1)
    df_ocko_umrti['datum'] = pd.to_datetime(df_ocko_umrti['datum'], errors='coerce')
    df_ocko_umrti['datum'] = df_ocko_umrti['datum'].dt.date
    df_ocko_umrti.rename(columns={'datum': 'date'}, inplace=True)
    df_ocko_umrti = pd.merge(df_ocko_umrti, vaxs, how='left', on='date')
    df_ocko_umrti = df_ocko_umrti.fillna(0)


    df_ocko_umrti['zemreli_bez_ockovani_relative'] = 1e6 * (df_ocko_umrti['zemreli_bez_ockovani'] + \
                                                            df_ocko_umrti['zemreli_nedokoncene_ockovani']) / \
                                                        (residents-df_ocko_umrti['vaxs_active'])
    df_ocko_umrti['zemreli_ockovani_relative'] = 1e6 * (df_ocko_umrti['zemreli_dokoncene_ockovani'] + \
                                                    df_ocko_umrti['zemreli_posilujici_davka'])/ df_ocko_umrti['vaxs_active']
    
    with urllib.request.urlopen(f'https://onemocneni-aktualne.mzcr.cz/api/v3/ockovani-jip?page=1&datum%5Bafter%5D={data_date}&apiToken={token}') as url:
        data = json.loads(url.read().decode())


    df_ocko_jip = pd.json_normalize(data['hydra:member'])
    df_ocko_jip = df_ocko_jip.drop(['@id', '@type', 'id'], axis=1)
    df_ocko_jip['datum'] = pd.to_datetime(df_ocko_jip['datum'], errors='coerce')
    df_ocko_jip['datum'] = df_ocko_jip['datum'].dt.date
    df_ocko_jip.rename(columns={'datum': 'date'}, inplace=True)
    df_ocko_jip = pd.merge(df_ocko_jip, vaxs, how='left', on='date')
    df_ocko_jip = df_ocko_jip.fillna(0)
    df_ocko_jip['jip_bez_ockovani_relative'] = 1e6 * (df_ocko_jip['jip_bez_ockovani'] + \
                                                    df_ocko_jip['jip_nedokoncene_ockovani']) / \
                                                        (residents-df_ocko_jip['vaxs_active'])
    df_ocko_jip['jip_ockovani_relative'] = 1e6 * (df_ocko_jip['jip_dokoncene_ockovani'] + \
                                                    df_ocko_jip['jip_posilujici_davka'])/ df_ocko_jip['vaxs_active']


    with urllib.request.urlopen(f'https://onemocneni-aktualne.mzcr.cz/api/v3/ockovani-pozitivni?page=1&datum%5Bafter%5D={data_date}&apiToken={token}') as url:
        data = json.loads(url.read().decode())


    df_ocko_positive = pd.json_normalize(data['hydra:member'])
    df_ocko_positive = df_ocko_positive.drop(['@id', '@type', 'id'], axis=1)
    df_ocko_positive['datum'] = pd.to_datetime(df_ocko_positive['datum'], errors='coerce')
    df_ocko_positive['datum'] = df_ocko_positive['datum'].dt.date
    df_ocko_positive.rename(columns={'datum': 'date'}, inplace=True)
    df_ocko_positive = pd.merge(df_ocko_positive, vaxs, how='left', on='date')
    df_ocko_positive = df_ocko_positive.fillna(0)
    df_ocko_positive['pozitivni_bez_ockovani_relative'] = 1e5 * (df_ocko_positive['pozitivni_bez_ockovani'] + \
                                                    df_ocko_positive['pozitivni_nedokoncene_ockovani']) / \
                                                        (residents-df_ocko_positive['vaxs_active'])
    df_ocko_positive['pozitivni_ockovani_relative'] = 1e5 * (df_ocko_positive['pozitivni_dokoncene_ockovani'] + \
                                                    df_ocko_positive['pozitivni_posilujici_davka'])/ df_ocko_positive['vaxs_active']
    
    return df_ocko_umrti, df_ocko_jip, df_ocko_positive



def plot_djp_vax(df_ocko_umrti, df_ocko_jip, df_ocko_positive, days_back):
    fig = plt.figure(figsize=(22,30))
    ax1 = fig.add_subplot(311)
    ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(313)

    df_ocko_umrti.plot(x='date', 
            y=['zemreli_bez_ockovani_relative','zemreli_ockovani_relative'], 
            kind='bar',
            color=['gray', 'tomato'],
            linewidth=3,
            stacked=True,
            grid=True, 
            legend=True,
            label=['neočkovaní','aktivní očkování'],
            ax=ax1,                        
            title=f'Denní počet zemřelých na 1 milión obyvatel podle stavu očkování za posledních {days_back} dní')
    ax1.tick_params(axis="x", rotation=45)

    df_ocko_jip.plot(x='date', 
            y=['jip_bez_ockovani_relative','jip_ockovani_relative'], 
            kind='bar',
            color=['gray', 'tomato'],
            linewidth=3,
            stacked=True,
            grid=True, 
            legend=True,
            label=['neočkovaní','aktivní očkování'],
            ax=ax2,
            title=f'Denní přírůstek na JIP na 1 milión obyvatel podle stavu očkování za posledních {days_back} dní')
    ax2.tick_params(axis="x", rotation=45)

    df_ocko_positive.plot(x='date', 
            y=['pozitivni_bez_ockovani_relative','pozitivni_ockovani_relative'], 
            kind='bar',
            color=['gray', 'tomato'],
            linewidth=3,
            stacked=True,
            grid=True, 
            legend=True,
            label=['neočkovaní','aktivně očkování'],
            ax=ax3,
            title=f'Denní přírůstek pozitivních na 100 tisíc obyvatel podle stavu očkování za posledních {days_back} dní')
    ax3.tick_params(axis="x", rotation=45)  
    
    
def plot_djp_vax_ratio(df_ocko_umrti, df_ocko_jip, df_ocko_positive, days_back):
    # kolikrát víc neočkovaných než očkovaných 
    df_ocko_umrti['neocko_ocko_pomer'] = df_ocko_umrti['zemreli_bez_ockovani_relative'] / df_ocko_umrti['zemreli_ockovani_relative']
    df_ocko_umrti['neocko_ocko_pomer_7']=df_ocko_umrti['neocko_ocko_pomer'].rolling(window=7).sum()/7
    
    df_ocko_jip['neocko_ocko_pomer'] = df_ocko_jip['jip_bez_ockovani_relative'] / df_ocko_jip['jip_ockovani_relative']
    df_ocko_jip['neocko_ocko_pomer_7']=df_ocko_jip['neocko_ocko_pomer'].rolling(window=7).sum()/7
    
    df_ocko_positive['neocko_ocko_pomer'] = df_ocko_positive['pozitivni_bez_ockovani_relative'] / df_ocko_positive['pozitivni_ockovani_relative']
    df_ocko_positive['neocko_ocko_pomer_7']=df_ocko_positive['neocko_ocko_pomer'].rolling(window=7).sum()/7

    
    def plot_djp_subplot(dff, axx, title, colour):
        axx.bar(dff[-days_back:]['date'], dff[-days_back:]['neocko_ocko_pomer'], 
                color=colour, #'dimgray', 
                label='poměr neočko/očko',)
        axx.plot(dff[-days_back:]['date'], dff[-days_back:]['neocko_ocko_pomer_7'], 
                 color='black', 
                 linewidth=2, 
                 marker='o', 
                 label='7denní průměr')
        axx.ticklabel_format(useOffset=False, style='plain', axis='y')
        axx.set_title(title) #f'Denní poměr neočkovaných / aktivně očkovaných zemřelých za posledních {days_back} dní')
        axx.legend(fontsize=14)
        axx.tick_params(axis="x", rotation=45)
        
    
    fig = plt.figure(figsize=(22,30))
    ax1 = fig.add_subplot(311)
    ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(313)

    #df_ocko_umrti.plot(x='date', 
    #        y=['neocko_ocko_pomer'], 
    #        kind='bar',
    #        color=['black'],
    #        linewidth=3,
    #        stacked=True,
    #        grid=True, 
    #        legend=False,
    #        ax=ax1,
    #        title=f'Denní poměr neočkovaných / aktivně očkovaných zemřelých za posledních {days_back} dní')
    #ax1.tick_params(axis="x", rotation=45)
    
    #ax1.bar(df_ocko_umrti[-days_back:]['date'], df_ocko_umrti[-days_back:]['neocko_ocko_pomer'], 
    #        color='dimgray', 
    #        label='poměr neočko/očko',)
    #ax1.plot(df_ocko_umrti[-days_back:]['date'], df_ocko_umrti[-days_back:]['neocko_ocko_pomer_7'], 
    #         color='black', 
    #         linewidth=2, 
    #         marker='o', 
    #         label='7denní průměr')
    #ax1.ticklabel_format(useOffset=False, style='plain', axis='y')
    #ax1.set_title(f'Denní poměr neočkovaných / aktivně očkovaných zemřelých za posledních {days_back} dní')
    #ax1.legend(fontsize=14)
    #ax1.tick_params(axis="x", rotation=45)
    
    plot_djp_subplot(df_ocko_umrti, 
                     ax1, 
                     f'Denní poměr neočkovaných / aktivně očkovaných zemřelých za posledních {days_back} dní', 
                     'dimgray')

    #df_ocko_jip.plot(x='date', 
    #        y=['neocko_ocko_pomer'], 
    #        kind='bar',
    #        color=['tomato'],
    #        linewidth=3,
    #        stacked=True,
    #        grid=True, 
    #        legend=False,
    #        ax=ax2,
    #        title=f'Denní poměr neočkovaných / aktivně očkovaných na JIP za posledních {days_back} dní')
    #ax2.tick_params(axis="x", rotation=45)
    
    #ax2.bar(df_ocko_jip[-days_back:]['date'], df_ocko_jip[-days_back:]['neocko_ocko_pomer'], 
    #        color='tomato', 
    #        label='poměr neočko/očko',)
    #ax2.plot(df_ocko_jip[-days_back:]['date'], df_ocko_jip[-days_back:]['neocko_ocko_pomer_7'], 
    #         color='dimgray', 
    #         linewidth=2, 
    #         marker='o', 
    #         label='7denní průměr')
    #ax2.ticklabel_format(useOffset=False, style='plain', axis='y')
    #ax2.set_title(f'Denní poměr neočkovaných / aktivně očkovaných na JIP za posledních {days_back} dní')
    #ax2.legend(fontsize=14)
    #ax2.tick_params(axis="x", rotation=45)
    
    plot_djp_subplot(df_ocko_jip, 
                     ax2, 
                     f'Denní poměr neočkovaných / aktivně očkovaných na JIP za posledních {days_back} dní', 
                     'tomato')

    #df_ocko_positive.plot(x='date', 
    #        y=['neocko_ocko_pomer'], 
    #        kind='bar',
    #        color=['royalblue'],
    #        linewidth=3,
    #        stacked=True,
    #        grid=True, 
    #        legend=False,
    #        ax=ax3,
    #        title=f'Denní poměr neočkovaných / aktivně očkovaných pozitivně testovaných za posledních {days_back} dní')
    #ax3.tick_params(axis="x", rotation=45)
    
    plot_djp_subplot(df_ocko_positive, 
                     ax3, 
                     f'Denní poměr neočkovaných / aktivně očkovaných pozitivně testovaných za posledních {days_back} dní', 
                     'royalblue')
    
    
def get_reinfection_data(days_back):
    url ='https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/nakazeni-reinfekce.csv'
    dfr = pd.read_csv(url)
    dfr['datum'] = pd.to_datetime(dfr['datum'], errors='coerce')
    dfr['datum'] = dfr['datum'].dt.date
    dfr = dfr.fillna(0)
    dfr.rename(columns={'datum': 'date',}, inplace=True)
    dfr['reinfekce_7']=dfr['nove_reinfekce'].rolling(min_periods=1, window=7).sum()/7
    
    return dfr


def plot_reinfection(dfr, days_back):
    #plt.style.use('ggplot')
    #fig = plt.figure(figsize=(22,10))
    #ax1 = fig.add_subplot(111)
    #ax1.ticklabel_format(useOffset=False, style='plain', axis='y')
    #dfr[-days_back:].plot(x='date', y='nove_reinfekce',
    #        kind='bar', 
    #            style='tab:green',
    #            #marker='o',
    #            linewidth=2,                   
    #            legend=False,
    #            grid=True, 
    #            ax=ax1,
    #            title=f'Počet reinfekcí za posledních {days_back} dní')
    
    plt.style.use('ggplot')
    fig = plt.figure(figsize=(22,10))
    ax1 = fig.add_subplot(111)

    ax1.bar(dfr[-days_back:]['date'], dfr[-days_back:]['nove_reinfekce'], 
            color='tab:blue', 
            label='nové reinfekce',)
    ax1.plot(dfr[-days_back:]['date'], dfr[-days_back:]['reinfekce_7'], 
             color='black', 
             linewidth=2, 
             marker='o', 
             label='7denní průměr')
    ax1.ticklabel_format(useOffset=False, style='plain', axis='y')
    ax1.set_title(f'Počet reinfekcí za posledních {days_back} dní')
    ax1.legend(fontsize=14)
    ax1.tick_params(axis="x", rotation=45)