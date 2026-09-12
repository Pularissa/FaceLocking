from pathlib import Path


PROJECT_DIRS = [
    "data/db",
    "data/enroll",
    "models",
    "src",
]


def main():
    for directory in PROJECT_DIRS:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {path}")

    Path("src/__init__.py").touch(exist_ok=True)
    Path("README.md").touch(exist_ok=True)

    print("\nProject structure initialized successfully.")


if __name__ == "__main__":
    main()