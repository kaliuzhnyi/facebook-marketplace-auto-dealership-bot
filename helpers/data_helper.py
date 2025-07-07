import os
import shutil
from pathlib import Path
from urllib.parse import urljoin

import requests

from config import CONFIG_DEALER_LICENSE_ID, CONFIG_DEALER_URL, CONFIG_PHOTOS_BASE_FOLDER, CONFIG
from helpers.csv_helper import Row, push_data_to_csv, BaseColor, FuelType, Transmission, BodyType


def import_data_to_csv(csv_file_name: str):
    data = import_data_from_website_cams(CONFIG_DEALER_LICENSE_ID)
    push_data_to_csv(data, csv_file_name)


def import_data_from_website_cams(license_id: str) -> list[Row]:
    result = []

    url = urljoin(CONFIG_DEALER_URL, '/php/get_list.php')
    params = {
        "sql": f"select * from vehicles_for_sale where license = {license_id} order by online_posted desc"
    }
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    clear_photos_base_folder(CONFIG_PHOTOS_BASE_FOLDER)

    vehicles = response.json()
    for item in vehicles:
        try:

            year = int(item['year']) if item.get('year') and str(item['year']).isdigit() else None
            make = str(item.get('make', '')).strip()
            model = str(item.get('model', '')).strip()

            mileage = int(item['mileage']) if item.get('mileage') and str(item['mileage']).isdigit() else 0

            price = float(item['sale_price_sel']) if item.get('sale_price_sel') and str(item['sale_price_sel']).replace(
                '.', '', 1).isdigit() else 0.0

            stockno = item.get('stockno', '').strip()

            photos_folder = os.path.join(Path(__file__).resolve().parent, CONFIG['photos']['base_folder'])
            if stockno:
                photos_folder = os.path.join(photos_folder, stockno)

            row = Row(
                body_type=BodyType.from_str(str(item.get('body_type') or item.get('product', '')).strip()),
                year=year,
                make=make,
                model=model,
                exterior_color=BaseColor.from_str(str(item.get('colour', '')).strip()),
                interior_color=BaseColor.from_str(str(item.get('interior', '')).strip()),
                mileage=mileage,
                fuel_type=FuelType.from_str(str(item.get('fuel_type', '')).strip()),
                transmission=Transmission.from_str(str(item.get('transmission_description')).strip()),
                price=price,
                title=f"{year or ''} {make} {model}".strip(),
                description=str(item.get('online_description', '')).strip(),
                location=f"{item.get('city', '').strip()}, {item.get('province', '').strip()}",
                groups=['default'],
                stockno=stockno,
                vin=item.get('vin', '').strip(),
                photos_folder=photos_folder
            )

            if stockno:
                row.photos_names = get_and_save_photos(stockno=stockno,
                                                       photos_folder=row.photos_folder,
                                                       license_id=license_id)

            result.append(row)
        except Exception as e:
            print(f"Error to processing stockno={item.get('stockno')}: {e}")
        break
    return result


def get_and_save_photos(stockno: str,
                        photos_folder: str,
                        license_id: str) -> list[str]:
    """
    Downloads photos for a specific stock number into the given folder.
    Returns a list of downloaded file names.
    """
    sql = f"select url from photo_url where stockno = '{stockno}' and license = {license_id} order by sequence_id"
    url = urljoin(CONFIG_DEALER_URL, '/php/get_list.php')
    params = {"sql": sql}
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        photo_data = response.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch photo URLs for stockno={stockno}: {e}")
        return []

    os.makedirs(photos_folder, exist_ok=True)
    photo_names = []

    for p in photo_data:
        rel_url = p.get("url", "")
        if not rel_url:
            continue

        photo_url = urljoin(CONFIG_DEALER_URL, f'/uploads/{license_id}/{rel_url}')
        filename = os.path.basename(rel_url)
        save_path = os.path.join(photos_folder, filename)

        try:
            photo_resp = requests.get(photo_url, headers=headers)
            photo_resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(photo_resp.content)
            photo_names.append(filename)
        except Exception as e:
            print(f"[WARNING] Could not download photo {photo_url}: {e}")

    return photo_names


def clear_photos_base_folder(photos_folder: str):

    if not os.path.exists(photos_folder):
        return  # Nothing to clear

    for entry in os.listdir(photos_folder):
        entry_path = os.path.join(photos_folder, entry)
        try:
            if os.path.isfile(entry_path) or os.path.islink(entry_path):
                os.remove(entry_path)
            elif os.path.isdir(entry_path):
                shutil.rmtree(entry_path)
        except Exception as e:
            print(f"[ERROR] Failed to remove {entry_path}: {e}")
