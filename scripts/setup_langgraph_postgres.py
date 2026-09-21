from app.persistence.postgres_checkpointer import (
    get_postgres_checkpointer,
)


def main() -> None:
    print("Connecting to PostgreSQL...")

    with get_postgres_checkpointer() as checkpointer:
        print("Creating LangGraph checkpoint tables...")
        checkpointer.setup()

    print(
        "LangGraph PostgreSQL checkpoint setup completed."
    )


if __name__ == "__main__":
    main()