import discord

from bot.data.models import CERTIFICATIONS
from bot.services.sheets import *
from bot.services.signup import generate_certifications

RANKS = {
    "Joint Directive Council": 1473330648344170587,
    "Captain": 1473325827927314473,
    "Lieutenant": 1473325784763600966,
    "Sergeant Major": 1473325752685695170,
    "Master Sergeant": 1473325704014856355,
    "Gunnery Sergeant": 1473325677284560961,
    "Staff Sergeant": 1473325650931748965,
    "Sergeant": 1473325619667271801,
    "Corporal": 1473319571321651396,
    "Elite Operator": 1473052503095644250,
    "Decorated Operator": 1473048747981410467,
    "Experienced Operator": 1473048446435983391,
    "Operator": 1473048399606448429,
    "Enlisted": 1473048349656486125,
    "Newbie": 1472937862184960107,
}

RANK_ORDER = [
    "Newbie",
    "Enlisted",
    "Operator",
    "Experienced Operator",
    "Decorated Operator",
    "Elite Operator",
    "Corporal",
    "Sergeant",
    "Staff Sergeant",
    "Gunnery Sergeant",
    "Master Sergeant",
    "Sergeant Major",
    "Lieutenant",
    "Captain",
    "Joint Directive Council",
]

RANK_LEVEL = {rank: level for level, rank in enumerate(RANK_ORDER)}

CHECK_MARKS = {"✓", "✔", "☑", "true", "yes", "y", "1"}

RANK_REQUIREMENT_MAP = {
    "Newbie": "Newbie",
    "Enlisted": "Enlisted",
    "Operator": "Operator",
    "Operator+": "Experienced Operator",
    "Officer+": "Lieutenant",
}


def _is_required(value) -> bool:
    """
    Returns True if a spreadsheet cell represents a check/requirement.
    """
    if value is None:
        return False

    value = str(value).strip().lower()

    return value in {
        "✓",
        "✔",
        "☑",
        "true",
        "yes",
        "y",
        "1",
    }


def parse_role_requirements(values: list[list]) -> dict:
    """
    Converts the role requirements spreadsheet into a Python dictionary.
    """

    if not values:
        return {}

    headers = [str(header).strip() for header in values[0]]

    try:
        role_index = headers.index("Role")
    except ValueError:
        raise ValueError("Spreadsheet is missing a 'Role' column")

    try:
        desc_index = headers.index("Description")
    except ValueError:
        desc_index = None

    certification_columns = [
        header
        for header in headers
        if header
        not in {
            "Role",
            "Description",
            *RANK_REQUIREMENT_MAP.keys(),
        }
    ]

    requirements = {}

    for row in values[1:]:
        row = row + [""] * (len(headers) - len(row))

        role = str(row[role_index]).strip()

        if not role:
            continue

        description = str(row[desc_index]).strip() if desc_index is not None else ""

        # ----------------------------------------
        # Find minimum rank
        # ----------------------------------------

        required_rank = None

        for spreadsheet_rank in RANK_REQUIREMENT_MAP.keys():
            if spreadsheet_rank not in headers:
                continue

            index = headers.index(spreadsheet_rank)

            if _is_required(row[index]):
                required_rank = RANK_REQUIREMENT_MAP[spreadsheet_rank]
                break

        # ----------------------------------------
        # Find certifications
        # ----------------------------------------

        certifications = []

        for certification in certification_columns:
            index = headers.index(certification)

            if _is_required(row[index]):
                certifications.append(certification)

        requirement = {
            "rank": required_rank,
            "certifications": certifications,
            "description": description,
        }

        # ----------------------------------------
        # Add requirement
        # ----------------------------------------

        if role not in requirements:
            requirements[role] = requirement
            continue

        existing = requirements[role]

        if isinstance(existing, list):
            if requirement not in existing:
                existing.append(requirement)

        elif existing != requirement:
            requirements[role] = [
                existing,
                requirement,
            ]

    return requirements


def meets_rank(user_rank: str, required_rank: str) -> bool:
    return RANK_LEVEL[user_rank] >= RANK_LEVEL[required_rank]


def check_eligibility(user_rank, user_certs, role_requirement) -> bool:

    required_rank = role_requirement.get("rank")
    required_certs = role_requirement.get("certifications", [])

    if required_rank is not None:
        if user_rank is None:
            return False

        rank_ok = RANK_LEVEL[user_rank] >= RANK_LEVEL[required_rank]
    else:
        rank_ok = True

    certs_ok = all(cert in user_certs for cert in required_certs)

    return rank_ok and certs_ok


def get_role_requirements(
    spreadsheet_id: str,
    range_name: str,
) -> dict:
    """
    Reads the role requirements spreadsheet and converts
    it into ROLE_REQUIREMENTS format.
    """

    values = get_values(
        spreadsheet_id,
        range_name,
    )

    return parse_role_requirements(values)


def available_roles(member: discord.Member, role_list: dict) -> list:
    available = {}

    user_rank = None
    highest_level = -1

    # Find user's highest rank
    for role in member.roles:
        for rank, role_id in RANKS.items():
            if role.id == role_id:
                level = RANK_LEVEL[rank]

                if level > highest_level:
                    highest_level = level
                    user_rank = rank

    # Get user's certifications
    user_certs = set(generate_certifications(member))

    # Check every role requirement
    for role_name, requirement in role_list.items():
        if isinstance(requirement, dict):
            if check_eligibility(user_rank, user_certs, requirement):
                available[role_name] = requirement.get("description", "")
        elif isinstance(requirement, list):
            matching = next(
                (
                    req
                    for req in requirement
                    if check_eligibility(user_rank, user_certs, req)
                ),
                None,
            )
            if matching:
                available[role_name] = matching.get("description", "")

    return available


def extract_roles(answers: dict) -> tuple[str, str, str]:
    return (
        answers.get("role_select_1", ""),
        answers.get("role_select_2", ""),
        answers.get("role_select_3", ""),
    )
