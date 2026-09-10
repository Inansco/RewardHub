from database import get_db, init_db


init_db()

connection = get_db()


rewards = [
    ("₦500 Cash Reward", 1000, 500),
    ("₦1,000 Cash Reward", 2000, 1000),
    ("₦2,500 Cash Reward", 5000, 2500)
]


for reward in rewards:

    connection.execute(
        """
        INSERT INTO rewards
        (name, points_required, cash_value)
        VALUES (?, ?, ?)
        """,
        reward
    )


connection.commit()
connection.close()

print("Rewards added successfully.")