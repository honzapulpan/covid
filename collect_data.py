import pandas as pd
import urllib.request
import json
from datetime import date


def main():
    with urllib.request.urlopen("https://api.apify.com/v2/key-value-stores/K373S4uCFR9W1K8ei/records/LATEST?disableRedirect=true") as url:
        data = json.loads(url.read().decode())

    daily_data = pd.read_csv('daily_data.csv')

    today = date.today()
    fi = daily_data.index[daily_data['date'] == str(today)]

    if len(fi.tolist()):
        daily_data.loc[fi, 
               ['totalTested',
                'tested',
                'totalInfected',
                'infected',
                'totalRecovered',
                'recovered',
                'totalDeceased',
                'deceased']] = data['totalTested'],\
                               data['totalTested'] - daily_data['totalTested'].loc[fi-1],\
                               data['infected'],\
                               data['infected'] - daily_data['totalInfected'].loc[fi-1],\
                               data['recovered'],\
                               data['recovered'] - daily_data['totalRecovered'].loc[fi-1],\
                               data['deceased'],\
                               data['deceased'] - daily_data['totalDeceased'].loc[fi-1]
    else:
        daily_data = daily_data.append({'date': today,
                                        'totalTested': data['totalTested'],
                                        'tested': data['totalTested'] - daily_data['totalTested'].iloc[-1],
                                        'totalInfected': data['infected'],
                                        'infected': data['infected'] - daily_data['totalInfected'].iloc[-1],                                    
                                        'totalRecovered': data['recovered'],
                                        'recovered': data['recovered'] - daily_data['totalRecovered'].iloc[-1],
                                        'totalDeceased': data['deceased'],
                                        'deceased': data['deceased'] - daily_data['totalDeceased'].iloc[-1]},
                                        ignore_index=True)                                                                                          
    daily_data.to_csv('daily_data.csv', index=False)



if __name__ == "__main__":
    main()