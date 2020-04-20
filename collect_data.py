import pandas as pd
import urllib.request
import json
from datetime import date


def main():

    with urllib.request.urlopen("https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19/osoby.json") as url:
        positiveTests_json = json.loads(url.read().decode())
        positiveTests = pd.DataFrame(positiveTests_json)
        positiveTests['DatumHlaseni'] = pd.to_datetime(positiveTests['DatumHlaseni'], errors='coerce')    
        #positiveTests.to_csv('/home/pi/covid/persons-'+str(max(positiveTests['DatumHlaseni'].dt.date))+'.csv', index=False)    
        positiveTests.to_csv('persons-'+str(max(positiveTests['DatumHlaseni'].dt.date))+'.csv', index=False)    


    with urllib.request.urlopen("https://api.apify.com/v2/key-value-stores/K373S4uCFR9W1K8ei/records/LATEST?disableRedirect=true") as url:
        data = json.loads(url.read().decode())

        
    totalPositiveTests = pd.DataFrame(data['totalPositiveTests'])
    totalPositiveTests['date'] = pd.to_datetime(totalPositiveTests['date'], errors='coerce')
    totalPositiveTests['date'] = totalPositiveTests['date'].dt.date
    #totalPositiveTests.to_csv('/home/pi/covid/total_positive_tests.csv', index=False)
    totalPositiveTests.to_csv('total_positive_tests.csv', index=False)
    
    numberOfTested = pd.DataFrame(data['numberOfTestedGraph'])
    numberOfTested['date'] = pd.to_datetime(numberOfTested['date'], errors='coerce')
    numberOfTested['date'] = numberOfTested['date'].dt.date
    #numberOfTested.to_csv('/home/pi/covid/number_of_tested.csv', index=False)
    numberOfTested.to_csv('number_of_tested.csv', index=False)
    
    infectedByRegion = pd.DataFrame(data['infectedByRegion'])
    infectedByRegion.set_index('name', inplace = True)
    #infectedByRegion.to_csv('/home/pi/covid/infected_by_region.csv', index=True)
    infectedByRegion.to_csv('infected_by_region.csv', index=True)
    
    infectedDaily = pd.DataFrame(data['infectedDaily'])  
    infectedDaily['date'] = pd.to_datetime(infectedDaily['date'], errors='coerce')
    infectedDaily['date'] = infectedDaily['date'].dt.date
    #infectedDaily.to_csv('/home/pi/covid/infected_daily.csv', index=False)
    infectedDaily.to_csv('infected_daily.csv', index=False)
    
    #daily_data = pd.read_csv('/home/pi/covid/daily_data.csv')
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
    #daily_data.to_csv('/home/pi/covid/daily_data.csv', index=False)
    daily_data.to_csv('daily_data.csv', index=False)



if __name__ == "__main__":
    main()
