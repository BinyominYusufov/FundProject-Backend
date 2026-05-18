from __future__ import annotations

import logging

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

DONOR_GROUP = "donor"
FUND_OWNER_GROUP = "fund_owner"
ROLE_GROUPS = (DONOR_GROUP, FUND_OWNER_GROUP)


def _perm_codenames(model_cls, codenames):
    ct = ContentType.objects.get_for_model(model_cls)
    return list(Permission.objects.filter(content_type=ct, codename__in=codenames))


def ensure_role_groups() -> None:
    """Create donor + fund_owner groups with the correct permissions.

    Idempotent. Safe to call from post_migrate.
    """
    try:
        from funds.models import Fund
        from users.models import Campaign, Donation
    except Exception as exc:
        logger.warning("[GROUPS] Skipped (models not ready): %s", exc)
        return

    donor_group, _ = Group.objects.get_or_create(name=DONOR_GROUP)
    fund_owner_group, _ = Group.objects.get_or_create(name=FUND_OWNER_GROUP)

    donor_perms = []
    donor_perms += _perm_codenames(Fund, ["view_fund"])
    donor_perms += _perm_codenames(Campaign, ["view_campaign"])
    donor_perms += _perm_codenames(Donation, ["view_donation", "add_donation"])
    donor_group.permissions.set(donor_perms)

    owner_perms = []
    owner_perms += _perm_codenames(Fund, ["view_fund", "add_fund", "change_fund"])
    owner_perms += _perm_codenames(Donation, ["view_donation"])
    fund_owner_group.permissions.set(owner_perms)


def sync_user_groups(user) -> None:
    """Remove user from all role-groups and put them in the one matching user.role."""
    from django.contrib.auth.models import Group
    from users.models import User

    # Strip every role group (and legacy FundOwners) so swaps are clean.
    legacy = ["FundOwners"]
    user.groups.remove(
        *Group.objects.filter(name__in=list(ROLE_GROUPS) + legacy)
    )

    if user.role == User.Role.DONOR:
        g, _ = Group.objects.get_or_create(name=DONOR_GROUP)
        user.groups.add(g)
    elif user.role == User.Role.FUND_OWNER:
        g, _ = Group.objects.get_or_create(name=FUND_OWNER_GROUP)
        user.groups.add(g)
        legacy_group, _ = Group.objects.get_or_create(name="FundOwners")
        user.groups.add(legacy_group)


@receiver(post_save, sender="users.User")
def _sync_groups_on_save(sender, instance, **kwargs):
    try:
        sync_user_groups(instance)
    except Exception as exc:
        logger.warning("[GROUPS] sync failed for user=%s: %s", instance.pk, exc)
