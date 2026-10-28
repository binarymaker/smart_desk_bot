"""Read-only check that Python can access classic Outlook (recent mail + today's meetings)."""

import sys
from datetime import datetime, timedelta

try:
    import pywintypes
    import win32com.client
except ImportError:
    sys.exit("pywin32 is missing. Install it with: pip install pywin32")

MAIL_COUNT = 10
MEETING_DAYS = 1
OL_FOLDER_INBOX = 6
OL_FOLDER_CALENDAR = 9
OL_MAIL_ITEM = 43


def local(dt):
    # pywin32 tags Outlook's local times as UTC; drop the tag to keep the real local value.
    return dt.replace(tzinfo=None)


def short(text, size):
    text = (text or "").replace("\r", " ").replace("\n", " ").strip()
    return text if len(text) <= size else text[: size - 3] + "..."


def connect():
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        return outlook.GetNamespace("MAPI")
    except pywintypes.com_error as err:
        sys.exit(
            f"Cannot connect to Outlook: {err}\n"
            "Classic Outlook (desktop) is required. 'New Outlook' has no COM interface."
        )


def show_recent_mail(ns):
    print(f"\n=== Last {MAIL_COUNT} emails (Inbox) ===")
    items = ns.GetDefaultFolder(OL_FOLDER_INBOX).Items
    items.Sort("[ReceivedTime]", True)

    shown = 0
    item = items.GetFirst()
    while item is not None and shown < MAIL_COUNT:
        if item.Class == OL_MAIL_ITEM:
            received = local(item.ReceivedTime).strftime("%d-%b %H:%M")
            unread = "*" if item.UnRead else " "
            print(f"{unread} {received}  {short(item.SenderName, 24):<24}  {short(item.Subject, 50)}")
            shown += 1
        item = items.GetNext()

    if shown == 0:
        print("No emails found.")
    else:
        print("(* = unread)")


def show_meetings(ns):
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=MEETING_DAYS)
    print(f"\n=== Meetings {start:%d-%b-%Y} ({MEETING_DAYS} day) ===")

    items = ns.GetDefaultFolder(OL_FOLDER_CALENDAR).Items
    items.IncludeRecurrences = True
    items.Sort("[Start]")
    # Month names avoid dd/mm vs mm/dd ambiguity in Outlook's date filter.
    fmt = "%d %B %Y %H:%M"
    restricted = items.Restrict(f"[Start] >= '{start:{fmt}}' AND [Start] < '{end:{fmt}}'")

    shown = 0
    item = restricted.GetFirst()
    while item is not None and shown < 50:
        begin = local(item.Start)
        if start <= begin < end:
            finish = local(item.End)
            print(f"{begin:%H:%M}-{finish:%H:%M}  {short(item.Subject, 50):<50}  {short(item.Location, 25)}")
            shown += 1
        item = restricted.GetNext()

    if shown == 0:
        print("No meetings found.")


def main():
    ns = connect()
    print("Connected to Outlook.")
    show_recent_mail(ns)
    show_meetings(ns)
    print("\nOutlook access via Python works.")


if __name__ == "__main__":
    main()
