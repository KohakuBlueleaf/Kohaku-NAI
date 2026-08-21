"""
Per-model priority/permission resolution for the discord bot.

A priority table (``USER_PRIORITY`` / ``GUILD_PRIORITY``) maps an id to either:

* an ``int``  -- the same priority for every model (the original behaviour), or
* a ``dict``  -- ``{model_pattern: priority}`` for per-model priority.

Patterns are matched in this order: exact model name, then the longest matching
glob (``nai-diffusion-5-*``), then the ``"*"`` fallback. An id with no matching
entry gets no grant at all.

Since ``priority == 0`` already means "denied" when ``WHITE_LIST`` is on, a
per-model table doubles as a per-model allow list: leave a model out (or give it
0) and it is not usable. A *negative* priority on a **user** entry is a hard deny
that overrides any grant the guild would give.
"""

from fnmatch import fnmatchcase

from kohaku_nai.dc_bot_modules import config


def normalize_priority_table(raw: dict) -> dict:
    """Coerce a raw json priority table into ``{int_id: int | {str: int}}``."""
    table = {}
    for id_, entry in (raw or {}).items():
        if isinstance(entry, dict):
            entry = {str(model): int(prio) for model, prio in entry.items()}
        else:
            entry = int(entry)
        table[int(id_)] = entry
    return table


def _resolve_entry(entry, model: str) -> int | None:
    """Priority this entry grants for ``model``, or None if it grants nothing."""
    if entry is None:
        return None
    if isinstance(entry, dict):
        if model in entry:
            return entry[model]
        # Longest matching glob wins, so `nai-diffusion-5-full` beats
        # `nai-diffusion-5-*` beats `nai-diffusion-*`.
        best = None
        for pattern in entry:
            if pattern == "*" or not fnmatchcase(model, pattern):
                continue
            if best is None or len(pattern) > len(best):
                best = pattern
        if best is not None:
            return entry[best]
        return entry.get("*")
    return int(entry)


def resolve_priority(user_id: int, guild_id: int | None, model: str) -> int:
    """Effective priority for a user in a guild for one model.

    Negative means explicitly denied, 0 means no grant, positive is the queue
    priority to send to the gen server.
    """
    user_priority = _resolve_entry(config.USER_PRIORITY.get(user_id), model)
    if user_priority is not None and user_priority < 0:
        # Hard deny: the user is blocked from this model even if the guild
        # would otherwise grant it.
        return user_priority

    guild_priority = None
    if guild_id is not None:
        guild_priority = _resolve_entry(config.GUILD_PRIORITY.get(guild_id), model)

    return max(max(user_priority or 0, 0), max(guild_priority or 0, 0))


def check_permission(user_id: int, guild_id: int | None, model: str) -> tuple[bool, int]:
    """Return ``(allowed, priority)`` for one model."""
    priority = resolve_priority(user_id, guild_id, model)
    if priority < 0:
        return False, 0
    if priority == 0 and config.WHITE_LIST:
        return False, 0
    return True, priority


def allowed_models(user_id: int, guild_id: int | None, models) -> list[str]:
    """Subset of ``models`` the user may generate with."""
    return [
        model for model in models if check_permission(user_id, guild_id, model)[0]
    ]


def has_any_permission(user_id: int, guild_id: int | None, models) -> bool:
    """Whether the user may use at least one model, for an early bail-out."""
    return any(check_permission(user_id, guild_id, model)[0] for model in models)


NO_ACCESS_NOTICE = (
    "This command is not allowed for this server or user. "
    "Please contact the bot owner for more information."
)


def model_denied_notice(model: str, user_id: int, guild_id: int | None, models) -> str:
    usable = allowed_models(user_id, guild_id, models)
    notice = (
        f"You are not allowed to use `{model}`. "
        "Please contact the bot owner for more information."
    )
    if usable:
        notice += "\nModels available to you: " + ", ".join(f"`{m}`" for m in usable)
    return notice
