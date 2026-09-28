import os
import re
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SHEET_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


SERVICE_ACCOUNT_FILE = str(
    Path(__file__).resolve().parents[2] / "credentials" / "google-service-account.json"
)

_sheets_service = None

# init functions


async def init_sheets():
    """
    Creates the shared Google Sheets and Drive API clients.

    Safe to call on every bot startup.
    """

    global _sheets_service, _drive_service

    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )

    _sheets_service = build(
        "sheets",
        "v4",
        credentials=credentials,
    )

    _drive_service = build(
        "drive",
        "v3",
        credentials=credentials,
    )


def _get_sheets_connection():
    """
    Returns the shared Google Sheets API client.
    Raises if init_sheets() hasn't run yet.
    """

    if _sheets_service is None:
        raise RuntimeError("Google Sheets not initialized — call init_sheets() first")

    return _sheets_service


async def close_sheets():
    """
    Closes the underlying HTTP sessions.
    Call on bot shutdown.
    """

    global _sheets_service, _drive_service

    if _sheets_service is not None:
        _sheets_service.close()
        _sheets_service = None

    if _drive_service is not None:
        _drive_service.close()
        _drive_service = None


# spreadsheet functions


def get_spreadsheet(spreadsheet_id: str):
    """
    Gets spreadsheet metadata.
    """

    service = _get_sheets_connection()

    return service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()


# value functions


def get_values(
    spreadsheet_id: str,
    range_name: str,
):
    """
    Returns values from a range.

    Example:
        get_values("abc123", "Sheet1!A1:C10")
    """

    service = _get_sheets_connection()

    result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
        )
        .execute()
    )

    return result.get("values", [])


def update_values(
    spreadsheet_id: str,
    range_name: str,
    values: list[list],
):
    """
    Replaces values in a range.

    Example:
        update_values(
            spreadsheet_id,
            "Sheet1!A1:B2",
            [
                ["Name", "Score"],
                ["Bob", 100],
            ],
        )
    """

    service = _get_sheets_connection()

    body = {
        "values": values,
    }

    return (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )


def append_values(
    spreadsheet_id: str,
    range_name: str,
    values: list[list],
):
    """
    Appends rows to the end of a range.
    """

    service = _get_sheets_connection()

    body = {
        "values": values,
    }

    return (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )


def clear_values(
    spreadsheet_id: str,
    range_name: str,
):
    """
    Clears values from a range.
    """

    service = _get_sheets_connection()

    return (
        service.spreadsheets()
        .values()
        .clear(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            body={},
        )
        .execute()
    )


def extract_sheet_id(url: str) -> str | None:
    match = SHEET_ID_RE.search(url)
    return match.group(1) if match else None


def get_valid_sheet_id(link: str) -> str | None:
    sheet_id = extract_sheet_id(link)

    if sheet_id is None:
        return None

    try:
        get_spreadsheet(sheet_id)
    except HttpError:
        return None

    return sheet_id


def spreadsheet_url(spreadsheet_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


def batch_update_values(spreadsheet_id: str, updates: list[tuple[str, list[list]]]):
    """
    Updates multiple ranges in one API call.

    Args:
        updates: list of (range_name, values) pairs, e.g.
            [("Signup!B4", [["Machine Gunner"]]), ("Signup!C4", [["Squad Leader"]])]
    """
    service = _get_sheets_connection()

    body = {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {"range": range_name, "values": values} for range_name, values in updates
        ],
    }

    return (
        service.spreadsheets()
        .values()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )


def find_header_map(
    spreadsheet_id: str, sheet_name: str, needed_labels: set[str], search_rows: int = 5
) -> tuple[dict[str, int], int]:
    """
    Scans the first search_rows rows for a row containing all needed_labels.
    Returns (label -> column index, header_row_number).
    """
    rows = get_values(spreadsheet_id, f"{sheet_name}!A1:Z{search_rows}")

    for row_num, row in enumerate(rows, start=1):
        col_map = {cell.strip(): i for i, cell in enumerate(row) if cell.strip()}
        if needed_labels.issubset(col_map.keys()):
            return col_map, row_num

    raise ValueError(
        f"Could not find header row with columns {needed_labels} in {sheet_name}"
    )


def find_row_by_value(
    spreadsheet_id: str,
    sheet_name: str,
    col_map: dict[str, int],
    match_col_index: int,
    match_value: str,
    header_row: int,
) -> int | None:
    """
    Returns the row number (1-indexed) where match_col_index equals
    match_value, or None if not found.
    """
    last_col_letter = chr(ord("A") + max(col_map.values()))
    data_start = header_row + 1
    existing = get_values(
        spreadsheet_id, f"{sheet_name}!A{data_start}:{last_col_letter}"
    )

    for i, row in enumerate(existing, start=data_start):
        cell = row[match_col_index] if len(row) > match_col_index else ""
        if str(cell) == str(match_value):
            return i

    return None


def find_row_by_value_or_empty(
    spreadsheet_id: str,
    sheet_name: str,
    col_map: dict[str, int],
    match_col_index: int,
    match_value: str,
    header_row: int,
) -> int:
    """
    Returns the row where match_col_index equals match_value, else the
    first row where that column is empty, else the row right after the
    last existing row.
    """
    last_col_letter = chr(ord("A") + max(col_map.values()))
    data_start = header_row + 1
    existing = get_values(
        spreadsheet_id, f"{sheet_name}!A{data_start}:{last_col_letter}"
    )

    empty_row_index = None
    for i, row in enumerate(existing, start=data_start):
        cell = row[match_col_index] if len(row) > match_col_index else ""
        if str(cell) == str(match_value):
            return i
        if not cell and empty_row_index is None:
            empty_row_index = i

    return empty_row_index or (data_start + len(existing))


def write_row_cells(
    spreadsheet_id: str, sheet_name: str, row: int, cells: list[tuple[int, str]]
):
    """
    Writes {col_index: value} pairs to specific cells in one row via a
    single batch update.
    """
    updates = [
        (f"{sheet_name}!{_col_letter(col)}{row}", [[value]]) for col, value in cells
    ]
    batch_update_values(spreadsheet_id, updates)


def _col_letter(index: int) -> str:
    return chr(ord("A") + index)
