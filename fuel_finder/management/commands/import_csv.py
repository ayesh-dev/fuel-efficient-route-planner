import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from fuel_finder.models import FuelStation
from fuel_finder.services import geocode_location

class Command(BaseCommand):
    help = 'Imports fuel station CSV data into SQLite database'

    def handle(self, *args, **kwargs):
        # Database clear karein taakay repetitive data duplicate na ho
        FuelStation.objects.all().delete()

        api_key = getattr(settings, "ORS_API_KEY", None)
        if not api_key:
            self.stdout.write(self.style.ERROR("ORS_API_KEY is missing in settings."))
            return

        stations = []
        file_path = 'fuel-prices-for-be-assessment.csv'
        geocode_cache = {}  # (city, state) -> [lon, lat] or None, avoids repeat lookups
        skipped_rows = 0
        skipped_geocode = 0

        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row_number, row in enumerate(reader, start=1):
                    if row_number % 100 == 0:
                        self.stdout.write(f'Processed {row_number} rows...')
                    try:
                        # Price string se '$' sign remove karke float mein convert kar rahe hain
                        price = float(row['Retail Price'].replace('$', '').strip())
                        city = row['City'].strip()
                        state = row['State'].strip()

                        cache_key = (city, state)
                        if cache_key not in geocode_cache:
                            try:
                                geocode_cache[cache_key] = geocode_location(
                                    f"{city}, {state}", api_key
                                )
                            except Exception:
                                geocode_cache[cache_key] = None

                        coords = geocode_cache[cache_key]
                        if coords is None:
                            skipped_geocode += 1
                        longitude, latitude = coords if coords else (None, None)

                        stations.append(
                            FuelStation(
                                opis_id=int(row['OPIS Truckstop ID']),
                                name=row['Truckstop Name'],
                                address=row['Address'],
                                city=city,
                                state=state,
                                price=price,
                                latitude=latitude,
                                longitude=longitude,
                            )
                        )
                    except (ValueError, KeyError):
                        skipped_rows += 1
                        continue

            # bulk_create sary records ek sath fast save karta hai
            FuelStation.objects.bulk_create(stations, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(stations)} fuel stations!'))
            self.stdout.write(f'Skipped rows (bad data): {skipped_rows}')
            self.stdout.write(f'Stations without coordinates (geocoding failed): {skipped_geocode}')

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File "{file_path}" not found in project root folder!'))