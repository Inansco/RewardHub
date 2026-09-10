from database import get_db, init_db


init_db()

connection = get_db()


tasks = [
    (
        "Welcome to RewardHub",
        "Complete this simple welcome task.",
        50
    ),
    (
        "RewardHub Quiz",
        "Answer our beginner quiz.",
        100
    ),
    (
        "Daily Check-in",
        "Check in today and receive your daily bonus.",
        25
    )
]


for task in tasks:

    connection.execute(
        """
        INSERT INTO tasks (title, description, points)
        VALUES (?, ?, ?)
        """,
        task
    )


connection.commit()
connection.close()

print("Tasks added successfully.")