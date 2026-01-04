import logging
from django.utils.text import slugify
from uuid import uuid4
from .models import Company, SubjectMembership, UserProfile

logger = logging.getLogger(__name__)


def _generate_client_unique_id():
    import random
    for _ in range(10000):
        candidate = f"{random.randint(0,9999):04d}"
        if not Company.objects.filter(clientUniqueId=candidate).exists():
            return candidate
    return str(int(uuid4().int % 10000)).zfill(4)


def ensure_user_has_subject(user):
    """Ensure the given user has an active_subject (Company). Return the Company.

    - If user.profile.active_subject exists and is present in DB -> return it
    - Else try to find a SubjectMembership for the user and use that company
    - Else create a minimal Company, SubjectMembership (OWNER) and set profile.active_subject
    """
    profile = getattr(user, 'profile', None)
    # if profile exists and active_subject set and still exists -> return
    if profile and profile.active_subject_id:
        try:
            subj = profile.active_subject
            if subj is not None:
                return subj
        except Company.DoesNotExist:
            logger.debug('active_subject referenced on profile but does not exist')

    # try to find any membership
    membership = SubjectMembership.objects.filter(user=user).select_related('company').first()
    if membership:
        company = membership.company
        if profile:
            # keep both active_subject and active_company in sync for backward compatibility
            profile.active_subject = company
            try:
                # if the profile has active_company field, set it as well
                profile.active_company = company
                profile.save(update_fields=['active_subject', 'active_company'])
            except Exception:
                profile.save(update_fields=['active_subject'])
        return company

    # create minimal company
    name = (getattr(user, 'get_full_name', None) and user.get_full_name()) or getattr(user, 'username', 'subject')
    unique_id = _generate_client_unique_id()
    company = Company.objects.create(
        clientName=(name[:200] if name else 'Untitled'),
        addressLine1='',
        town='',
        province='GRAD ZAGREB',
        postalCode='10000',
        phoneNumber='',
        emailAddress=(getattr(user, 'email', '') or ''),
        clientUniqueId=unique_id,
        clientType='Pravna osoba'
    )

    # create membership
    SubjectMembership.objects.create(user=user, company=company, role=SubjectMembership.ROLE_OWNER)

    # set profile.active_subject and active_company (if present)
    if profile:
        profile.active_subject = company
        try:
            profile.active_company = company
            profile.save(update_fields=['active_subject', 'active_company'])
        except Exception:
            profile.save(update_fields=['active_subject'])

    logger.info(f"Assigned new subject {company} to user {user}")
    return company
