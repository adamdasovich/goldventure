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


def company_subscription_active(company) -> bool:
    """True if `company` holds a live company subscription.

    Tolerates a missing row: a company that has never subscribed simply has no
    related object, which is the common case for the 396 companies nobody has
    claimed.
    """
    if company is None:
        return False
    subscription = getattr(company, 'subscription', None)
    if subscription is None:
        return False
    return bool(subscription.is_active)


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
    """
    superuser = bool(getattr(user, 'is_superuser', False)) and bool(
        getattr(user, 'is_authenticated', False)
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
        'can_edit': superuser or (rep and paid),
        'reason': reason,
        'is_representative': rep,
        'subscription_active': paid,
        'requires_subscription': rep and not paid,
    }
