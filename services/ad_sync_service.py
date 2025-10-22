"""
Active Directory Synchronization Service.
Handles periodic synchronization of users from AD to the database.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from models import db, User
from .ldap_service import LDAPAuthenticator

logger = logging.getLogger(__name__)


class ADSyncService:
    """
    Service for synchronizing users from Active Directory to the database.
    """
    
    def __init__(self, db_session=None):
        """
        Initialize AD sync service.
        
        Args:
            db_session: Optional database session. If not provided, uses global db.
        """
        self.db = db_session or db
        self.ldap_authenticator = LDAPAuthenticator()
    
    def sync_all_users(self) -> Dict[str, Any]:
        """
        Synchronize all users from Active Directory to the database.
        
        This method:
        1. Fetches all users from AD matching the filter
        2. Checks userAccountControl status for each user
        3. Creates/updates users in database
        4. Marks users as inactive if:
           - No longer in AD filter
           - AD account is disabled
        5. Updates user information (department, etc.)
        
        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'total_ad_users': 0,
            'users_created': 0,
            'users_updated': 0,
            'users_deactivated': 0,
            'users_reactivated': 0,
            'errors': []
        }
        
        try:
            # Get all users from AD
            ad_users = self.ldap_authenticator.get_all_users()
            stats['total_ad_users'] = len(ad_users)
            
            if not ad_users:
                logger.warning("No users found in Active Directory matching the filter")
                return stats
            
            # Track AD usernames for deactivation check
            ad_usernames = set()
            
            # Process each AD user
            for ad_user_info in ad_users:
                try:
                    username = ad_user_info.get('username')
                    if not username:
                        continue
                    
                    ad_usernames.add(username)
                    
                    # Check if account is enabled in AD
                    uac = ad_user_info.get('user_account_control')
                    if uac:
                        try:
                            uac_int = int(uac)
                        except (ValueError, TypeError):
                            uac_int = None
                    else:
                        uac_int = None
                    
                    is_enabled = self.ldap_authenticator.is_account_enabled(uac_int) if uac_int else True
                    
                    # Get or create user in database
                    result = self._sync_user(ad_user_info, is_enabled)
                    
                    if result == 'created':
                        stats['users_created'] += 1
                    elif result == 'updated':
                        stats['users_updated'] += 1
                    elif result == 'reactivated':
                        stats['users_reactivated'] += 1
                    elif result == 'deactivated':
                        stats['users_deactivated'] += 1
                        
                except Exception as e:
                    error_msg = f"Error syncing user {ad_user_info.get('username', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            
            # Deactivate users not found in AD
            deactivated_count = self._deactivate_missing_users(ad_usernames)
            stats['users_deactivated'] += deactivated_count
            
            # Commit all changes
            self.db.session.commit()
            
            logger.info(
                f"AD Sync completed - Created: {stats['users_created']}, "
                f"Updated: {stats['users_updated']}, "
                f"Reactivated: {stats['users_reactivated']}, "
                f"Deactivated: {stats['users_deactivated']}, "
                f"Errors: {len(stats['errors'])}"
            )
            
        except Exception as e:
            error_msg = f"Fatal error during AD sync: {str(e)}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            self.db.session.rollback()
        
        return stats
    
    def _sync_user(self, ad_user_info: Dict[str, Any], is_enabled: bool) -> str:
        """
        Sync a single user from AD to database.
        
        Args:
            ad_user_info: User information from AD
            is_enabled: Whether the AD account is enabled
            
        Returns:
            Status: 'created', 'updated', 'reactivated', 'deactivated', or 'unchanged'
        """
        username = ad_user_info.get('username')
        email = ad_user_info.get('email')
        
        # Generate default email if not provided
        if not email:
            email = f"{username}@psc.local"
            ad_user_info['email'] = email
        
        # Generate default full_name if not provided
        full_name = ad_user_info.get('full_name')
        if not full_name or full_name.strip() == '':
            full_name = username.title()
            ad_user_info['full_name'] = full_name
        
        # Find existing user
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Update existing user
            was_active = user.is_active
            should_be_active = is_enabled
            
            # Update user fields
            user.email = email
            user.full_name = full_name
            
            # NÃO altera o status is_active automaticamente
            # Apenas desativa se a conta foi desabilitada no AD
            if not is_enabled and was_active:
                # Conta desabilitada no AD - desativa no sistema
                user.is_active = False
                logger.warning(f"Deactivating user {username} - account disabled in AD")
                return 'deactivated'
            elif not is_enabled and not was_active:
                # Já estava inativo e continua inativo no AD
                return 'updated'
            elif is_enabled and was_active:
                # Já estava ativo e continua ativo no AD
                return 'updated'
            else:
                # is_enabled=True e was_active=False
                # Mantém inativo - admin desativou manualmente
                logger.info(f"User {username} remains inactive - admin must manually activate")
                return 'updated'
        else:
            # Create new user (SEM PERMISSÕES - admin must set later)
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                role='user',  # Sem permissões por padrão
                is_active=False,  # SEMPRE INATIVO até admin aprovar
                is_ldap_user=True,
                must_change_password=False,
                ldap_dn=ad_user_info.get('ldap_dn'),
                department=ad_user_info.get('department'),
                position=ad_user_info.get('position'),
                phone=ad_user_info.get('phone'),
                mobile=ad_user_info.get('mobile'),
                city=ad_user_info.get('city'),
                state=ad_user_info.get('state'),
                postal_code=ad_user_info.get('postal_code'),
                country=ad_user_info.get('country'),
                street_address=ad_user_info.get('street_address'),
                home_phone=ad_user_info.get('home_phone'),
                work_address=ad_user_info.get('work_address'),
                fax=ad_user_info.get('fax'),
                pager=ad_user_info.get('pager')
            )
            self.db.session.add(user)
            logger.info(f"Creating new user {username} (INACTIVE - awaiting admin approval)")
            return 'created'
    
    def _deactivate_missing_users(self, ad_usernames: set) -> int:
        """
        Deactivate users in database that are no longer in AD.
        
        Args:
            ad_usernames: Set of usernames found in AD
            
        Returns:
            Number of users deactivated
        """
        # Find active users in DB that are not in AD
        active_db_users = User.query.filter_by(is_active=True).all()
        
        deactivated_count = 0
        for user in active_db_users:
            if user.username not in ad_usernames:
                logger.warning(
                    f"Deactivating user {user.username} - no longer found in AD or doesn't match filter"
                )
                user.is_active = False
                deactivated_count += 1
        
        return deactivated_count
    
    def sync_single_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Synchronize a single user from AD.
        
        Args:
            username: Username to sync
            
        Returns:
            Dictionary with sync result or None if user not found in AD
        """
        try:
            # Check if user exists in AD
            user_dn = self.ldap_authenticator._search_user(username)
            if not user_dn:
                logger.warning(f"User {username} not found in AD")
                return None
            
            # Get user info from AD
            connection = self.ldap_authenticator._get_connection()
            ad_user_info = self.ldap_authenticator._get_user_info(connection, user_dn)
            
            if not ad_user_info:
                return None
            
            # Check if account is enabled
            uac = ad_user_info.get('user_account_control')
            uac_int = int(uac) if uac else None
            is_enabled = self.ldap_authenticator.is_account_enabled(uac_int) if uac_int else True
            
            # Sync user
            result = self._sync_user(ad_user_info, is_enabled)
            self.db.session.commit()
            
            return {
                'username': username,
                'status': result,
                'is_active': is_enabled
            }
            
        except Exception as e:
            logger.error(f"Error syncing single user {username}: {str(e)}")
            self.db.session.rollback()
            return None

