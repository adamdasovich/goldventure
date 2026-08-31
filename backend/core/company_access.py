"""Who may edit a company's page.

Two independent conditions, and both have to hold:

1. **Identity.** ``user.company`` points at the company. That link is only set
   when a staff member approves a CompanyAccessRequest, which is the step that
   checks the person actually works there. Nobody can buy their way onto
   someone else's page.
2. **Payment.** That company holds an active CompanySubscription. Editing is
   what the company plan sells, so an approved representative whose plan has
   lapsed reads the page like anybody else.

Superusers bypass both.

Keep every editing endpoint pointed at ``can_manage_company`` rather than
re-deriving the rule. Before this module existed the check was written out by
hand in seven places across three view files, all of them testing identity
alone, and the projects endpoints tested neither - they were staff-only, so the
"+ Add Project" button a representative could see would have 403'd.
"""

import logging

logger = logging.getLogger(__name__)


# A subscription in one of these states is finished: nothing will revive it, so
# a fresh checkout is the right move. Anything else (including past_due and
# unpaid) is a live Stripe subscription that must be repaired in the billing
# portal instead — checking out again would leave the company paying twice.
DEAD_SUBSCRIPTION_STATUSES = ('canceled', 'incomplete_expired')


def company_subscription(company):
    """The company's subscription row, or None. Tolerates a missing relation."""
    if company is None:
        return None
    return getattr(company, 'subscription', None)


def company_subscription_active(company) -> bool:
    """True if `company` holds a live company subscription.

    Tolerates a missing row: a company that has never subscribed simply has no
    related object, which is the common case for the 396 companies nobody has
    claimed.
    """
    subscription = company_subscription(company)
    if subscription is None:
        return False
    return bool(subscription.is_active)


def has_live_subscription(company) -> bool:
    """True if a Stripe subscription exists that is not finished.

    Distinguishes "never subscribed" from "subscribed and the card failed".
    The second cannot be fixed with a new checkout — that just bills them
    twice — so both the API and the copy have to tell them apart.
    """
    subscription = company_subscription(company)
    if subscription is None or not subscription.stripe_subscription_id:
        return False
    return subscription.status not in DEAD_SUBSCRIPTION_STATUSES


def is_company_representative(user, company) -> bool:
    """True if `user` is the approved representative of `company`.

    Identity only - says nothing about whether the company is paying.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if company is None:
        return False
    return user.company_id == company.id


def can_manage_company(user, company) -> bool:
    """True if `user` may edit `company`'s page right now."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return (
        is_company_representative(user, company)
        and company_subscription_active(company)
    )


def access_state(user, company) -> dict:
    """The full picture, for endpoints that report rather than enforce.

    ``can_edit``             may they edit right now
    ``reason``               why, for the existing can_edit consumers
    ``is_representative``    approved for this company, paid or not
    ``subscription_active``  the company is paying
    ``requires_subscription`` approved but not paying - the one state worth a
                             prompt, since it is the only one the visitor can
                             fix by getting out a card
    ``payment_needs_attention`` approved, not paying, but a live Stripe
                             subscription exists: the card failed. They must
                             repair it in the billing portal, NOT check out
                             again, which would bill them twice.
    """
    superuser = bool(getattr(user, 'is_authenticated', False)) and bool(
        getattr(user, 'is_superuser', False)
    )
    rep = is_company_representative(user, company)
    paid = company_subscription_active(company)

    if superuser:
        reason = 'superuser'
    elif rep and paid:
        reason = 'company_representative'
    else:
        reason = None

    return {
        # Deliberately can_manage_company() and not a second copy of the rule.
        # This function used to recompute it from `superuser or (rep and paid)`,
        # which is the same thing right up until one of them is edited.
        'can_edit': can_manage_company(user, company),
        'reason': reason,
        'is_representative': rep,
        'subscription_active': paid,
        'requires_subscription': rep and not paid,
        'payment_needs_attention': rep and not paid and has_live_subscription(company),
    }
