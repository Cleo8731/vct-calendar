import json
import logging
from datetime import datetime as dt, timedelta

from googleapiclient.errors import HttpError

import auth
import calendar_sync
import config
import scraper

logger = logging.getLogger(__name__)


def load_last_updated():
    if config.LAST_UPDATED_PATH.exists():
        with config.LAST_UPDATED_PATH.open("r") as timestamps:
            return json.load(timestamps)
    return {region: "" for region in config.REGION_ID}


def main():
    config.configure_logging()

    try:
        service = auth.get_calendar_service()

        web_cals = {}
        last_updated = load_last_updated()

        for region in config.REGION_ID:
            try:
                cal_id, webcal_link = calendar_sync.fetch_calendar(service, region)
                web_cals[region] = webcal_link

                needs_update = (
                    not last_updated[region]
                    or dt.fromisoformat(last_updated[region]) <= dt.now() - timedelta(days=1)
                )
                matches_info = scraper.scrape("all" if needs_update else "upcoming", region)
                last_updated[region] = dt.now().isoformat()
                calendar_sync.update_calendar(service, cal_id, matches_info, region)

            except Exception as e:
                logger.error(f"{region} Calendar issue: {e}")
                continue

        with config.WEB_CAL_PUBLIC_PATH.open("w") as f:
            json.dump(web_cals, f, indent=4)

        with config.LAST_UPDATED_PATH.open("w") as timestamps:
            json.dump(last_updated, timestamps, indent=4)
            logger.info("Last updated timestamps saved...")

    except HttpError as error:
        logger.error(f"Houston, we have a {error}")


if __name__ == "__main__":
    main()
