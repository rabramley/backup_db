#!/usr/bin/python3
import tomllib
import subprocess
from pathlib import Path


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


def backup_mysql(config):
    print(f"Backing up MySQL server '{config['name']}'")
    mysql_create_config(config)

    for db in mysql_databases(config):
        print(db)

    MYSQL_CONFIG_FILENAME.unlink()


def backup_postgres(config):
    print(f"Backing up Postgres server '{config['name']}'")


def main():
    config = get_config()

    for s in config.get('servers', []):
        match t := s.get('type', ''):
            case 'mysql':
                backup_mysql(s)
            case "postgres":
                backup_postgres(s)
            case _:
                print(f"I don't know what a type of '{t}' is")


main()

