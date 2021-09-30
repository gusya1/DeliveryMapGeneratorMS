import googlemaps
from googlemaps.exceptions import *
from MSApi import MSApi
from MSApi.properties import DateTimeFilter, Expand
from MSApi.documents import CustomerOrder
import json
import datetime


def find_delivery_time_attribute(customerorder: CustomerOrder):
    attributes = customerorder.gen_attributes()
    if attributes is None:
        return None
    for attr in customerorder.gen_attributes():
        if attr.get_name() == "Время доставки":
            return attr.get_value()
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
    __gmaps: googlemaps.Client = None

    projects_blacklist: list = []
    default_color: str = "#b3b3b3"
    delivery_time_missed_color: str = "#FF0000"

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
        try:
            self.error_list.clear()

            map_name = date.strftime('%d.%m.%Y')

            # создаём фильтр по дате
            dt = datetime.datetime.combine(date, datetime.time.min)
            date_filter = DateTimeFilter.gte('deliveryPlannedMoment', dt)
            date_filter += DateTimeFilter.lt('deliveryPlannedMoment', dt + datetime.timedelta(days=1))

            features_list = []
            features_iter = 0

            offset = 0
            for customer_order in MSApi.gen_customer_orders(filters=date_filter, expand=Expand('agent', 'project')):
                customer_order: CustomerOrder

                project = customer_order.get_project()
                if project is not None:
                    if project.get_name() in self.projects_blacklist:
                        continue

                color = self.default_color

                # FIXME maybe fix in new version MSApi
                delivery_time = find_delivery_time_attribute(customer_order)
                if delivery_time is None:
                    delivery_time = ""
                    color = self.delivery_time_missed_color

                agent = customer_order.get_agent()
                actual_address = agent.get_actual_address()
                if actual_address is None:
                    self.error_list.append(f"Actual Address not defined in \"{agent.get_name()}\"")
                    continue

                geocode_result = self.__gmaps.geocode(actual_address)
                if len(geocode_result) == 0:
                    self.error_list.append(f"Agent \"{agent.get_name()}\" address not found")
                    continue
                if len(geocode_result) != 1:
                    self.error_list.append(f"Ambiguous address in \"{agent.get_name()}\"")
                    continue

                location = geocode_result[0].get('geometry').get('location')
                features_list.append(create_point_feature(
                    features_iter,
                    location.get('lat'),
                    location.get('lng'),
                    f"{customer_order.get_name()} ({delivery_time})",
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
        except ApiError as e:
            raise MapGeneratorError(f"Google Maps API error: {e}")
        except HTTPError as e:
            raise MapGeneratorError(f"HTTP error: {e}")
        except Timeout as e:
            raise MapGeneratorError(f"Timeout error: {e}")
        except TransportError as e:
            raise MapGeneratorError(f"Transport error: {e}")
