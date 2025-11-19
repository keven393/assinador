"""
LDAP Authentication Service following OOP principles.
Implements the Single Responsibility Principle by handling only LDAP authentication.
"""
from typing import Optional, Dict, Any, List
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars
import logging
import os

logger = logging.getLogger(__name__)


class LDAPAuthenticationError(Exception):
    """Custom exception for LDAP authentication errors."""
    pass


class LDAPAuthenticator:
    """
    LDAP Authenticator class following OOP principles.
    Encapsulates all LDAP-related functionality.
    """
    
    def __init__(self):
        """Initialize LDAP authenticator with configuration."""
        self.server_url = os.environ.get('LDAP_SERVER', 'ldap://localhost')
        self.port = int(os.environ.get('LDAP_PORT', '389'))
        self.base_dn = os.environ.get('LDAP_BASE_DN', 'dc=example,dc=com')
        self.user_dn = os.environ.get('LDAP_USER_DN', 'cn=admin,dc=example,dc=com')
        self.password = os.environ.get('LDAP_PASSWORD', '')
        self.user_search_filter = os.environ.get('LDAP_USER_SEARCH_FILTER', 
                                                  '(&(objectClass=user)(sAMAccountName={username}))')
        self.username_field = os.environ.get('LDAP_USERNAME_FIELD', 'sAMAccountName')
        self.group_filter = os.environ.get('LDAP_GROUP_FILTER', '(objectClass=group)')
        self._server = None
        self._connection = None
        
        # Log das configurações (sem senha)
        logger.info(f"LDAP Config: Server={self.server_url}:{self.port}, BaseDN={self.base_dn}, UserDN={self.user_dn}")
    
    def _get_server(self) -> Server:
        """Get LDAP server instance."""
        if not self._server:
            self._server = Server(
                self.server_url,
                port=self.port,
                get_info=ALL
            )
        return self._server
    
    def _get_connection(self) -> Connection:
        """Get LDAP connection instance."""
        if not self._connection:
            server = self._get_server()
            self._connection = Connection(
                server,
                user=self.user_dn,
                password=self.password,
                auto_bind=True
            )
        return self._connection
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user against LDAP server.
        
        Args:
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            User information dictionary if authentication successful, None otherwise
            
        Raises:
            LDAPAuthenticationError: If authentication fails
        """
        try:
            connection = self._get_connection()
            
            # Search for user with filter
            user_dn = self._search_user(username)
            if not user_dn:
                logger.warning(f"User not found in LDAP or doesn't match filter: {username}")
                return None
            
            # Attempt to bind with user credentials
            user_connection = Connection(
                self._get_server(),
                user=user_dn,
                password=password,
                auto_bind=True
            )
            
            # Get user attributes
            user_info = self._get_user_info(connection, user_dn)
            user_connection.unbind()
            
            logger.info(f"User authenticated successfully: {username}")
            return user_info
            
        except LDAPException as e:
            logger.error(f"LDAP authentication error for user {username}: {str(e)}")
            raise LDAPAuthenticationError(f"Authentication failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during LDAP authentication: {str(e)}")
            raise LDAPAuthenticationError(f"Authentication failed: {str(e)}")
    
    def check_user_in_filter(self, username: str) -> bool:
        """
        Check if a user exists in LDAP and matches the search filter.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists and matches filter, False otherwise
        """
        try:
            user_dn = self._search_user(username)
            return user_dn is not None
        except Exception as e:
            logger.error(f"Error checking user {username} in LDAP filter: {str(e)}")
            return False
    
    def _search_user(self, username: str) -> Optional[str]:
        """
        Search for user DN in LDAP.
        
        Args:
            username: Username to search for
            
        Returns:
            User DN if found, None otherwise
        """
        try:
            connection = self._get_connection()
            # Escape LDAP filter characters to prevent injection attacks
            escaped_username = escape_filter_chars(username)
            search_filter = self.user_search_filter.format(username=escaped_username)
            
            connection.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['sAMAccountName']
            )
            
            if connection.entries:
                return str(connection.entries[0].entry_dn)
            
            return None
            
        except LDAPException as e:
            logger.error(f"LDAP search error for user {username}: {str(e)}")
            return None
    
    def _get_user_info(self, connection: Connection, user_dn: str) -> Dict[str, Any]:
        """
        Get user information from Active Directory.
        
        Args:
            connection: LDAP connection
            user_dn: User distinguished name
            
        Returns:
            Dictionary containing user information
        """
        try:
            # Search for user with specific attributes
            connection.search(
                search_base=user_dn,
                search_filter='(objectClass=*)',
                search_scope=SUBTREE,
                attributes=[
                    'sAMAccountName', 'mail', 'displayName', 'cn', 'uid',
                    'title', 'department', 'departmentNumber', 'telephoneNumber',
                    'mobile', 'l', 'st', 'postalCode', 'co', 'streetAddress',
                    'homePhone', 'postalAddress', 'facsimileTelephoneNumber',
                    'pager', 'userAccountControl'
                ]
            )
            
            if connection.entries:
                entry = connection.entries[0]
                
                def get_attr(attr_name):
                    """Helper to safely get attribute value."""
                    if hasattr(entry, attr_name):
                        val = getattr(entry, attr_name)
                        if val and hasattr(val, 'value'):
                            return str(val.value) if val.value else ''
                        elif val:
                            return str(val)
                    return ''
                
                return {
                    'username': get_attr('sAMAccountName'),
                    'email': get_attr('mail'),
                    'full_name': get_attr('displayName') or get_attr('cn'),
                    'department': get_attr('department') or get_attr('departmentNumber'),
                    'position': get_attr('title'),
                    'phone': get_attr('telephoneNumber'),
                    'mobile': get_attr('mobile'),
                    'city': get_attr('l'),
                    'state': get_attr('st'),
                    'postal_code': get_attr('postalCode'),
                    'country': get_attr('co'),
                    'street_address': get_attr('streetAddress'),
                    'home_phone': get_attr('homePhone'),
                    'work_address': get_attr('postalAddress'),
                    'fax': get_attr('facsimileTelephoneNumber'),
                    'pager': get_attr('pager'),
                    'ldap_dn': user_dn,
                    'user_account_control': get_attr('userAccountControl')
                }
            
            return {}
            
        except LDAPException as e:
            logger.error(f"Error getting user info for {user_dn}: {str(e)}")
            return {}
    
    def validate_credentials(self, username: str, password: str) -> bool:
        """
        Validate user credentials without returning user info.
        
        Args:
            username: Username to validate
            password: Password to validate
            
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            user_info = self.authenticate(username, password)
            return user_info is not None
        except LDAPAuthenticationError:
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users from AD that match the user search filter.
        
        Returns:
            List of user information dictionaries
        """
        try:
            connection = self._get_connection()
            
            # Use the base filter without username placeholder
            base_filter = self.user_search_filter.replace("(sAMAccountName={username})", "")
            if base_filter.endswith(")"):
                base_filter = base_filter[:-1]
            base_filter += ")"
            
            connection.search(
                search_base=self.base_dn,
                search_filter=base_filter,
                search_scope=SUBTREE,
                attributes=[
                    'sAMAccountName', 'mail', 'displayName', 'cn', 'uid',
                    'title', 'department', 'departmentNumber', 'telephoneNumber',
                    'mobile', 'l', 'st', 'postalCode', 'co', 'streetAddress',
                    'homePhone', 'postalAddress', 'facsimileTelephoneNumber',
                    'pager', 'userAccountControl'
                ]
            )
            
            users = []
            for entry in connection.entries:
                def get_attr(attr_name):
                    """Helper to safely get attribute value."""
                    if hasattr(entry, attr_name):
                        val = getattr(entry, attr_name)
                        if val and hasattr(val, 'value'):
                            return str(val.value) if val.value else ''
                        elif val:
                            return str(val)
                    return ''
                
                username = get_attr('sAMAccountName')
                if not username:
                    continue
                    
                user_info = {
                    'username': username,
                    'email': get_attr('mail'),
                    'full_name': get_attr('displayName') or get_attr('cn'),
                    'department': get_attr('department') or get_attr('departmentNumber'),
                    'position': get_attr('title'),
                    'phone': get_attr('telephoneNumber'),
                    'mobile': get_attr('mobile'),
                    'city': get_attr('l'),
                    'state': get_attr('st'),
                    'postal_code': get_attr('postalCode'),
                    'country': get_attr('co'),
                    'street_address': get_attr('streetAddress'),
                    'home_phone': get_attr('homePhone'),
                    'work_address': get_attr('postalAddress'),
                    'fax': get_attr('facsimileTelephoneNumber'),
                    'pager': get_attr('pager'),
                    'ldap_dn': str(entry.entry_dn),
                    'user_account_control': get_attr('userAccountControl')
                }
                users.append(user_info)
            
            logger.info(f"Found {len(users)} users in AD matching filter")
            return users
            
        except LDAPException as e:
            logger.error(f"Error getting all users from LDAP: {str(e)}")
            return []
    
    @staticmethod
    def is_account_enabled(user_account_control: int) -> bool:
        """
        Check if AD account is enabled based on userAccountControl value.
        
        Args:
            user_account_control: The userAccountControl value from AD
            
        Returns:
            True if account is enabled, False otherwise
        """
        if user_account_control is None:
            return False
        
        # Check if bit 2 (ACCOUNTDISABLE) is set
        ACCOUNTDISABLE = 0x0002
        return (user_account_control & ACCOUNTDISABLE) == 0
    
    def close_connection(self):
        """Close LDAP connection."""
        if self._connection:
            try:
                self._connection.unbind()
                self._connection = None
            except Exception as e:
                logger.error(f"Error closing LDAP connection: {str(e)}")
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close_connection()

