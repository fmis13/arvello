"""
Template tags and filters for user-related functionality.

Provides filters to display user names with academic titles,
following Croatian academic title conventions:
- Pre-Bologna titles (left): "dr. sc. Ivan Horvat"
- Bologna titles (right): "Ivan Horvat, bacc. oec."
"""
from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.filter
def full_name_with_title(user):
    """
    Returns the user's full name with academic title positioned correctly.
    
    Usage in templates:
        {{ request.user|full_name_with_title }}
        {{ user|full_name_with_title }}
    
    Args:
        user: User instance
        
    Returns:
        str: Formatted name with title, or just the name if no title/profile
    """
    if not user or not hasattr(user, 'pk') or user.pk is None:
        return ''
    
    try:
        # Try to get the user's profile
        if hasattr(user, 'profile') and user.profile:
            return user.profile.get_full_name_with_title()
    except Exception:
        pass
    
    # Fallback to standard get_full_name or username
    return user.get_full_name() or user.username


@register.filter
def user_name_only(user):
    """
    Returns just the user's name without academic title.
    
    Usage in templates:
        {{ request.user|user_name_only }}
    
    Args:
        user: User instance
        
    Returns:
        str: Name without title
    """
    if not user or not hasattr(user, 'pk') or user.pk is None:
        return ''
    
    try:
        if hasattr(user, 'profile') and user.profile:
            return user.profile.get_name_only()
    except Exception:
        pass
    
    return user.get_full_name() or user.username


@register.filter
def academic_title(user):
    """
    Returns just the user's academic title.
    
    Usage in templates:
        {{ request.user|academic_title }}
    
    Args:
        user: User instance
        
    Returns:
        str: Academic title or empty string
    """
    if not user or not hasattr(user, 'pk') or user.pk is None:
        return ''
    
    try:
        if hasattr(user, 'profile') and user.profile:
            return user.profile.get_academic_title_display_value()
    except Exception:
        pass
    
    return ''


@register.simple_tag
def get_user_display_name(user, include_title=True):
    """
    Returns the user's display name, optionally with academic title.
    
    Usage in templates:
        {% get_user_display_name request.user %}
        {% get_user_display_name user include_title=False %}
    
    Args:
        user: User instance
        include_title: Whether to include academic title (default: True)
        
    Returns:
        str: Formatted name (with or without title based on parameter)
    """
    if not user or not hasattr(user, 'pk') or user.pk is None:
        return ''
    
    if include_title:
        return full_name_with_title(user)
    else:
        return user_name_only(user)
