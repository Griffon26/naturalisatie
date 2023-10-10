from datetime import date, datetime, timedelta
import json
import requests
import sys
import time


class RequestError(Exception):
    pass


def send_request(session, req):
    base_url = \
        'https://online3.jccsoftware.nl/JCC/Afspraakgeleiding%20Productie/JCC-Afspraakgeleiding/Api/api'
    full_url = f'{base_url}{req["url"]}'
    try:
        if req['method'] == 'POST':
            response = session.post(full_url, req.get('data', {}), headers=req.get('headers', {}))
        elif req['method'] == 'GET':
            response = session.get(full_url, params=req.get('params', {}))
        else:
            raise RequestError(f'Invalid method type specified')
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response.text
    except requests.exceptions.RequestException as e:
        raise RequestError(f'Request to {req["url"]} failed:\n{e}')


def count_available_times():
    with requests.Session() as session:
        session.headers.update({
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8,es;q=0.7',
            'Content-Length':'0',
            'Dnt':'1',
            'Id':'651a9a86-0f44-43ec-a626-3bdb11d31118',
            'Language':'nl',
            'Origin':'https://eindhoven.mijnafspraakmaken.nl',
            'Referer':'https://eindhoven.mijnafspraakmaken.nl/',
            'Sec-Ch-Ua':'"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'Sec-Ch-Ua-Mobile':'?0',
            'Sec-Ch-Ua-Platform':'"Windows"',
            'Sec-Fetch-Dest':'empty',
            'Sec-Fetch-Mode':'cors',
            'Sec-Fetch-Site':'cross-site',
            'Token':'e171c5c5-03cd-4deb-be00-d3f8241e234f',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'})

        #print('Perform "login" request:')
        response_content = send_request(session, {
            'method': 'POST',
            'url': '/warp/login'
        })
        #print(response_content)

        #print('Perform "listforappointment" request:')
        response_content = send_request(session, {
            'method': 'GET',
            'url': '/proxy/warp/activity/listforappointment'
        })
        obj = json.loads(response_content)
        selected_entries = [entry for entry in obj['data'] if entry['description'] == 'Nederlander worden - Naturalisatie']
        #print(json.dumps(selected_entries, indent=2))
        assert len(selected_entries) == 1
        activityId = selected_entries[0]['id']

        #print('Perform "location/forappointment" request:')
        response_content = send_request(session, {
            'method': 'GET',
            'url': '/proxy/warp/location/forappointment',
            'params': {
                'selectedActivityId': f'{activityId}'
            }
        })
        obj = json.loads(response_content)
        #print(json.dumps(obj, indent=2))
        assert len(obj['data']) == 1
        locationId = obj['data'][0]['id']

        startdate = date.today() + timedelta(days=28 * 3)
        enddate = startdate + timedelta(days=31)

        #print(f'Perform "availabletimelist" request from {startdate} to {enddate}:')
        response_content = send_request(session, {
            'method': 'GET',
            'url': '/proxy/warp/appointment/availabletimelist',
            'params': {
                'fromDate': f'{startdate}',
                'toDate': f'{enddate}',
                'activityId': f'{activityId}',
                'amount': '1',
                'locationId': f'{locationId}',
                'currentAppointmentId': 'null'
            }
        })
        obj = json.loads(response_content)
        #print(json.dumps(obj, indent=2))

        return obj['data']['availableTimesList']


def timestamp():
    return f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'


def main():
    available_times = count_available_times()
    while not available_times:
        print(f'{timestamp()} - No available times. Waiting a while...', flush=True)
        time.sleep(15 * 60)
        available_times = count_available_times()

    print(f'{timestamp()} - Available times: {available_times}', flush=True)


if __name__ == "__main__":
    main()
