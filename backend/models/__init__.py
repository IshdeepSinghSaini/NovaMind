"""
Importing all models here makes sure SQLAlchemy knows about every table
before we create them. Usage elsewhere:  from models import User, Document, ...
"""

from models.user import AccessLevel, Role, User, role_access_levels
from models.document import Department, Document, DocumentChunk, DocumentProcessingLog
from models.conversation import Conversation, Message, MessageCitation
from models.logs import AuditLog, QueryLog

__all__ = [
    "AccessLevel", "Role", "User", "role_access_levels",
    "Department", "Document", "DocumentChunk", "DocumentProcessingLog",
    "Conversation", "Message", "MessageCitation",
    "AuditLog", "QueryLog",
]
