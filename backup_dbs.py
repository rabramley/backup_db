#!/usr/bin/python3
import tomllib
import subprocess
from pathlib import Path
from datetime import datetime


def get_config():
    config_path = Path("backup_dbs.toml")
    if not config_path.exists():
        return dict()

    with open(config_path, "rb") as f:
        return tomllib.load(f)


MYSQL_CONFIG_FILENAME=Path("backup_dbs.cnf")


def mysql_create_config(config):
    with open(MYSQL_CONFIG_FILENAME, "w") as f:
        f.write("[client]\n")
        f.write(f"host=\"{config['host']}\"\n")
        f.write(f"user=\"{config['user']}\"\n")
        f.write(f"password=\"{config['password']}\"\n")


def mysql_databases(config):
    result = subprocess.run(
        ["mysql", f"--defaults-file={MYSQL_CONFIG_FILENAME}", "-e", "SHOW DATABASES;"],
        capture_output=True,
        text=True)

    if result.returncode:
        print(result.stderr)
        return []

    not_dbs = ["Database", "information_schema", "performance_schema"]

    return [s for s in result.stdout.splitlines() if s not in not_dbs]


def backup_mysql_database(db: str, backup_dir: Path):
    print(f"Backing up {db} into '{backup_dir}'")

    backup_dir = backup_dir / db
    backup_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.sql"

    filepath = backup_dir / filename

    result = subprocess.run(
        [
            "mysqldump", 
            f"--defaults-file={MYSQL_CONFIG_FILENAME}", 
            "--force",
            "--opt",
            "--databases",
            "--events",
            "--routines",
            "--triggers",
            db,
        ],
        capture_output=True,
        text=True)

    if result.returncode:
        print(result.stderr)
        return

    with open(filepath, "w") as f:
        f.writelines(result.stdout)


def backup_mysql(config: dict, backup_dir: Path):
    print(f"Backing up MySQL server '{config['name']}'")
    mysql_create_config(config)
    backup_dir = backup_dir / config["name"]

    for db in mysql_databases(config):
        backup_mysql_database(db, backup_dir)

    MYSQL_CONFIG_FILENAME.unlink()


def backup_postgres(config: dict, backup_dir: Path):
    print(f"Backing up Postgres server '{config['name']}'")


def main():
    config = get_config()

    backup_dir = Path(config["backup_dir"])

    for s in config.get('servers', []):
        match t := s.get('type', ''):
            case 'mysql':
                backup_mysql(s, backup_dir)
            case "postgres":
                backup_postgres(s, backup_dir)
            case _:
                print(f"I don't know what a type of '{t}' is")


main()

