import pandas as pd
import urllib.request
import json
from datetime import date


def main():
    with urllib.request.urlopen("https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19/testy.json") as url:
        numberOfTested_json = json.loads(url.read().decode())
        numberOfTested = pd.DataFrame(numberOfTested_json['data'])
        numberOfTested['datum'] = pd.to_datetime(numberOfTested['datum'], errors='coerce')    
        numberOfTested.to_csv('/home/pi/covid/tested-'+numberOfTested_json['data'][-1]['datum']+'.csv', index=False)

    with urllib.request.urlopen("https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19/nakaza.json") as url:
        totalPositiveTests_json = json.loads(url.read().decode())
        totalPositiveTests = pd.DataFrame(totalPositiveTests_json)
        totalPositiveTests['datum'] = pd.to_datetime(totalPositiveTests['datum'], errors='coerce')    
        totalPositiveTests.to_csv('/home/pi/covid/positive-'+totalPositiveTests_json[-1]['datum']+'.csv', index=False)    


if __name__ == "__main__":
    main()