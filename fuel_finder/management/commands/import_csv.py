import csv
from django.core.management.base import BaseCommand
from fuel_finder.models import FuelStation

class Command(BaseCommand):
    help = 'Imports fuel station CSV data into SQLite database'

    def handle(self, *args, **kwargs):
        # Database clear karein taakay repetitive data duplicate na ho
        FuelStation.objects.all().delete()
        
        stations = []
        file_path = 'fuel-prices-for-be-assessment.csv'
        
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        # Price string se '$' sign remove karke float mein convert kar rahe hain
                        price = float(row['Retail Price'].replace('$', '').strip())
                        stations.append(
                            FuelStation(
                                opis_id=int(row['OPIS Truckstop ID']),
                                name=row['Truckstop Name'],
                                address=row['Address'],
                                city=row['City'],
                                state=row['State'],
                                price=price
                            )
                        )
                    except (ValueError, KeyError):
                        continue

            # bulk_create sary records ek sath fast save karta hai
            FuelStation.objects.bulk_create(stations, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(stations)} fuel stations!'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File "{file_path}" not found in project root folder!'))