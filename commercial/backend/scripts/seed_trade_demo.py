"""Demo trainers for the trade page. Re-running replaces these four emails.

Passwords are the same on purpose: demo-password. Do not use these accounts
for anything but a local screenshot.
"""

from data.go_catalog import EntryFlags
from services.accounts import TrainerDetails, connect, init_db, register
from services.lists import add_entry, init_lists

_PASSWORD = "demo-password"
_PEOPLE = (
    {
        "email": "avery@demo.test",
        "trainer_name": "Avery",
        "city": "Toronto",
        "trainer_level": 42,
        "team": "mystic",
        "rows": (
            ("want", "magikarp", EntryFlags(shiny=True)),
            ("have", "heracross", EntryFlags()),
        ),
    },
    {
        "email": "jordan@demo.test",
        "trainer_name": "Jordan",
        "city": "Toronto",
        "trainer_level": 37,
        "team": "valor",
        "rows": (
            ("want", "heracross", EntryFlags()),
            ("have", "magikarp", EntryFlags(shiny=True)),
        ),
    },
    {
        "email": "sam@demo.test",
        "trainer_name": "Sam",
        "city": "Montreal",
        "trainer_level": 29,
        "team": "instinct",
        "rows": (("have", "magikarp", EntryFlags(shiny=True)),),
    },
    {
        "email": "riley@demo.test",
        "trainer_name": "Riley",
        "city": "Toronto",
        "trainer_level": 51,
        "team": "mystic",
        "rows": (
            ("want", "beldum", EntryFlags(dynamax=True)),
            ("have", "kangaskhan", EntryFlags()),
        ),
    },
)


def main() -> None:
    init_lists()
    init_db()
    with connect() as conn:
        for person in _PEOPLE:
            conn.execute(
                """
                DELETE FROM list_entries
                WHERE user_id IN (SELECT id FROM users WHERE email = ?)
                """,
                (person["email"],),
            )
            conn.execute(
                """
                DELETE FROM sessions
                WHERE user_id IN (SELECT id FROM users WHERE email = ?)
                """,
                (person["email"],),
            )
            conn.execute("DELETE FROM users WHERE email = ?", (person["email"],))
    for person in _PEOPLE:
        user, _token = register(
            person["email"],
            _PASSWORD,
            TrainerDetails(
                trainer_name=person["trainer_name"],
                city=person["city"],
                friend_code=None,
                trainer_level=person["trainer_level"],
                team=person["team"],
                timezone="America/Toronto",
            ),
            True,
        )
        for kind, species_id, flags in person["rows"]:
            add_entry(user["id"], kind, flags, species_id)
        print(f"{person['trainer_name']} in {person['city']} ({person['email']})")


if __name__ == "__main__":
    main()
