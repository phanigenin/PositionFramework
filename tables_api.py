def create_account(
    account_name: str,
    broker: str,
    broker_account_id: str | None = None,
    currency: str = "USD",
):
    from table_setup import Account, get_session

    session = get_session()

    try:
        account = Account(
            account_name=account_name,
            broker=broker,
            broker_account_id=broker_account_id,
            currency=currency,
        )

        session.add(account)
        session.commit()
        session.refresh(account)

        return account

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()

#print(create_account(account_name="Resolutrade",broker="Zerodha",broker_account_id="VVA462",currency="INR"))
#print(create_account(account_name="Phani",broker="Zerodha",broker_account_id="VJE088",currency="INR"))
#print(create_account(account_name="Janaki",broker="Zerodha",broker_account_id="FW8562",currency="INR"))
#print(create_account(account_name="Phani",broker="Schwab",broker_account_id="98811752SCHW",currency="USD"))