PG_DOMAIN = "pogrywamy.pl"


def check_link(link: str):
    if not link.startswith(f"https://{PG_DOMAIN}/topic"):
        return False
    return True
