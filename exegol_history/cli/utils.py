import argparse
import os
import re
import shlex
import shutil
import sys
import platform
from pathlib import Path
from typing import Dict, Union
from exegol_history.config.config import AppConfig
from exegol_history.db_api.creds import Credential
from exegol_history.db_api.hosts import Host

CREDS_VARIABLES = ["USER", "PASSWORD", "NT_HASH", "DOMAIN"]
HOSTS_VARIABLES = ["IP", "TARGET", "DB_HOSTNAME", "DC_HOST", "DC_IP", "ROLE"]
# profile.sh shipped with the tool uses commented placeholders: `#export VAR='...'`
VARIABLE_REGEX_UNIX = r"#?\s*(?:export|unset)\s+([\w\d]+)(?:='([^']*)')?"
VARIABLE_REGEX_WINDOWS = r"(?:Set|Remove)-Variable -Name (\S*) (?:-Value '[^']*?' )?-Scope Global(?: -ErrorAction SilentlyContinue)?"


def check_delimiter(delimiter: str) -> str:
    if len(delimiter) != 1:
        raise argparse.ArgumentTypeError("Delimiter must be a single character.")

    return delimiter


def write_host_in_profile(host: Host, config: AppConfig):
    profile_sh_path = config.paths.profile_sh_path
    variables_correspondance = {
        HOSTS_VARIABLES[0]: host.ip,
        HOSTS_VARIABLES[1]: host.ip,
        HOSTS_VARIABLES[2]: host.hostname,
    }

    if host.role == "DC":
        variables_correspondance[HOSTS_VARIABLES[3]] = host.hostname
        variables_correspondance[HOSTS_VARIABLES[4]] = host.ip

    parse_and_update(profile_sh_path, variables_correspondance)


def write_credential_in_profile(credential: Credential, config: AppConfig):
    profile_sh_path = config.paths.profile_sh_path
    variables_correspondance = {
        CREDS_VARIABLES[0]: credential.username,
        CREDS_VARIABLES[1]: credential.password,
        CREDS_VARIABLES[2]: credential.hash,
        CREDS_VARIABLES[3]: credential.domain,
    }

    parse_and_update(profile_sh_path, variables_correspondance)


def write_target_in_profile(target: str, config: AppConfig):
    profile_sh_path = config.paths.profile_sh_path
    # Keep IP in sync with hosts flow: both point at the active target address.
    variables_correspondance = {
        HOSTS_VARIABLES[0]: target,
        HOSTS_VARIABLES[1]: target,
    }
    parse_and_update(profile_sh_path, variables_correspondance)


def parse_and_update(
    profile_sh_path: Union[str, Path], variables_correspondance: Dict[str, str]
):
    path = Path(profile_sh_path).expanduser()
    with open(path, "r") as profile:
        variables = profile.readlines()

    for i, line in enumerate(variables):
        if platform.system() == "Windows":
            tmp = re.search(VARIABLE_REGEX_WINDOWS, line)
        else:
            tmp = re.search(VARIABLE_REGEX_UNIX, line)

        if tmp:
            variable_name = tmp.group(1)

            if variable_name in variables_correspondance.keys():
                new_value = variables_correspondance[variable_name]
                if new_value:
                    if platform.system() == "Windows":
                        line = f"Set-Variable -Name {variable_name} -Value '{new_value}' -Scope Global\n"
                    else:
                        # Always write an active export so `source profile.sh` applies it.
                        line = f"export {variable_name}='{new_value}'\n"
                else:
                    if platform.system() == "Windows":
                        line = f"Remove-Variable -Name {variable_name} -Scope Global -ErrorAction SilentlyContinue\n"
                    else:
                        line = f"unset {variable_name}\n"

                variables[i] = line

    with open(path, "w") as profile:
        profile.write("".join(variables))


def console_error(message: str):
    return f"[[bold red]![/bold red]] {message}"


def console_success(message: str):
    return f"[[bold green]+[/bold green]] {message}"


def console_info(message: str):
    return f"[[bold blue]*[/bold blue]] {message}"


def try_respawn_shell_after_profile_write(config: AppConfig) -> None:
    """Replace this process with $SHELL after sourcing profile (Unix TTY only).

    A child process cannot modify the parent's environment; this is the usual
    workaround so variables from profile.sh are active immediately after the TUI.
    """
    if platform.system() == "Windows":
        return
    if os.environ.get("EXEGOL_HISTORY_NO_RESPAWN"):
        return
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return

    profile = Path(config.paths.profile_sh_path).expanduser().resolve()
    if not profile.is_file():
        return

    shell = os.environ.get("SHELL") or "/bin/bash"
    shell_path = shutil.which(shell)
    if not shell_path and os.path.isfile(shell):
        shell_path = shell
    if not shell_path:
        return

    quoted_profile = shlex.quote(str(profile))
    quoted_shell = shlex.quote(shell_path)
    # POSIX `.` loads exports; `exec` hands tty to a new interactive login shell.
    cmd = f". {quoted_profile} && exec {quoted_shell} -il"
    try:
        os.execl(shell_path, shell_path, "-c", cmd)
    except OSError:
        return
