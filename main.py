from dataclasses import dataclass
import json
import argparse

import requests

# Define data classes
@dataclass
class Location:
    lat: float = None
    lng: float = None
    address: str = None
    city: str = None
    country: str = None

@dataclass
class Amenities:
    general: list[str] = None
    room: list[str] = None


@dataclass
class Image:
    link: str = None
    description: str = None

@dataclass
class Images:
    rooms: list[Image]
    site: list[Image]
    amenities: list[Image]

@dataclass
class Hotel:
    id: str
    destination_id: str
    name: str
    location: Location
    description: str
    amenities: Amenities
    images: Images
    booking_conditions: list[str]

class BaseSupplier:
    def endpoint():
        """URL to fetch supplier data"""

    def parse(obj: dict) -> Hotel:
        """Parse supplier-provided data into Hotel object"""

    def fetch(self):
        url = self.endpoint()
        resp = requests.get(url)
        return [self.parse(dto) for dto in resp.json()]


class Acme(BaseSupplier):
    @staticmethod
    def endpoint():
        return 'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/acme'

    @staticmethod
    def parse(dto: dict) -> Hotel:

        # Parse location
        location = Location(
            lat=dto['Latitude'],
            lng=dto['Longitude'],
            address=dto['Address'].strip(),
            city=dto['City'],
            country=dto['Country']
        )

        # Parse amenities
        # Assume that the amenities are general and not room-specific
        amenities = Amenities(
            general=[facility.strip().lower() for facility in dto['Facilities']],
            room=[] 
        )

        return Hotel(
            id=dto['Id'],
            destination_id= str(dto['DestinationId']),
            name=dto['Name'],
            location=location,
            description=dto['Description'],
            amenities=amenities,
            images=Images(
                rooms=[],
                site=[],
                amenities=[]
            ),
            booking_conditions = []
        )

    @staticmethod
    def fetch():
        url = Acme.endpoint()
        resp = requests.get(url)

        # Return a list of tuples with the hotel object and priority
        return [(Acme.parse(dto), 1) for dto in resp.json()]
    

class PaperFlies(BaseSupplier):
    @staticmethod
    def endpoint():
        return 'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/paperflies'

    @staticmethod
    def parse(dto: dict) -> Hotel:
        
        # Parse the location details
        location = Location(
            address=dto['location']['address'].strip(),
            country=dto['location']['country']
        )
        
        # Parse amenities
        amenities = Amenities(
            general=[item.strip() for item in dto['amenities']['general']],
            room=[item.strip() for item in dto['amenities']['room']]
        )
        
        # Parse images
        rooms_images = [Image(link=image['link'], description=image['caption']) for image in dto['images']['rooms']]
        site_images = [Image(link=image['link'], description=image['caption']) for image in dto['images']['site']]
        images = Images(
            rooms=rooms_images,
            site=site_images,
            amenities=[]  # No amenity images in the provided response
        )
        
        # Parse booking conditions
        booking_conditions = [condition.strip().split('.')[0] for condition in dto['booking_conditions']]
        
        # Create the hotel object and return
        return Hotel(
            id=dto['hotel_id'],
            destination_id=str(dto['destination_id']),
            name=dto['hotel_name'],
            location=location,
            description=dto['details'].strip(),
            amenities=amenities,
            images=images,
            booking_conditions=booking_conditions
        )
    @staticmethod
    def fetch():
        url = PaperFlies.endpoint()
        resp = requests.get(url)
        # Return a list of tuples with the hotel object and priority
        return [(PaperFlies.parse(dto), 3) for dto in resp.json()]

class Patagonia(BaseSupplier):
    @staticmethod
    def endpoint():
        return 'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/patagonia'

    @staticmethod
    def parse(dto: dict) -> Hotel:
        location = Location(
            lat=dto['lat'],
            lng=dto['lng'],
            address=dto['address'],
        )
        
        # Parse amenities list
        amenities = Amenities(
            general=[],  
            room=dto.get('amenities', []) 
        )
        
        # Parse images
        rooms_images = [
            Image(link=image['url'], description=image['description'])
            for image in dto['images']['rooms']
        ]
        site_images = []  
        amenities_images = [
            Image(link=image['url'], description=image['description'])
            for image in dto['images']['amenities']
        ]
        images = Images(
            rooms=rooms_images,
            site=site_images,
            amenities=amenities_images
        )
        
  
        return Hotel(
            id=dto['id'],
            destination_id=str(dto['destination']),  
            name=dto['name'],
            location=location,
            description=dto['info'], 
            amenities=amenities,
            images=images,
            booking_conditions=[]
        )
    
    @staticmethod
    def fetch():
        url = Patagonia.endpoint()
        resp = requests.get(url)
        # Return a list of tuples with the hotel object and priority
        return [(Patagonia.parse(dto), 2) for dto in resp.json()]

class Helper:
    @staticmethod
    def get_first_not_none(hotels,fields):
        field = fields.split(".")
        for hotel in hotels:
            value = hotel
            for f in field:
               value = getattr(value, f, None)
            if value:
                return value
        return None

class HotelsService:
    def __init__(self):
        self.data = []

    def merge_and_save(self, data):
        map = {}
        for tup in data:
            key = (tup[0].id, tup[0].destination_id)
            if key in map:
                map[key].append(tup)
            else:
                map[key] = [tup]
        
        for key, pairs in map.items():
            hotels = [pair[0] for pair in pairs]
            if len(hotels) == 1:
                self.data.append(hotels[0])
            else:
                # Choose the hotel with the highest priority
                pairs.sort(key=lambda x: x[1], reverse=True)
                hotels = [pair[0] for pair in pairs]            

                location = Location(
                    lat = Helper.get_first_not_none(hotels, 'location.lat'),
                    lng = Helper.get_first_not_none(hotels, 'location.lng'),
                    address = Helper.get_first_not_none(hotels, 'location.address'),
                    city = Helper.get_first_not_none(hotels, 'location.city'),
                    country = Helper.get_first_not_none(hotels, 'location.country')
                )

                description = Helper.get_first_not_none(hotels, 'description')
                amenities = Amenities(
                    general = Helper.get_first_not_none(hotels, 'amenities.general'),
                    room = Helper.get_first_not_none(hotels, 'amenities.room')
                )

                images = Images(
                    rooms = Helper.get_first_not_none(hotels, 'images.rooms'),
                    site = Helper.get_first_not_none(hotels, 'images.site'),
                    amenities = Helper.get_first_not_none(hotels, 'images.amenities')
                )
                booking_conditions = Helper.get_first_not_none(hotels, 'booking_conditions') 

                merged_hotel = Hotel(
                    id= Helper.get_first_not_none(hotels, 'id'),
                    destination_id= Helper.get_first_not_none(hotels, 'destination_id'),
                    name= Helper.get_first_not_none(hotels, 'name'),
                    location= location,
                    description= description,
                    amenities= amenities,
                    images= images,
                    booking_conditions= booking_conditions
                )
                self.data.append(merged_hotel)
            


    def find(self, hotel_ids, destination_ids):
        if('none' in hotel_ids or 'none' in destination_ids):
            return self.data
        return [hotel for hotel in self.data if hotel.id in hotel_ids and hotel.destination_id in destination_ids]

def fetch_hotels(hotel_ids, destination_ids):
    # Write your code here

    suppliers = [
        Acme(),
        PaperFlies(),
        Patagonia(),
    ]

    # Fetch data from all suppliers
    all_supplier_data = []
    for supp in suppliers:
        all_supplier_data.extend(supp.fetch())

    # Merge all the data and save it in-memory somewhere
    svc = HotelsService()
    svc.merge_and_save(all_supplier_data)


    # Fetch filtered data
    filtered = svc.find(hotel_ids, destination_ids)


    # Return as json
    return json.dumps(filtered, default=lambda x: x.__dict__)
    
def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("hotel_ids", type=str, help="Hotel IDs")
    parser.add_argument("destination_ids", type=str, help="Destination IDs")
    
    # Parse the arguments
    args = parser.parse_args()
    
    hotel_ids = args.hotel_ids.split(',')
    destination_ids = args.destination_ids.split(',')
    
    result = fetch_hotels(hotel_ids, destination_ids)
    print(result)

if __name__ == "__main__":
    main()