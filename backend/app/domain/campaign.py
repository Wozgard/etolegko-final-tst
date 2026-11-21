CAMPAIGN_NAME_PREFIX = "test_shvirev_"


def normalize_campaign_name(name: str) -> str:
    if name.startswith(CAMPAIGN_NAME_PREFIX):
        return name
    return f"{CAMPAIGN_NAME_PREFIX}{name}"


def campaign_alias(name: str) -> str:
    return name.lower().replace(" ", "_")