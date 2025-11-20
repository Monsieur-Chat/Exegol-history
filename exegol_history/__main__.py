from pathlib import Path
import sys
import tomllib
from rich.console import Console
from rich.traceback import install
from exegol_history.cli.arguments import parse_arguments
from exegol_history.cli.functions import (
    ADD_SUBCOMMAND,
    DELETE_SUBCOMMAND,
    EDIT_SUBCOMMAND,
    EXPORT_SUBCOMMAND,
    IMPORT_SUBCOMMAND,
    SET_SUBCOMMAND,
    SHOW_SUBCOMMAND,
    SYNC_SUBCOMMAND,
    UNSET_SUBCOMMAND,
    add_object,
    cli_export_objects,
    cli_import_objects,
    cli_sync_objects,
    delete_objects,
    edit_object,
    set_objects,
    show_objects,
    show_version,
    sync_objects,
    unset_objects,
    VERSION_SUBCOMMAND,
)
from exegol_history.config.config import AppConfig, ConfigTest
from sqlalchemy import exc


console = Console(soft_wrap=True)


def main():
    install(show_locals=False)

    need_config = False
    need_db = False
    config = None

    args = parse_arguments().parse_args()

    # Functions that needs the database (also need config)
    if args.command in [
        ADD_SUBCOMMAND,
        IMPORT_SUBCOMMAND,
        EDIT_SUBCOMMAND,
        EXPORT_SUBCOMMAND,
        DELETE_SUBCOMMAND,
        SET_SUBCOMMAND,
        SYNC_SUBCOMMAND,
    ]:
        need_db = True
        need_config = True
    # Functions that only need config
    elif args.command in [UNSET_SUBCOMMAND]:
        need_config = True

    if need_config:
        config = AppConfig.load_config()
        db_path = AppConfig.EXEGOL_HISTORY_HOME_FOLDER_NAME / config["paths"]["db_name"]
        db_key_path = (
            AppConfig.EXEGOL_HISTORY_HOME_FOLDER_NAME / config["paths"]["db_key_name"]
        )

        AppConfig.setup_profile(config["paths"]["profile_sh_path"])

        #tmp = Path.home() / ".exegol_history" / "config.toml"
        #with open(tmp, "rb") as config_file:
            #config_data = tomllib.load(config_file)
            #config = ConfigTest(config_data)
            #print(config.keybindings.copy_username_clipboard)

        if need_db:
            engine = AppConfig.setup_db(db_path, db_key_path)

            # Synchronise enabled connectors automatically
            if args.command != SYNC_SUBCOMMAND:
                try:
                    sync_objects(engine, config, True, True)
                except Exception:
                    pass

    try:
        # CLI
        if args.command == VERSION_SUBCOMMAND:
            show_version(console)
        elif args.command == ADD_SUBCOMMAND:
            try:
                add_object(args, engine, config)
            except exc.IntegrityError:
                console.print("[-] The credential already exist !")
        elif args.command == IMPORT_SUBCOMMAND:
            cli_import_objects(args, engine)
        elif args.command == EDIT_SUBCOMMAND:
            edit_object(args, engine, console)
        elif args.command == EXPORT_SUBCOMMAND:
            cli_export_objects(args, engine, console)
        elif args.command == DELETE_SUBCOMMAND:
            delete_objects(args, engine, console)
        elif args.command == SYNC_SUBCOMMAND:
            cli_sync_objects(engine, config, console, True, True)

        # TUI
        elif args.command == SET_SUBCOMMAND:
            set_objects(args, engine, config, console)
        elif args.command == UNSET_SUBCOMMAND:
            unset_objects(args, config)
        elif args.command == SHOW_SUBCOMMAND:
            show_objects(console)
        else:
            raise NotImplementedError("This function is not available")
    except Exception:
        console.print_exception(show_locals=True)
        sys.exit(1)
