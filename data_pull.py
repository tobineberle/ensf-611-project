import pandas as pd
import requests as rq
import json
import regex as re
import datetime
from shapely.geometry import shape, Point

def main():
    date = '2021-01-01'
    lat = '51.436240'
    long = '-116.219068'
    area = 'Kootenay-Boundary'

    api = APIRequest(date, area, lat, long)

    df = pd.DataFrame(columns=['Date', 'btl_rating', 'tln_rating', 'alp_rating', 'problem1', 'problem2', 'problem3', 'chance1', 'chance2', 'chance3'])

    for single_date in dateRange(datetime.date(2020, 1, 1), datetime.date(2020, 2, 1)):
        api.date = single_date
        data = api.parseRequest()
        df = pd.concat()

def dateRange(start_date: datetime.date , end_date: datetime.date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + datetime.timedelta(n)

# API Defintions
class APIRequest():
    flexibility_switch_date = datetime.date.fromisoformat('2022-11-01')

    def __init__(self, date, area, lat, long):
        self.date = datetime.date.fromisoformat(date)
        self.area = area
        self.point = Point(long, lat)

    def parseRequest(self):
        '''  
        Note df for avalanche data will be:
        date, below_treeline_rating, treeline_rating, alpine_rating,
        avy_problem_1, avy_problem_2, avy_problem_3,
        avy_problem_1_chance, avy_problem_2_chance, avy_problem_3_chance 
        '''
        data =[self.date]
        if self.date < self.flexibility_switch_date:
            json = self.inflexibleRequest()
            for i in range(len(json)):
                if json[i]['area']['name'] == self.area:
                    break
            json = json[i]
               
        else:
            json = self.flexibleRequest()
        #Add ratings
        data.append(json['report']['dangerRatings'][0]['ratings']['btl']['rating']['value'])
        data.append(json['report']['dangerRatings'][0]['ratings']['tln']['rating']['value'])
        data.append(json['report']['dangerRatings'][0]['ratings']['alp']['rating']['value'])
        #Add problems
        for i in range(3):
            try:
                data.append(json['report']['problems'][i]['type']['value'])
            except:
                data.append(pd.NA)
        #Add chances
        for i in range(3):
            try:
                data.append(json['report']['problems'][i]['factors'][2]['graphic']['alt'].split()[-1])
            except:
                data.append(pd.NA)
            
        print(data)
        return data

    def inflexibleRequest(self):
        url = "http://api.avalanche.ca/forecasts/en/archive/" + str(self.date) + "T08:00:00.000Z"
        print('LOG: Getting inflexible zone request for ', self.date, ' from ', url)
        payload = {}
        headers = {}
        try:
            response = rq.request("GET", url, headers= headers, data= payload)
        
        except Exception as exp:
            print('ERROR: Exception occured in api.inflexibleRequest().')
            print(exp)
            return
        
        response_text = response.text
        response.close()
        return json.loads(response_text)
    

    def flexibleRequest(self):
        #Get area and meta data
        area_url = 'https://api.avalanche.ca/forecasts/en/areas?date=' + str(self.date) +'T08:00:00.000Z'
        print('LOG: Getting flexible area request for ', str(self.date), ' from ', area_url)
        try:
            area_payload = {}
            area_headers = {}
            area_response = rq.request("GET", area_url, headers= area_headers, data= area_payload)

        except Exception as exp:
            print('ERROR: Exception occured in api.flexibleRequest()/area.')
            print(exp)
            return


        metadata_url = 'https://api.avalanche.ca/forecasts/en/metadata?date=' + str(self.date) +'T08:00:00.000Z'
        print('LOG: Getting flexible metadata request for ', str(self.date), ' from ', metadata_url)

        try:
            meta_payload = {}
            meta_headers = {}
            meta_response = rq.request("GET", metadata_url, headers= meta_headers, data= meta_payload)
    
        except Exception as exp:
            print('ERROR: Exception occured in api.flexibleRequest()/meta.')
            print(exp)
            return  

        
        #Link meta data to an area using shapely
        #Need to link geojson (area) data -> metadata (area id) -> product data (product id)
        area_shapes = json.loads(area_response.text)
        area_response.close()

        for feature in area_shapes['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(self.point):
                id = feature['id']
                meta_json = json.loads(meta_response.text)
                for area in meta_json:
                    if area['area']['id'] == id:
                        id_url = "https://api.avalanche.ca/forecasts/en/products/"+ str(area['product']['id'])
                        print('LOG: Getting flexible id request for ', str(self.date), ' from ', metadata_url)
                        try:
                            id_payload = {}
                            id_headers = {}
                            id_response = rq.request("GET", id_url, headers= id_headers, data= id_payload)
                    
                        except Exception as exp:
                            print('ERROR: Exception occured in api.flexibleRequest()/id.')
                            print(exp)
                            return None
                        id_json = json.loads(id_response.text)
                        meta_response.close()
                        id_response.close()
                        
                        print('SUCCESS: Returned product id for:', str(self.date), ' from ', id_url )
                        return id_json
        
        meta_response.close()
        id_response.close()

        print('ERROR: Exception occured in api.flexibleRequest().')
        return None

main()