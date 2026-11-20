"""Post balanced stock reclassifications with the inventory transaction."""

from bson import ObjectId

ACCOUNTS = {
    "PRODUCTION_WIP": ("1201", "Production work in progress", "ASSET", "DEBIT"),
    "PRODUCTION_ABSORPTION": (
        "5091",
        "Production expenses absorbed",
        "EXPENSE",
        "DEBIT",
    ),
}


def account(db, session, org, actor, key, at):
    query = dict(organization=org, system_key=key)
    existing = db.chart_of_accounts.find_one(query, session=session)
    if existing and existing.get("is_active", True):
        return existing["_id"]
    if existing or key not in ACCOUNTS:
        raise ValueError(f"Enable the {key} system account before posting production.")
    code, name, kind, balance = ACCOUNTS[key]
    if db.chart_of_accounts.find_one(
        dict(organization=org, account_code=code), session=session
    ):
        raise ValueError(
            f"Account code {code} is occupied. Configure {key} before posting."
        )
    return db.chart_of_accounts.insert_one(
        dict(
            **query,
            account_code=code,
            account_name=name,
            account_type=kind,
            normal_balance=balance,
            is_system_account=True,
            is_active=True,
            allow_manual_posting=False,
            created_by=actor,
            created_at=at,
            updated_at=at,
        ),
        session=session,
    ).inserted_id


def journal(db, session, org, actor, order, batch, at, debit, credit, value):
    if not value:
        return
    lines = []
    for key, dr, cr in [(debit, value, 0), (credit, 0, value)]:
        lines.append(
            dict(
                account=account(db, session, org, actor, key, at),
                debit=float(dr),
                credit=float(cr),
            )
        )
    db.journal_entries.insert_one(
        dict(
            organization=org,
            journal_number="MFG-" + str(ObjectId()),
            journal_date=at,
            description=f"{order['number']} · {batch}",
            source_type="MANUFACTURING",
            source_id=str(order["_id"]),
            lines=lines,
            total_debit=float(value),
            total_credit=float(value),
            status="POSTED",
            posted_at=at,
            created_at=at,
            updated_at=at,
            created_by=actor,
        ),
        session=session,
    )
