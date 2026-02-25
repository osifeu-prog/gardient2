from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

Role = Literal["user", "supporter", "admin", "owner"]

ROLE_ORDER = {"user": 0, "supporter": 1, "admin": 2, "owner": 3}

@dataclass(frozen=True)
class Cmd:
    cmd: str
    desc: str
    min_role: Role = "user"
    show_in_start: bool = True
    show_in_menu: bool = True

def allowed(user_role: Role, cmd_role: Role) -> bool:
    return ROLE_ORDER[user_role] >= ROLE_ORDER[cmd_role]

def visible(cmds: List[Cmd], role: Role, *, for_start: bool, for_menu: bool) -> List[Cmd]:
    out: List[Cmd] = []
    for c in cmds:
        if not allowed(role, c.min_role):
            continue
        if for_start and not c.show_in_start:
            continue
        if for_menu and not c.show_in_menu:
            continue
        out.append(c)
    return out

# Single source of truth (UI)
COMMANDS: List[Cmd] = [
    Cmd("start", "Start / Home", "user", show_in_start=False, show_in_menu=True),
    Cmd("menu", "Show menu", "user"),
    Cmd("whoami", "User info", "user"),
    Cmd("health", "Health report", "user"),

    # Economy (public)
    Cmd("donate", "Support / donate", "user"),
    Cmd("ref", "Referral link", "user"),
    Cmd("my", "My points & requests", "user"),
    Cmd("buy", "Request token purchase", "user"),
    Cmd("claim", "Claim donation (manual verify)", "user", show_in_start=False, show_in_menu=True),

    # Infra
    Cmd("status", "Infra status", "admin"),
    Cmd("admins", "List admins", "user", show_in_start=False, show_in_menu=True),

    # Admin inbox
    Cmd("pending", "List pending requests", "admin"),
    Cmd("approve", "Approve request (admin)", "admin", show_in_start=False, show_in_menu=True),
    Cmd("reject", "Reject request (admin)", "admin", show_in_start=False, show_in_menu=True),
    Cmd("dm", "DM a user", "admin", show_in_start=False, show_in_menu=True),
    Cmd("broadcast_admins", "Broadcast to admins", "owner", show_in_start=False, show_in_menu=True),

    # Owner/system
    Cmd("admin", "Admin report", "admin", show_in_start=False, show_in_menu=True),
    Cmd("vars", "Vars (SET/MISSING)", "admin", show_in_start=False, show_in_menu=True),
    Cmd("webhook", "Webhook info", "admin", show_in_start=False, show_in_menu=True),
    Cmd("diag", "Diagnostics", "admin", show_in_start=False, show_in_menu=True),
    Cmd("pingdb", "DB ping", "admin", show_in_start=False, show_in_menu=True),
    Cmd("pingredis", "Redis ping", "admin", show_in_start=False, show_in_menu=True),
    Cmd("snapshot", "Snapshot", "admin", show_in_start=False, show_in_menu=True),
]
