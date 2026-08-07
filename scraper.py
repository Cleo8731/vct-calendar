import logging
from datetime import datetime as dt, timedelta

import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)


def prize_pool(prize_text):
    return int(prize_text.replace("$", "").replace(",", ""))


def is_international(event_tag, event_path) -> bool:
    ### find international events by prize pool
    prize_tag = event_tag.find(class_="mod-prize")
    prize_text = prize_tag.find(string=True, recursive=False).strip()
    if prize_text == "TBD" or prize_pool(prize_text) < 500000:
        return False
    if not config.INCLUDE_EWC and "esports-world-cup" in event_path:
        return False
    return True


def is_regional(event_tag, event_path) -> bool:
    prize_tag = event_tag.find(class_="mod-prize")
    prize_text = prize_tag.find(string=True, recursive=False).strip()
    if not prize_text == "TBD" and prize_pool(prize_text) >= 500000:
        return False
    if not config.INCLUDE_EWC and "esports-world-cup" in event_path:
        return False
    if not config.INCLUDE_CHALLENGERS and "challengers" in event_path:
        return False
    return True


def is_americas(event_tag, event_path) -> bool:
    return is_regional(event_tag, event_path)


def is_emea(event_tag, event_path) -> bool:
    if not is_regional(event_tag, event_path):
        return False
    if not config.INCLUDE_STRIKE_ARABIA and "strike-arabia" in event_path:
        return False
    return True


def is_pacific(event_tag, event_path) -> bool:
    return is_regional(event_tag, event_path)


def is_china(event_tag, event_path) -> bool:
    return is_regional(event_tag, event_path)


def is_region(event_tag, event_path, region) -> bool:
    match region:
        case "International":
            return is_international(event_tag, event_path)
        case "Americas":
            return is_americas(event_tag, event_path)
        case "EMEA":
            return is_emea(event_tag, event_path)
        case "Pacific":
            return is_pacific(event_tag, event_path)
        case "China":
            return is_china(event_tag, event_path)


def scrape_matches(matches_page, matches_info):
    soup = BeautifulSoup(matches_page.text, "html.parser")
    event_name = soup.find(class_="event-header-main-title").text.strip()
    matches_info[event_name] = {}

    mixed_tags = soup.find_all(
        class_=[
            "match-item",
            "wf-label mod-large",
            "match-item-time",
            "match-item-vs-team-name",
            "match-item-event",
        ]
    )
    team_side = False
    team_name = ["", ""]

    for tag in mixed_tags:
        try:
            classes = tag.get("class")
            match classes:
                case _ if "wf-module-item" == classes[0] and "match-item" == classes[1]:
                    match_id = tag.get("href").split("/")[1]

                case ["wf-label", "mod-large"]:
                    date_text = tag.find(string=True, recursive=False).strip()[5:]

                case ["match-item-time"]:
                    # Create match info structure and fill in match datetime
                    time_text = tag.text.strip()
                    dt_temp = dt.strptime(date_text + time_text, "%B %d, %Y%I:%M %p")

                case ["match-item-vs-team-name"]:
                    # fill in team names
                    team_name[team_side] = tag.text.strip()
                    team_side = not team_side

                case ["match-item-event", "text-of"]:
                    # fill in series and stage info
                    series = tag.find_all(string=True)[1].strip()
                    match_len = config.SERIES_LEN.get(series, config.SERIES_LEN_DEFAULT)
                    matches_info[event_name][match_id] = {
                        "event_id": "",
                        "series": series,
                        "stage": tag.find_all(string=True)[2].strip(),
                        "team1": team_name[0],
                        "team2": team_name[1],
                        "time_begin": dt_temp.isoformat(),
                        "time_end": (dt_temp + timedelta(hours=match_len)).isoformat(),
                    }
        except Exception as e:
            logger.warning(f"Skipping broken match due to error: {e}")
            continue


def scrape_helper(soup, matches_info, max_pages, region):
    for page_num in range(1, max_pages + 1):
        logger.info(f"Opening VLR Events page {page_num}...")
        if not page_num == 1:
            tier1 = requests.get(
                f"{config.VLR_URL}/events/?tier=60&region={config.REGION_ID[region]}&page={page_num}"
            )
            soup = BeautifulSoup(tier1.text, "html.parser")

        event_tags = soup.find_all(class_="wf-card mod-flex event-item")
        for event_tag in event_tags:
            event_path = event_tag.get("href")
            if not is_region(event_tag, event_path, region):
                continue
            logger.info(
                f"Accessing Event URL: {config.VLR_URL}{event_path[:6]}/matches{event_path[6:]}/?series_id=all"
            )
            matches_page = requests.get(
                f"{config.VLR_URL}{event_path[:6]}/matches{event_path[6:]}/?series_id=all"
            )
            scrape_matches(matches_page, matches_info)
    logger.info("Webscrape complete...")
    return matches_info


def scrape(scrape_type, region):
    logger.info(f"Beginning webscrape of {scrape_type} {region} VCT matches...")
    matches_info = {}
    tier1 = requests.get(f"{config.VLR_URL}/events/?tier=60&region={config.REGION_ID[region]}")
    tier1_soup = BeautifulSoup(tier1.text, "html.parser")

    if scrape_type == "upcoming":
        tag_upcoming = tier1_soup.find(class_="events-container-col")
        return scrape_helper(tag_upcoming, matches_info, 1, region)

    elif scrape_type == "all":
        last_page_tags = tier1_soup.find_all(class_="btn mod-page")
        max_pages = int(last_page_tags[-1].text) if last_page_tags else 1
        return scrape_helper(tier1_soup, matches_info, max_pages, region)
