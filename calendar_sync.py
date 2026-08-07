import logging
from time import sleep as wait

from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def execute_with_retry(request, max_attempts=1):
    while True:
        try:
            result = request.execute()
            wait(0.2)
            return result
        except HttpError as error:
            if error.status_code == 403:
                wait_time = 10
                logger.warning(f"Hit error {error.status_code}. Waiting for {wait_time} seconds...")
                wait(wait_time)
            else:
                return error.status_code

def create_calendar(service, region):
    cal_body = {
        "description": f"VCT {region} event matches",
        "summary": f"VCT {region}",
        "timeZone": "America/Los_Angeles",
    }
    cal_id = service.calendars().insert(body=cal_body).execute()["id"]
    acl_public = {
        "scope": {"type": "default"},
        "role": "reader",
    }
    service.acl().insert(calendarId=cal_id, body=acl_public).execute()


def fetch_calendar(service, region):
    logger.info("Searching for existing calendar...")
    cal_id = next(
        (
            cal["id"]
            for cal in service.calendarList().list().execute()["items"]
            if cal["summary"] == f"VCT {region}"
        ),
        None,
    )

    if not cal_id:
        logger.info("No calendar found. Creating new calendar...")
        create_calendar(service, region)
    else:
        logger.info("Existing calendar found...")

    webcal_link = (
        f"https://calendar.google.com/calendar/u/0/r?cid={cal_id}"
    )
    return cal_id, webcal_link


def update_calendar(service, cal_id, matches_info, region):
    logger.info("Writing to calendar... ")

    for event in matches_info:
        for match_id in matches_info[event]:

            match_alias = matches_info[event][match_id]
            event_body = {
                "description": f"{event}: {match_alias['stage']} {match_alias['series']}",
                "end": {
                    "dateTime": match_alias["time_end"],
                    "timeZone": "America/Los_Angeles",
                },
                "endTimeUnspecified": False,
                "eventType": "default",
                "id": match_id,
                "start": {
                    "dateTime": match_alias["time_begin"],
                    "timeZone": "America/Los_Angeles",
                },
                "summary": f"{match_alias['team1']} vs. {match_alias['team2']}",
            }

            # Update existing event
            if execute_with_retry(
                service.events().update(calendarId=cal_id, eventId=match_id, body=event_body)
            ) == 404:
                # create new event
                execute_with_retry(
                    service.events().insert(calendarId=cal_id, body=event_body), 5
                )
                logger.info(f"Created new event (id={match_id})... ")
            else:
                logger.info(f"Updated existing event (id={match_id})... ")

    logger.info(f"VCT {region} Calendar successfully updated... ")
