from moysklad.api import MoySklad
from moysklad.queries import Expand, Filter, Ordering, Select, Search, Query
# import moysklad.exceptions import *
import googlemaps
from googlemaps.exceptions import *
import json
import datetime


def find_delivery_time_attribute(customerorder):
    attributes = customerorder.get('attributes')
    if attributes is None:
        return None
    for attr in attributes:
        if attr.get('name') == "Время доставки":
            return attr.get("value")
    return None


def create_point_feature(feature_id, lat, lon, point_name, desc, color):
    return {
        'type': "Feature",
        'id': feature_id,
        'geometry': {
            'type': "Point",
            'coordinates': [lon, lat]
        },
        'properties': {
            'description': desc,
            'iconCaption': point_name,
            'marker-color': color
        }
    }


class MapGeneratorError(Exception):
    pass


class MapGenerator(object):
    __sklad: MoySklad = None
    __gmaps: googlemaps.Client = None

    projects_blacklist: list = []
    default_color: str = "#b3b3b3"
    delivery_time_missed_color: str = "#FF0000"

    @classmethod
    def moy_sklad_login(cls, login: str, password: str):
        import requests
        import base64
        cls.__sklad = MoySklad.get_instance(login, password)
        auch_base64 = base64.b64encode(f"{login}:{password}".encode('utf-8')).decode('utf-8')
        response = requests.post(f"{cls.__sklad.get_client().endpoint}/security/token",
                                 headers={"Authorization": f"Basic {auch_base64}"})
        if response.status_code != 201:
            raise MapGeneratorError(response.json().get('errors')[0].get('error'))
        cls.__sklad.set_pos_token(str(response.json()["access_token"]))

    @classmethod
    def set_googlemap_key(cls, key: str):
        try:
            cls.__gmaps = googlemaps.Client(key=key)
        except ValueError as e:
            raise MapGeneratorError(f"{str(e)} Key: \"{key}\"")

    def __init__(self):
        self.error_list = []

    def get_error_list(self) -> list:
        return self.error_list

    def create_map_for_day(self, date: datetime.date) -> (int, int, str):
        # try:
        self.error_list.clear()

        client = self.__sklad.get_client()
        methods = self.__sklad.get_methods()

        map_name = date.strftime('%d.%m.%Y')

        # создаём фильтр по дате
        date_filter = Filter().gte('deliveryPlannedMoment', date.strftime('%Y-%m-%d'))
        date_filter += Filter().lt('deliveryPlannedMoment', (date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'))

        features_list = []
        features_iter = 0

        offset = 0
        while True:
            response = client.get(
                method=methods.get_list_url('customerorder'),
                query=Query(
                    date_filter,
                    Select(limit=100, offset=offset),
                    Expand('agent', 'project')
                ),
            )
            if len(response.rows) == 0:
                break
            offset += len(response.rows)
            for row in response.rows:

                if row.get('project') is not None:
                    if row.get('project').get('name') in self.projects_blacklist:
                        continue

                color = self.default_color

                delivery_time = find_delivery_time_attribute(row)
                if delivery_time is None:
                    delivery_time = ""
                    color = self.delivery_time_missed_color

                name = row.get('name')

                actual_address = row.get('agent').get('actualAddress')
                if actual_address is None:
                    self.error_list.append(f"Actual Address not defined in \"{row.get('agent').get('name')}\"")
                    continue

                geocode_result = self.__gmaps.geocode(actual_address)
                if len(geocode_result) == 0:
                    self.error_list.append(f"Agent \"{row.get('agent').get('name')}\" address not found")
                    continue
                if len(geocode_result) != 1:
                    self.error_list.append(f"Ambiguous address in \"{row.get('agent').get('name')}\"")
                    continue

                location = geocode_result[0].get('geometry').get('location')
                features_list.append(create_point_feature(
                    features_iter,
                    location.get('lat'),
                    location.get('lng'),
                    f"{name} ({delivery_time})",
                    actual_address,
                    color
                ))
                features_iter += 1

        geojson_point_collection = {
            'type': "FeatureCollection",
            'metadata': {
                'name': map_name,
            },
            "features": features_list
        }

        return features_iter + len(self.error_list), features_iter, json.dumps(geojson_point_collection)
        # except ApiError as e:
        #     raise MapGeneratorError(f"Google Maps API error: {e}")
        # except HTTPError as e:
        #     raise MapGeneratorError(f"HTTP error: {e}")
        # except Timeout as e:
        #     raise MapGeneratorError(f"Timeout error: {e}")
        # except TransportError as e:
        #     raise MapGeneratorError(f"Transport error: {e}")
        # except TransportError as e:
        #     raise MapGeneratorError(f"Transport error: {e}")
