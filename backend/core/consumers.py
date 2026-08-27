"""
WebSocket consumers for real-time forum and guest speaker sessions.

This module implements the WebSocket consumers that handle real-time
communication for the forum discussion and guest speaker Q&A features.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models as django_models

from core.models import (
    ForumDiscussion,
    ForumMessage,
    UserPresence,
    GuestSpeakerSession,
    SessionQuestion,
    SessionModerator,
    SessionSpeaker,
    SessionParticipant,
    QuestionUpvote,
    SpeakerEvent,
    EventRegistration,
    EventQuestion,
    EventReaction,
    PropertyInquiry,
    InquiryMessage,
)

User = get_user_model()
logger = logging.getLogger(__name__)


async def _cache_rate_limit(user_id: int, scope: str, limit: int = 10, window: int = 60) -> bool:
    """Generic cache-based rate limiter. Returns True if within limits."""
    from django.core.cache import cache
    key = f'ws_rate:{scope}:{user_id}'
    count = cache.get(key, 0)
    if count >= limit:
        return False
    cache.set(key, count + 1, window)
    return True


class ForumConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time forum discussions.

    Handles message broadcasting, typing indicators, and user presence.
    """

    async def connect(self):
        """
        Handle WebSocket connection.

        - Extract discussion ID from URL
        - Authenticate user
        - Verify access permissions
        - Join discussion channel group
        - Update user presence
        - Send initial state
        """
        self.discussion_id = self.scope['url_route']['kwargs']['discussion_id']
        self.discussion_group_name = f'forum_{self.discussion_id}'
        self.user = self.scope.get('user')

        # Authenticate user
        if not self.user or not self.user.is_authenticated:
            logger.warning(f"Unauthenticated connection attempt to discussion {self.discussion_id}")
            await self.close(code=4001)
            return

        # Verify discussion exists and user has access
        discussion = await self.get_discussion()
        if not discussion:
            logger.warning(f"User {self.user.id} attempted to join non-existent discussion {self.discussion_id}")
            await self.close(code=4004)
            return

        has_access = await self.check_discussion_access(discussion)
        if not has_access:
            logger.warning(f"User {self.user.id} denied access to discussion {self.discussion_id}")
            await self.close(code=4003)
            return

        # Accept connection
        await self.accept()

        # Join discussion channel group
        await self.channel_layer.group_add(
            self.discussion_group_name,
            self.channel_name
        )

        # Update user presence
        await self.update_presence(is_online=True)

        # Broadcast user joined event
        await self.channel_layer.group_send(
            self.discussion_group_name,
            {
                'type': 'user_joined',
                'user': await self.get_user_data(self.user),
                'timestamp': timezone.now().isoformat(),
            }
        )

        # Send initial state to connected client
        await self.send_initial_state()

        logger.info(f"User {self.user.id} connected to discussion {self.discussion_id}")

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        - Update user presence (offline)
        - Clear typing indicator
        - Broadcast user left event
        - Leave channel group
        """
        if hasattr(self, 'discussion_group_name') and self.user and self.user.is_authenticated:
            # Update presence
            await self.update_presence(is_online=False, is_typing=False)

            # Broadcast user left
            await self.channel_layer.group_send(
                self.discussion_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'timestamp': timezone.now().isoformat(),
                }
            )

            # Leave group
            await self.channel_layer.group_discard(
                self.discussion_group_name,
                self.channel_name
            )

            logger.info(f"User {self.user.id} disconnected from discussion {self.discussion_id}")

    async def receive(self, text_data):
        """
        Route incoming WebSocket messages to appropriate handlers.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            # Route to appropriate handler
            handlers = {
                'message.send': self.handle_message_send,
                'message.edit': self.handle_message_edit,
                'message.delete': self.handle_message_delete,
                'typing.start': self.handle_typing_start,
                'typing.stop': self.handle_typing_stop,
                'presence.update': self.handle_presence_update,
            }

            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await self.send_error("Internal server error")

    # ========================================================================
    # MESSAGE HANDLERS
    # ========================================================================

    async def handle_message_send(self, data: Dict[str, Any]):
        """
        Handle sending a new message.

        - Validate content
        - Check rate limiting
        - Save to database
        - Broadcast to all participants
        - Clear typing indicator
        """
        content = data.get('content', '').strip()
        reply_to_id = data.get('reply_to')

        # Validate
        if not content:
            await self.send_error("Message content is required")
            return

        if len(content) > 5000:
            await self.send_error("Message too long (max 5000 characters)")
            return

        # Check rate limiting
        rate_ok = await self.check_rate_limit()
        if not rate_ok:
            await self.send_error("Rate limit exceeded. Please slow down.")
            return

        # Save message
        message = await self.save_message(content, reply_to_id)

        if message:
            # Clear typing indicator
            await self.update_presence(is_typing=False)

            # Broadcast message
            await self.channel_layer.group_send(
                self.discussion_group_name,
                {
                    'type': 'message_new',
                    'message': await self.serialize_message(message),
                }
            )

            logger.info(f"User {self.user.id} sent message {message.id} in discussion {self.discussion_id}")

    async def handle_message_edit(self, data: Dict[str, Any]):
        """
        Handle editing an existing message.
        """
        message_id = data.get('message_id')
        new_content = data.get('content', '').strip()

        if not message_id or not new_content:
            await self.send_error("Message ID and content are required")
            return

        # Update message
        message = await self.edit_message(message_id, new_content)

        if message:
            # Broadcast update
            await self.channel_layer.group_send(
                self.discussion_group_name,
                {
                    'type': 'message_edited',
                    'message': await self.serialize_message(message),
                }
            )

            logger.info(f"User {self.user.id} edited message {message_id}")
        else:
            await self.send_error("Failed to edit message. You may not have permission.")

    async def handle_message_delete(self, data: Dict[str, Any]):
        """
        Handle soft-deleting a message.
        """
        message_id = data.get('message_id')

        if not message_id:
            await self.send_error("Message ID is required")
            return

        # Delete message (soft delete)
        success = await self.delete_message(message_id)

        if success:
            # Broadcast deletion
            await self.channel_layer.group_send(
                self.discussion_group_name,
                {
                    'type': 'message_deleted',
                    'message_id': message_id,
                    'timestamp': timezone.now().isoformat(),
                }
            )

            logger.info(f"User {self.user.id} deleted message {message_id}")
        else:
            await self.send_error("Failed to delete message. You may not have permission.")

    # ========================================================================
    # TYPING INDICATOR HANDLERS
    # ========================================================================

    async def handle_typing_start(self, data: Dict[str, Any]):
        """Handle user started typing."""
        await self.update_presence(is_typing=True)

        # Broadcast to others
        await self.channel_layer.group_send(
            self.discussion_group_name,
            {
                'type': 'typing_indicator',
                'user': await self.get_user_data(self.user),
                'is_typing': True,
            }
        )

    async def handle_typing_stop(self, data: Dict[str, Any]):
        """Handle user stopped typing."""
        await self.update_presence(is_typing=False)

        # Broadcast to others
        await self.channel_layer.group_send(
            self.discussion_group_name,
            {
                'type': 'typing_indicator',
                'user': await self.get_user_data(self.user),
                'is_typing': False,
            }
        )

    async def handle_presence_update(self, data: Dict[str, Any]):
        """
        Handle presence heartbeat.

        Clients should send this every 30 seconds to maintain online status.
        """
        await self.update_presence(is_online=True)

    # ========================================================================
    # CHANNEL LAYER EVENT RECEIVERS
    # ========================================================================

    async def user_joined(self, event):
        """Broadcast when a user joins the discussion."""
        await self.send(text_data=json.dumps({
            'type': 'user.joined',
            'user': event['user'],
            'timestamp': event['timestamp'],
        }))

    async def user_left(self, event):
        """Broadcast when a user leaves the discussion."""
        await self.send(text_data=json.dumps({
            'type': 'user.left',
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
        }))

    async def message_new(self, event):
        """Broadcast new message to all participants."""
        await self.send(text_data=json.dumps({
            'type': 'message.new',
            'message': event['message'],
        }))

    async def message_edited(self, event):
        """Broadcast message edit to all participants."""
        await self.send(text_data=json.dumps({
            'type': 'message.edited',
            'message': event['message'],
        }))

    async def message_deleted(self, event):
        """Broadcast message deletion to all participants."""
        await self.send(text_data=json.dumps({
            'type': 'message.deleted',
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))

    async def typing_indicator(self, event):
        """Broadcast typing indicator (exclude sender)."""
        # Don't send typing indicators back to the sender
        if event['user']['id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing.indicator',
                'user': event['user'],
                'is_typing': event['is_typing'],
            }))

    # ========================================================================
    # DATABASE OPERATIONS (async wrappers)
    # ========================================================================

    @database_sync_to_async
    def get_discussion(self) -> Optional[ForumDiscussion]:
        """Fetch discussion from database."""
        try:
            return ForumDiscussion.objects.select_related('company').get(
                id=self.discussion_id,
                is_active=True
            )
        except ForumDiscussion.DoesNotExist:
            return None

    @database_sync_to_async
    def check_discussion_access(self, discussion: ForumDiscussion) -> bool:
        """
        Check if user has access to this discussion.

        Rules:
        - Active discussions: Any authenticated user
        - Archived discussions: Only superusers
        - Inactive discussions: No access
        """
        if not discussion.is_active:
            return False

        if discussion.is_archived and not self.user.is_superuser:
            return False

        # All authenticated users can access active discussions
        return True

    @database_sync_to_async
    def update_presence(self, is_online: bool = True, is_typing: bool = False):
        """Update or create user presence."""
        # Skip if user is not authenticated
        if not self.user or not self.user.is_authenticated:
            logger.debug("Skipping presence update for unauthenticated user")
            return

        # Skip if discussion_id is invalid (e.g., 0 or None)
        if not self.discussion_id or self.discussion_id == 0:
            logger.warning(f"Attempted to update presence with invalid discussion_id: {self.discussion_id}")
            return

        UserPresence.objects.update_or_create(
            user=self.user,
            discussion_id=self.discussion_id,
            defaults={
                'is_online': is_online,
                'is_typing': is_typing,
                'connection_id': self.channel_name,
            }
        )

    @database_sync_to_async
    def save_message(self, content: str, reply_to_id: Optional[int] = None) -> Optional[ForumMessage]:
        """Save message to database."""
        try:
            message = ForumMessage.objects.create(
                discussion_id=self.discussion_id,
                user=self.user,
                content=content,
                reply_to_id=reply_to_id,
            )

            # Update discussion stats
            discussion = ForumDiscussion.objects.get(id=self.discussion_id)
            discussion.message_count = ForumMessage.objects.filter(
                discussion_id=self.discussion_id,
                is_deleted=False
            ).count()
            discussion.last_message_at = timezone.now()
            discussion.save(update_fields=['message_count', 'last_message_at', 'updated_at'])

            return message
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def edit_message(self, message_id: int, new_content: str) -> Optional[ForumMessage]:
        """Edit an existing message (user must own it)."""
        try:
            message = ForumMessage.objects.get(
                id=message_id,
                user=self.user,
                is_deleted=False
            )
            message.content = new_content
            message.is_edited = True
            message.edited_at = timezone.now()
            message.save(update_fields=['content', 'is_edited', 'edited_at'])
            return message
        except ForumMessage.DoesNotExist:
            return None

    @database_sync_to_async
    def delete_message(self, message_id: int) -> bool:
        """Soft delete a message (user must own it or be moderator)."""
        try:
            message = ForumMessage.objects.get(id=message_id, is_deleted=False)

            # Refresh user from database to get current permissions
            fresh_user = User.objects.get(id=self.user.id)

            # Debug logging
            logger.info(f"[DELETE_DEBUG] message_id={message_id}, message.user_id={message.user_id}")
            logger.info(f"[DELETE_DEBUG] fresh_user.id={fresh_user.id}, user_type='{fresh_user.user_type}', is_superuser={fresh_user.is_superuser}")

            # Check permissions - user owns message OR is admin/superuser
            can_delete = (
                message.user_id == fresh_user.id or
                fresh_user.user_type == 'admin' or
                fresh_user.is_superuser
            )
            logger.info(f"[DELETE_DEBUG] can_delete={can_delete}")

            if can_delete:
                message.is_deleted = True
                message.deleted_at = timezone.now()
                message.deleted_by = fresh_user
                message.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

                # Update discussion message count
                discussion = ForumDiscussion.objects.get(id=self.discussion_id)
                discussion.message_count = ForumMessage.objects.filter(
                    discussion_id=self.discussion_id,
                    is_deleted=False
                ).count()
                discussion.save(update_fields=['message_count', 'updated_at'])

                return True
            return False
        except ForumMessage.DoesNotExist:
            logger.info(f"[DELETE_DEBUG] Message {message_id} not found or already deleted")
            return False

    @database_sync_to_async
    def check_rate_limit(self) -> bool:
        """
        Check if user is within rate limits.

        Limit: 10 messages per minute
        """
        one_minute_ago = timezone.now() - timezone.timedelta(minutes=1)
        recent_message_count = ForumMessage.objects.filter(
            user=self.user,
            discussion_id=self.discussion_id,
            created_at__gte=one_minute_ago
        ).count()

        return recent_message_count < 10

    @database_sync_to_async
    def serialize_message(self, message: ForumMessage) -> Dict[str, Any]:
        """Serialize message for WebSocket transmission."""
        return {
            'id': message.id,
            'content': message.content,
            'user': {
                'id': message.user.id,
                'username': message.user.username,
                'full_name': message.user.get_full_name() or message.user.username,
                'user_type': message.user.user_type,
            },
            'reply_to': message.reply_to_id,
            'is_edited': message.is_edited,
            'edited_at': message.edited_at.isoformat() if message.edited_at else None,
            'is_pinned': message.is_pinned,
            'is_highlighted': message.is_highlighted,
            'created_at': message.created_at.isoformat(),
        }

    @database_sync_to_async
    def get_user_data(self, user: User) -> Dict[str, Any]:
        """Serialize user data for WebSocket transmission."""
        return {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'user_type': user.user_type,
        }

    @database_sync_to_async
    def get_online_users(self) -> list:
        """Get list of currently online users."""
        presences = UserPresence.objects.filter(
            discussion_id=self.discussion_id,
            is_online=True
        ).select_related('user')

        return [{
            'id': p.user.id,
            'username': p.user.username,
            'full_name': p.user.get_full_name() or p.user.username,
            'is_typing': p.is_typing,
        } for p in presences]

    @database_sync_to_async
    def get_recent_messages(self, limit: int = 50) -> list:
        """Get recent messages for initial state."""
        messages = ForumMessage.objects.filter(
            discussion_id=self.discussion_id,
            is_deleted=False
        ).select_related('user').order_by('-created_at')[:limit]

        # Reverse to get chronological order
        messages = list(reversed(messages))

        return [{
            'id': m.id,
            'content': m.content,
            'user': {
                'id': m.user.id,
                'username': m.user.username,
                'full_name': m.user.get_full_name() or m.user.username,
                'user_type': m.user.user_type,
            },
            'reply_to': m.reply_to_id,
            'is_edited': m.is_edited,
            'edited_at': m.edited_at.isoformat() if m.edited_at else None,
            'is_pinned': m.is_pinned,
            'is_highlighted': m.is_highlighted,
            'created_at': m.created_at.isoformat(),
        } for m in messages]

    async def send_initial_state(self):
        """Send initial state to newly connected client."""
        online_users = await self.get_online_users()
        recent_messages = await self.get_recent_messages()

        await self.send(text_data=json.dumps({
            'type': 'initial.state',
            'data': {
                'online_users': online_users,
                'messages': recent_messages,
                'discussion_id': self.discussion_id,
            },
        }))

    async def send_error(self, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
        }))


# ============================================================================
# SESSION CONSUMER (Guest Speaker Q&A)
# ============================================================================

class SessionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for guest speaker Q&A sessions.

    Extends forum functionality with moderation and Q&A features.
    """

    async def connect(self):
        """Handle WebSocket connection to guest session."""
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.session_group_name = f'session_{self.session_id}'
        self.user = self.scope.get('user')

        # Authenticate
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Verify session exists
        session = await self.get_session()
        if not session:
            await self.close(code=4004)
            return

        # Check access
        has_access = await self.check_session_access(session)
        if not has_access:
            await self.close(code=4003)
            return

        await self.accept()

        # Join session group
        await self.channel_layer.group_add(
            self.session_group_name,
            self.channel_name
        )

        # Track participant
        await self.add_participant()

        # Send initial state
        await self.send_initial_state()

        logger.info(f"User {self.user.id} joined session {self.session_id}")

    async def disconnect(self, close_code):
        """Handle disconnection from guest session."""
        if hasattr(self, 'session_group_name'):
            await self.update_participant(is_active=False)

            await self.channel_layer.group_discard(
                self.session_group_name,
                self.channel_name
            )

            logger.info(f"User {self.user.id} left session {self.session_id}")

    async def receive(self, text_data):
        """Route incoming messages."""
        try:
            if not await _cache_rate_limit(self.user.id, f'session:{self.session_id}'):
                await self.send_error("Rate limit exceeded. Please slow down.")
                return

            data = json.loads(text_data)
            message_type = data.get('type')

            handlers = {
                'question.submit': self.handle_question_submit,
                'question.upvote': self.handle_question_upvote,
                'question.approve': self.handle_question_approve,
                'question.reject': self.handle_question_reject,
                'question.answer': self.handle_question_answer,
                'session.start': self.handle_session_start,
                'session.end': self.handle_session_end,
            }

            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error in session consumer: {e}", exc_info=True)
            await self.send_error("Internal server error")

    # ========================================================================
    # QUESTION HANDLERS
    # ========================================================================

    async def handle_question_submit(self, data: Dict[str, Any]):
        """Submit a question for moderation."""
        content = data.get('content', '').strip()

        if not content:
            await self.send_error("Question content is required")
            return

        question = await self.save_question(content)

        if question:
            # Notify moderators
            await self.channel_layer.group_send(
                f'{self.session_group_name}_moderators',
                {
                    'type': 'question_pending',
                    'question': await self.serialize_question(question),
                }
            )

            # Confirm to submitter
            await self.send(text_data=json.dumps({
                'type': 'question.submitted',
                'question_id': question.id,
                'message': 'Your question has been submitted for review',
            }))

    async def handle_question_upvote(self, data: Dict[str, Any]):
        """Upvote a question."""
        question_id = data.get('question_id')

        if not question_id:
            await self.send_error("Question ID is required")
            return

        result = await self.upvote_question(question_id)

        if result:
            # Broadcast updated vote count
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'question_upvoted',
                    'question_id': question_id,
                    'upvote_count': result['upvote_count'],
                }
            )

    async def handle_question_approve(self, data: Dict[str, Any]):
        """Approve a question (moderators only)."""
        question_id = data.get('question_id')

        is_moderator = await self.check_is_moderator()
        if not is_moderator:
            await self.send_error("Only moderators can approve questions")
            return

        question = await self.approve_question(question_id)

        if question:
            # Broadcast approved question to session
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'question_approved',
                    'question': await self.serialize_question(question),
                }
            )

    async def handle_question_reject(self, data: Dict[str, Any]):
        """Reject a question (moderators only)."""
        question_id = data.get('question_id')
        reason = data.get('reason', '')

        is_moderator = await self.check_is_moderator()
        if not is_moderator:
            await self.send_error("Only moderators can reject questions")
            return

        success = await self.reject_question(question_id, reason)

        if success:
            await self.send(text_data=json.dumps({
                'type': 'question.rejected',
                'question_id': question_id,
            }))

    async def handle_question_answer(self, data: Dict[str, Any]):
        """Mark question as answered (speakers only)."""
        question_id = data.get('question_id')
        answer_content = data.get('answer', '')

        is_speaker = await self.check_is_speaker()
        if not is_speaker:
            await self.send_error("Only speakers can answer questions")
            return

        question = await self.answer_question(question_id, answer_content)

        if question:
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'question_answered',
                    'question': await self.serialize_question(question),
                }
            )

    # ========================================================================
    # SESSION CONTROL HANDLERS
    # ========================================================================

    async def handle_session_start(self, data: Dict[str, Any]):
        """Start the guest session (moderators only)."""
        is_moderator = await self.check_is_moderator()
        if not is_moderator:
            await self.send_error("Only moderators can start sessions")
            return

        success = await self.start_session()

        if success:
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'session_started',
                    'timestamp': timezone.now().isoformat(),
                }
            )

    async def handle_session_end(self, data: Dict[str, Any]):
        """End the guest session (moderators only)."""
        is_moderator = await self.check_is_moderator()
        if not is_moderator:
            await self.send_error("Only moderators can end sessions")
            return

        success = await self.end_session()

        if success:
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'session_ended',
                    'timestamp': timezone.now().isoformat(),
                }
            )

    # ========================================================================
    # CHANNEL LAYER EVENT RECEIVERS
    # ========================================================================

    async def question_pending(self, event):
        """Notify moderators of pending question."""
        await self.send(text_data=json.dumps({
            'type': 'question.pending',
            'question': event['question'],
        }))

    async def question_approved(self, event):
        """Broadcast approved question to all participants."""
        await self.send(text_data=json.dumps({
            'type': 'question.approved',
            'question': event['question'],
        }))

    async def question_upvoted(self, event):
        """Broadcast vote count update."""
        await self.send(text_data=json.dumps({
            'type': 'question.upvoted',
            'question_id': event['question_id'],
            'upvote_count': event['upvote_count'],
        }))

    async def question_answered(self, event):
        """Broadcast answered question."""
        await self.send(text_data=json.dumps({
            'type': 'question.answered',
            'question': event['question'],
        }))

    async def session_started(self, event):
        """Broadcast session start."""
        await self.send(text_data=json.dumps({
            'type': 'session.started',
            'timestamp': event['timestamp'],
        }))

    async def session_ended(self, event):
        """Broadcast session end."""
        await self.send(text_data=json.dumps({
            'type': 'session.ended',
            'timestamp': event['timestamp'],
        }))

    # ========================================================================
    # DATABASE OPERATIONS
    # ========================================================================

    @database_sync_to_async
    def get_session(self) -> Optional[GuestSpeakerSession]:
        """Fetch session from database."""
        try:
            return GuestSpeakerSession.objects.select_related(
                'company', 'discussion'
            ).get(id=self.session_id)
        except GuestSpeakerSession.DoesNotExist:
            return None

    @database_sync_to_async
    def check_session_access(self, session: GuestSpeakerSession) -> bool:
        """
        Check if user can access this session.

        Rules:
        - Cancelled sessions: No access (except superusers)
        - Scheduled/live sessions: Any authenticated user
        - Ended sessions: Any authenticated user (for viewing archives)
        - Max participants: Respect limit if set (for live sessions)
        """
        if session.status == 'cancelled' and not self.user.is_superuser:
            return False

        # Check max participants for live sessions
        if session.status == 'live' and session.max_participants:
            current_participants = session.total_participants
            if current_participants >= session.max_participants:
                # Allow moderators and speakers even if at capacity
                from core.models import SessionModerator, SessionSpeaker
                is_moderator = SessionModerator.objects.filter(
                    session=session, user=self.user
                ).exists()
                is_speaker = SessionSpeaker.objects.filter(
                    session=session, user=self.user
                ).exists()
                if not (is_moderator or is_speaker or self.user.is_superuser):
                    return False

        # All authenticated users can access active sessions
        return True

    @database_sync_to_async
    def check_is_moderator(self) -> bool:
        """Check if current user is a moderator."""
        return SessionModerator.objects.filter(
            session_id=self.session_id,
            user=self.user
        ).exists() or self.user.user_type == 'admin'

    @database_sync_to_async
    def check_is_speaker(self) -> bool:
        """Check if current user is a speaker."""
        return SessionSpeaker.objects.filter(
            session_id=self.session_id,
            user=self.user
        ).exists()

    @database_sync_to_async
    def add_participant(self):
        """Add user as session participant."""
        SessionParticipant.objects.update_or_create(
            session_id=self.session_id,
            user=self.user,
            defaults={'is_currently_active': True}
        )

    @database_sync_to_async
    def update_participant(self, is_active: bool):
        """Update participant status."""
        SessionParticipant.objects.filter(
            session_id=self.session_id,
            user=self.user
        ).update(
            is_currently_active=is_active,
            left_at=timezone.now() if not is_active else None
        )

    @database_sync_to_async
    def save_question(self, content: str) -> Optional[SessionQuestion]:
        """Save question to database."""
        try:
            session = GuestSpeakerSession.objects.get(id=self.session_id)

            # Create message first
            message = ForumMessage.objects.create(
                discussion=session.discussion,
                user=self.user,
                content=content,
            )

            # Create question
            question = SessionQuestion.objects.create(
                session=session,
                message=message,
                asked_by=self.user,
                status='pending' if session.is_moderated else 'approved',
            )

            # Update stats
            session.total_questions += 1
            session.save(update_fields=['total_questions'])

            # Update participant stats
            SessionParticipant.objects.filter(
                session=session,
                user=self.user
            ).update(questions_asked=django_models.F('questions_asked') + 1)

            return question
        except Exception as e:
            logger.error(f"Error saving question: {e}")
            return None

    @database_sync_to_async
    def upvote_question(self, question_id: int) -> Optional[Dict[str, Any]]:
        """Upvote a question."""
        try:
            question = SessionQuestion.objects.get(id=question_id)

            # Create or get upvote
            upvote, created = QuestionUpvote.objects.get_or_create(
                question=question,
                user=self.user
            )

            if created:
                # Update count
                question.upvote_count += 1
                question.save(update_fields=['upvote_count'])

                # Update participant stats
                SessionParticipant.objects.filter(
                    session=question.session,
                    user=self.user
                ).update(questions_upvoted=django_models.F('questions_upvoted') + 1)

                return {'upvote_count': question.upvote_count}

            return None  # Already upvoted
        except SessionQuestion.DoesNotExist:
            return None

    @database_sync_to_async
    def approve_question(self, question_id: int) -> Optional[SessionQuestion]:
        """Approve a question (moderator action)."""
        try:
            question = SessionQuestion.objects.get(id=question_id)
            question.status = 'approved'
            question.reviewed_by = self.user
            question.reviewed_at = timezone.now()
            question.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

            # Update moderator stats
            SessionModerator.objects.filter(
                session=question.session,
                user=self.user
            ).update(questions_approved=django_models.F('questions_approved') + 1)

            return question
        except SessionQuestion.DoesNotExist:
            return None

    @database_sync_to_async
    def reject_question(self, question_id: int, reason: str) -> bool:
        """Reject a question (moderator action)."""
        try:
            question = SessionQuestion.objects.get(id=question_id)
            question.status = 'rejected'
            question.reviewed_by = self.user
            question.reviewed_at = timezone.now()
            question.rejection_reason = reason
            question.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason'])

            # Update moderator stats
            SessionModerator.objects.filter(
                session=question.session,
                user=self.user
            ).update(questions_rejected=django_models.F('questions_rejected') + 1)

            return True
        except SessionQuestion.DoesNotExist:
            return False

    @database_sync_to_async
    def answer_question(self, question_id: int, answer_content: str) -> Optional[SessionQuestion]:
        """Answer a question (speaker action)."""
        try:
            question = SessionQuestion.objects.get(id=question_id)

            # Create answer message
            answer_message = ForumMessage.objects.create(
                discussion=question.session.discussion,
                user=self.user,
                content=answer_content,
                reply_to=question.message,
                is_highlighted=True,  # Highlight speaker answers
            )

            # Update question
            question.status = 'answered'
            question.answered_by = self.user
            question.answered_at = timezone.now()
            question.answer_message = answer_message
            question.save(update_fields=['status', 'answered_by', 'answered_at', 'answer_message'])

            # Update speaker stats
            SessionSpeaker.objects.filter(
                session=question.session,
                user=self.user
            ).update(questions_answered=django_models.F('questions_answered') + 1)

            return question
        except SessionQuestion.DoesNotExist:
            return None

    @database_sync_to_async
    def start_session(self) -> bool:
        """Start the session (moderator action)."""
        try:
            session = GuestSpeakerSession.objects.get(id=self.session_id)
            session.status = 'live'
            session.actual_start = timezone.now()
            session.save(update_fields=['status', 'actual_start'])
            return True
        except GuestSpeakerSession.DoesNotExist:
            return False

    @database_sync_to_async
    def end_session(self) -> bool:
        """End the session (moderator action)."""
        try:
            session = GuestSpeakerSession.objects.get(id=self.session_id)
            session.status = 'ended'
            session.actual_end = timezone.now()
            session.save(update_fields=['status', 'actual_end'])

            # TODO: Trigger archive generation (Celery task)

            return True
        except GuestSpeakerSession.DoesNotExist:
            return False

    @database_sync_to_async
    def serialize_question(self, question: SessionQuestion) -> Dict[str, Any]:
        """Serialize question for WebSocket transmission."""
        return {
            'id': question.id,
            'content': question.message.content,
            'asked_by': {
                'id': question.asked_by.id,
                'username': question.asked_by.username,
                'full_name': question.asked_by.get_full_name() or question.asked_by.username,
            },
            'status': question.status,
            'priority': question.priority,
            'upvote_count': question.upvote_count,
            'created_at': question.created_at.isoformat(),
        }

    async def send_initial_state(self):
        """Send initial session state to connected client."""
        session_data = await self.get_session_data()

        await self.send(text_data=json.dumps({
            'type': 'initial.state',
            'data': session_data,
        }))

    @database_sync_to_async
    def get_session_data(self) -> Dict[str, Any]:
        """Get complete session state."""
        session = GuestSpeakerSession.objects.select_related(
            'company', 'discussion'
        ).prefetch_related(
            'speakers__user',
            'moderators__user',
            'questions__message__user'
        ).get(id=self.session_id)

        # Get approved questions
        approved_questions = session.questions.filter(
            status__in=['approved', 'answered']
        ).select_related('message__user', 'asked_by')

        return {
            'session_id': session.id,
            'title': session.title,
            'description': session.description,
            'status': session.status,
            'scheduled_start': session.scheduled_start.isoformat(),
            'scheduled_end': session.scheduled_end.isoformat(),
            'is_moderated': session.is_moderated,
            'speakers': [{
                'id': s.user.id,
                'name': s.user.get_full_name() or s.user.username,
                'role': s.role,
            } for s in session.speakers.all()],
            'questions': [{
                'id': q.id,
                'content': q.message.content,
                'asked_by': {
                    'id': q.asked_by.id,
                    'username': q.asked_by.username,
                    'full_name': q.asked_by.get_full_name() or q.asked_by.username,
                },
                'status': q.status,
                'priority': q.priority,
                'upvote_count': q.upvote_count,
                'created_at': q.created_at.isoformat(),
            } for q in approved_questions],
        }

    async def send_error(self, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
        }))


# ============================================================================
# SPEAKER EVENT CONSUMER
# ============================================================================

class SpeakerEventConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for speaker events.

    Handles real-time interactions during speaker events including:
    - User join/leave notifications
    - Question submissions and upvoting
    - Live reactions (applause, thumbs_up, fire, heart)
    - Event status updates
    - Speaker presence

    Group naming: event_{event_id}
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.event_group_name = f'event_{self.event_id}'
        self.user = self.scope['user']

        # Verify user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return

        # Verify event exists and is live
        event = await self.get_event()
        if not event:
            await self.close()
            return

        # Join event group
        await self.channel_layer.group_add(
            self.event_group_name,
            self.channel_name
        )

        await self.accept()

        # Mark user as attending if registered
        await self.mark_attendance()

        # Send initial state
        await self.send_initial_state()

        # Notify others that user joined
        await self.channel_layer.group_send(
            self.event_group_name,
            {
                'type': 'user_joined',
                'user': await self.get_user_data(self.user)
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'event_group_name'):
            # Notify others that user left
            await self.channel_layer.group_send(
                self.event_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id
                }
            )

            # Leave event group
            await self.channel_layer.group_discard(
                self.event_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            if not await _cache_rate_limit(self.user.id, f'speaker_event:{self.event_id}'):
                await self.send_error("Rate limit exceeded. Please slow down.")
                return

            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'question.submit':
                await self.handle_question_submit(data)
            elif message_type == 'question.upvote':
                await self.handle_question_upvote(data)
            elif message_type == 'reaction.send':
                await self.handle_reaction_send(data)
            elif message_type == 'presence.update':
                pass  # Heartbeat, no action needed
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send_error("An error occurred processing your request")

    # Message Handlers
    async def handle_question_submit(self, data):
        """Handle question submission."""
        content = data.get('content', '').strip()

        if not content:
            await self.send_error("Question content cannot be empty")
            return

        if len(content) > 1000:
            await self.send_error("Question too long (max 1000 characters)")
            return

        # Create question
        question = await self.create_question(content)

        # Broadcast new question
        await self.channel_layer.group_send(
            self.event_group_name,
            {
                'type': 'question_new',
                'question': await self.format_question(question)
            }
        )

    async def handle_question_upvote(self, data):
        """Handle question upvote."""
        question_id = data.get('question_id')

        if not question_id:
            await self.send_error("Question ID required")
            return

        # Upvote question
        question = await self.upvote_question(question_id)

        if not question:
            await self.send_error("Question not found")
            return

        # Broadcast updated question
        await self.channel_layer.group_send(
            self.event_group_name,
            {
                'type': 'question_upvoted',
                'question': await self.format_question(question)
            }
        )

    async def handle_reaction_send(self, data):
        """Handle reaction submission."""
        reaction_type = data.get('reaction_type')

        valid_reactions = ['applause', 'thumbs_up', 'fire', 'heart']
        if reaction_type not in valid_reactions:
            await self.send_error(f"Invalid reaction type. Must be one of: {', '.join(valid_reactions)}")
            return

        # Create reaction
        reaction = await self.create_reaction(reaction_type)

        # Broadcast reaction
        await self.channel_layer.group_send(
            self.event_group_name,
            {
                'type': 'reaction_received',
                'reaction': {
                    'user': await self.get_user_data(self.user),
                    'reaction_type': reaction_type,
                    'timestamp': reaction.timestamp.isoformat()
                }
            }
        )

    # Group message handlers
    async def user_joined(self, event):
        """Broadcast user joined event."""
        await self.send(text_data=json.dumps({
            'type': 'user.joined',
            'user': event['user']
        }))

    async def user_left(self, event):
        """Broadcast user left event."""
        await self.send(text_data=json.dumps({
            'type': 'user.left',
            'user_id': event['user_id']
        }))

    async def question_new(self, event):
        """Broadcast new question."""
        await self.send(text_data=json.dumps({
            'type': 'question.new',
            'question': event['question']
        }))

    async def question_upvoted(self, event):
        """Broadcast question upvote."""
        await self.send(text_data=json.dumps({
            'type': 'question.upvoted',
            'question': event['question']
        }))

    async def reaction_received(self, event):
        """Broadcast reaction."""
        await self.send(text_data=json.dumps({
            'type': 'reaction.received',
            'reaction': event['reaction']
        }))

    async def event_status_changed(self, event):
        """Broadcast event status change."""
        await self.send(text_data=json.dumps({
            'type': 'event.status_changed',
            'status': event['status']
        }))

    # Database operations
    @database_sync_to_async
    def get_event(self):
        """Get event from database."""
        try:
            return SpeakerEvent.objects.get(id=self.event_id, status='live')
        except SpeakerEvent.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_attendance(self):
        """Mark user as attended."""
        try:
            registration = EventRegistration.objects.get(
                event_id=self.event_id,
                user=self.user,
                status='registered'
            )
            if not registration.joined_at:
                registration.joined_at = timezone.now()
                registration.save(update_fields=['joined_at'])

                # Update event attended count
                event = SpeakerEvent.objects.get(id=self.event_id)
                event.attended_count += 1
                event.save(update_fields=['attended_count'])
        except EventRegistration.DoesNotExist:
            pass

    @database_sync_to_async
    def create_question(self, content):
        """Create a new question."""
        question = EventQuestion.objects.create(
            event_id=self.event_id,
            user=self.user,
            content=content,
            status='pending'
        )

        # Update event questions count
        event = SpeakerEvent.objects.get(id=self.event_id)
        event.questions_count = event.questions.count()
        event.save(update_fields=['questions_count'])

        return question

    @database_sync_to_async
    def upvote_question(self, question_id):
        """Upvote a question."""
        try:
            question = EventQuestion.objects.get(id=question_id, event_id=self.event_id)
            question.upvotes += 1
            question.save(update_fields=['upvotes'])
            return question
        except EventQuestion.DoesNotExist:
            return None

    @database_sync_to_async
    def create_reaction(self, reaction_type):
        """Create a reaction."""
        return EventReaction.objects.create(
            event_id=self.event_id,
            user=self.user,
            reaction_type=reaction_type
        )

    @database_sync_to_async
    def get_user_data(self, user):
        """Format user data for transmission."""
        return {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'user_type': getattr(user, 'user_type', 'investor')
        }

    @database_sync_to_async
    def format_question(self, question):
        """Format question for transmission."""
        return {
            'id': question.id,
            'user': {
                'id': question.user.id,
                'username': question.user.username,
                'full_name': question.user.get_full_name() or question.user.username,
            },
            'content': question.content,
            'status': question.status,
            'upvotes': question.upvotes,
            'is_featured': question.is_featured,
            'created_at': question.created_at.isoformat(),
        }

    async def send_initial_state(self):
        """Send initial event state to newly connected user."""
        data = await self.get_initial_state_data()
        await self.send(text_data=json.dumps({
            'type': 'initial.state',
            'data': data
        }))

    @database_sync_to_async
    def get_initial_state_data(self):
        """Get initial state data from database."""
        event = SpeakerEvent.objects.select_related('company', 'created_by').get(id=self.event_id)

        # Get approved questions
        questions = EventQuestion.objects.filter(
            event=event,
            status__in=['approved', 'answered']
        ).select_related('user', 'answered_by').order_by('-upvotes', '-created_at')[:50]

        # Get active participants (those who joined)
        participants = EventRegistration.objects.filter(
            event=event,
            joined_at__isnull=False
        ).select_related('user')[:100]

        return {
            'event': {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'status': event.status,
                'format': event.format,
                'video_url': event.video_url,
                'scheduled_start': event.scheduled_start.isoformat(),
                'scheduled_end': event.scheduled_end.isoformat(),
            },
            'questions': [{
                'id': q.id,
                'user': {
                    'id': q.user.id,
                    'username': q.user.username,
                    'full_name': q.user.get_full_name() or q.user.username,
                },
                'content': q.content,
                'status': q.status,
                'upvotes': q.upvotes,
                'is_featured': q.is_featured,
                'created_at': q.created_at.isoformat(),
            } for q in questions],
            'participants': [{
                'id': p.user.id,
                'username': p.user.username,
                'full_name': p.user.get_full_name() or p.user.username,
                'user_type': getattr(p.user, 'user_type', 'investor'),
            } for p in participants],
        }

    async def send_error(self, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': message,
        }))


# ============================================================================
# INQUIRY CONSUMER (Property Inquiries Real-Time Chat)
# ============================================================================

class InquiryConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time property inquiry conversations.

    Enables instant messaging between property buyers and sellers.
    Each user connects to their own inbox channel to receive messages
    across all their conversations.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')

        # Authenticate user
        if not self.user or not self.user.is_authenticated:
            logger.warning("Unauthenticated connection attempt to inquiry inbox")
            await self.close(code=4001)
            return

        # Create a unique channel group for this user's inbox
        self.user_inbox_group = f'inbox_{self.user.id}'

        # Accept connection
        await self.accept()

        # Join user's inbox group
        await self.channel_layer.group_add(
            self.user_inbox_group,
            self.channel_name
        )

        logger.info(f"User {self.user.id} connected to inbox WebSocket")

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection.established',
            'user_id': self.user.id,
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'user_inbox_group'):
            await self.channel_layer.group_discard(
                self.user_inbox_group,
                self.channel_name
            )
            logger.info(f"User {self.user.id} disconnected from inbox WebSocket")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            if not await _cache_rate_limit(self.user.id, f'inquiry:{self.inquiry_id}'):
                await self.send_error("Rate limit exceeded. Please slow down.")
                return

            data = json.loads(text_data)
            message_type = data.get('type')

            handlers = {
                'message.send': self.handle_message_send,
                'message.read': self.handle_message_read,
                'typing.start': self.handle_typing_start,
                'typing.stop': self.handle_typing_stop,
                'presence.update': self.handle_presence_update,
            }

            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await self.send_error("Internal server error")

    async def handle_message_send(self, data: Dict[str, Any]):
        """
        Handle sending a new message in an inquiry conversation.
        """
        inquiry_id = data.get('inquiry_id')
        content = data.get('content', '').strip()

        if not inquiry_id or not content:
            await self.send_error("Inquiry ID and message content are required")
            return

        if len(content) > 5000:
            await self.send_error("Message too long (max 5000 characters)")
            return

        # Verify access and save message
        result = await self.save_inquiry_message(inquiry_id, content)

        if result:
            message_data = result['message']
            recipient_id = result['recipient_id']

            # Send confirmation to sender
            await self.send(text_data=json.dumps({
                'type': 'message.sent',
                'message': message_data,
            }))

            # Send to recipient's inbox
            recipient_group = f'inbox_{recipient_id}'
            await self.channel_layer.group_send(
                recipient_group,
                {
                    'type': 'message_new',
                    'message': message_data,
                }
            )

            logger.info(f"User {self.user.id} sent message in inquiry {inquiry_id}")
        else:
            await self.send_error("Failed to send message. You may not have permission.")

    async def handle_message_read(self, data: Dict[str, Any]):
        """Handle marking messages as read."""
        inquiry_id = data.get('inquiry_id')
        message_ids = data.get('message_ids', [])

        if not inquiry_id:
            await self.send_error("Inquiry ID is required")
            return

        # Mark messages as read
        result = await self.mark_messages_read(inquiry_id, message_ids)

        if result:
            # Notify the other party that messages were read
            other_user_id = result['other_user_id']
            if other_user_id:
                other_group = f'inbox_{other_user_id}'
                await self.channel_layer.group_send(
                    other_group,
                    {
                        'type': 'messages_read',
                        'inquiry_id': inquiry_id,
                        'read_by': self.user.id,
                        'message_ids': result['read_message_ids'],
                    }
                )

    async def handle_typing_start(self, data: Dict[str, Any]):
        """Handle typing indicator start."""
        inquiry_id = data.get('inquiry_id')
        if not inquiry_id:
            return

        # Get the other party and notify them
        other_user_id = await self.get_other_party(inquiry_id)
        if other_user_id:
            other_group = f'inbox_{other_user_id}'
            await self.channel_layer.group_send(
                other_group,
                {
                    'type': 'typing_indicator',
                    'inquiry_id': inquiry_id,
                    'user_id': self.user.id,
                    'is_typing': True,
                }
            )

    async def handle_typing_stop(self, data: Dict[str, Any]):
        """Handle typing indicator stop."""
        inquiry_id = data.get('inquiry_id')
        if not inquiry_id:
            return

        other_user_id = await self.get_other_party(inquiry_id)
        if other_user_id:
            other_group = f'inbox_{other_user_id}'
            await self.channel_layer.group_send(
                other_group,
                {
                    'type': 'typing_indicator',
                    'inquiry_id': inquiry_id,
                    'user_id': self.user.id,
                    'is_typing': False,
                }
            )

    async def handle_presence_update(self, data: Dict[str, Any]):
        """Handle presence heartbeat - keeps connection alive."""
        pass

    # ========================================================================
    # CHANNEL LAYER EVENT RECEIVERS
    # ========================================================================

    async def message_new(self, event):
        """Broadcast new message to recipient."""
        await self.send(text_data=json.dumps({
            'type': 'message.new',
            'message': event['message'],
        }))

    async def messages_read(self, event):
        """Broadcast that messages were read."""
        await self.send(text_data=json.dumps({
            'type': 'messages.read',
            'inquiry_id': event['inquiry_id'],
            'read_by': event['read_by'],
            'message_ids': event['message_ids'],
        }))

    async def typing_indicator(self, event):
        """Broadcast typing indicator."""
        await self.send(text_data=json.dumps({
            'type': 'typing.indicator',
            'inquiry_id': event['inquiry_id'],
            'user_id': event['user_id'],
            'is_typing': event['is_typing'],
        }))

    # ========================================================================
    # DATABASE OPERATIONS
    # ========================================================================

    @database_sync_to_async
    def save_inquiry_message(self, inquiry_id: int, content: str) -> Optional[Dict[str, Any]]:
        """Save a message to the inquiry conversation."""
        try:
            inquiry = PropertyInquiry.objects.select_related(
                'listing__prospector__user', 'inquirer'
            ).get(id=inquiry_id)

            # Verify user is either the inquirer or the listing owner
            listing_owner = inquiry.listing.prospector.user
            if self.user.id not in [inquiry.inquirer.id, listing_owner.id]:
                return None

            # Determine recipient
            if self.user.id == inquiry.inquirer.id:
                recipient = listing_owner
            else:
                recipient = inquiry.inquirer

            # Create message
            message = InquiryMessage.objects.create(
                inquiry=inquiry,
                sender=self.user,
                message=content,
            )

            # Update inquiry status
            inquiry.status = 'responded'
            inquiry.updated_at = timezone.now()
            inquiry.save(update_fields=['status', 'updated_at'])

            return {
                'message': {
                    'id': message.id,
                    'inquiry_id': inquiry.id,
                    'sender': message.sender.id,
                    'sender_name': message.sender.get_full_name() or message.sender.username,
                    'sender_email': message.sender.email,
                    'message': message.message,
                    'is_read': message.is_read,
                    'is_from_prospector': message.sender.id == listing_owner.id,
                    'created_at': message.created_at.isoformat(),
                },
                'recipient_id': recipient.id,
            }

        except PropertyInquiry.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error saving inquiry message: {e}")
            return None

    @database_sync_to_async
    def mark_messages_read(self, inquiry_id: int, message_ids: list) -> Optional[Dict[str, Any]]:
        """Mark messages as read."""
        try:
            inquiry = PropertyInquiry.objects.select_related(
                'listing__prospector__user', 'inquirer'
            ).get(id=inquiry_id)

            listing_owner = inquiry.listing.prospector.user
            if self.user.id not in [inquiry.inquirer.id, listing_owner.id]:
                return None

            # Get the other party
            other_user_id = listing_owner.id if self.user.id == inquiry.inquirer.id else inquiry.inquirer.id

            # Mark messages from the other party as read
            if message_ids:
                updated = InquiryMessage.objects.filter(
                    inquiry_id=inquiry_id,
                    id__in=message_ids,
                    is_read=False
                ).exclude(sender=self.user).update(is_read=True)
            else:
                # Mark all unread messages from other party as read
                messages = InquiryMessage.objects.filter(
                    inquiry_id=inquiry_id,
                    is_read=False
                ).exclude(sender=self.user)
                message_ids = list(messages.values_list('id', flat=True))
                messages.update(is_read=True)

            return {
                'other_user_id': other_user_id,
                'read_message_ids': message_ids,
            }

        except PropertyInquiry.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error marking messages read: {e}")
            return None

    @database_sync_to_async
    def get_other_party(self, inquiry_id: int) -> Optional[int]:
        """Get the other party's user ID in an inquiry."""
        try:
            inquiry = PropertyInquiry.objects.select_related(
                'listing__prospector__user', 'inquirer'
            ).get(id=inquiry_id)

            listing_owner = inquiry.listing.prospector.user
            if self.user.id == inquiry.inquirer.id:
                return listing_owner.id
            elif self.user.id == listing_owner.id:
                return inquiry.inquirer.id
            return None

        except PropertyInquiry.DoesNotExist:
            return None

    async def send_error(self, message: str):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': message,
        }))


# ============================================================================
# ASK THE EDITOR CONSUMER (Reader <-> editor/developer live chat)
# ============================================================================

# Every connected staff member sits in this one group, so a reader's question
# lights up whichever editors happen to be online without the reader needing
# to know who they are.
EDITOR_GROUP = 'ask_editor_editors'


class EditorChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for the homepage "Ask the Editor" widget.

    Two kinds of connection share this consumer:

    * A reader (any authenticated user) joins only their own thread group and
      can send messages into their own thread. Their thread row is created
      lazily on first send.
    * An editor (is_staff or is_superuser) additionally joins EDITOR_GROUP and
      may open any thread and reply into it.

    Authorisation is decided once at connect time and stored on
    ``self.is_editor``; every handler that can touch another user's thread
    re-checks it, so a reader who forges a thread_id gets an error rather
    than someone else's conversation.
    """

    # --------------------------------------------------------------- lifecycle

    async def connect(self):
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            logger.warning("Unauthenticated connection attempt to ask-editor")
            await self.close(code=4001)
            return

        self.is_editor = bool(
            getattr(self.user, 'is_staff', False)
            or getattr(self.user, 'is_superuser', False)
        )
        self.user_group = f'ask_editor_user_{self.user.id}'

        await self.accept()
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        if self.is_editor:
            await self.channel_layer.group_add(EDITOR_GROUP, self.channel_name)

        logger.info(
            f"User {self.user.id} connected to ask-editor "
            f"({'editor' if self.is_editor else 'reader'})"
        )

        await self.send(text_data=json.dumps({
            'type': 'connection.established',
            'user_id': self.user.id,
            'is_editor': self.is_editor,
        }))
        await self.send_initial_state()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if getattr(self, 'is_editor', False):
            await self.channel_layer.group_discard(EDITOR_GROUP, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            # Reads and typing pings are cheap and frequent; only rate-limit
            # the handler that writes rows and fans out to other people.
            if message_type == 'message.send':
                if not await _cache_rate_limit(self.user.id, 'ask_editor', limit=15, window=60):
                    await self.send_error("You are sending messages too quickly. Give it a moment.")
                    return

            handlers = {
                'message.send': self.handle_message_send,
                'thread.open': self.handle_thread_open,
                'thread.read': self.handle_thread_read,
                'thread.resolve': self.handle_thread_resolve,
                'typing.start': self.handle_typing_start,
                'typing.stop': self.handle_typing_stop,
                'presence.ping': self.handle_presence_ping,
            }

            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                logger.warning(f"Unknown ask-editor message type: {message_type}")
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received on ask-editor: {e}")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling ask-editor message: {e}", exc_info=True)
            await self.send_error("Internal server error")

    # ------------------------------------------------------------ inbound types

    async def handle_message_send(self, data: Dict[str, Any]):
        """Send a message. Readers write to their own thread; editors reply
        into the thread named by `thread_id`."""
        content = (data.get('content') or '').strip()
        if not content:
            await self.send_error("Message cannot be empty")
            return
        if len(content) > 5000:
            await self.send_error("Message too long (max 5000 characters)")
            return

        thread_id = data.get('thread_id')

        if thread_id and not self.is_editor:
            await self.send_error("Not permitted")
            return

        as_editor = bool(self.is_editor and thread_id)

        result = await self.save_message(content, thread_id, as_editor)
        if not result:
            await self.send_error("Could not send that message.")
            return

        payload = {
            'type': 'message.new',
            'thread_id': result['thread_id'],
            'message': result['message'],
            'thread': result['thread'],
        }

        # The reader's own group, so their other open tabs stay in sync too.
        await self.channel_layer.group_send(
            f"ask_editor_user_{result['reader_id']}",
            {'type': 'chat_message', 'payload': payload},
        )
        # Editors always see the traffic, in both directions - an answer typed
        # by one editor should land in every other editor's inbox as well.
        await self.channel_layer.group_send(
            EDITOR_GROUP,
            {'type': 'chat_message', 'payload': payload},
        )

        if not as_editor:
            # Fire-and-forget. Dispatching to Celery talks to Redis, and a
            # Redis blip makes that retry for ~90s - the reader must not sit
            # there waiting on an email they never see. Their message is
            # already saved and already delivered to any live editor.
            asyncio.create_task(
                self.queue_editor_alert(result['thread_id'], result['message']['id'])
            )

    async def handle_thread_open(self, data: Dict[str, Any]):
        """Editor-only: load one thread's full history."""
        if not self.is_editor:
            await self.send_error("Not permitted")
            return

        thread_id = data.get('thread_id')
        if not thread_id:
            await self.send_error("thread_id is required")
            return

        history = await self.get_thread_history(thread_id)
        if history is None:
            await self.send_error("Conversation not found")
            return

        await self.send(text_data=json.dumps({
            'type': 'thread.history',
            'thread_id': thread_id,
            **history,
        }))

        # Opening a conversation IS reading it. Doing this server-side rather
        # than making the client send a second `thread.read` keeps the badge
        # honest even if that follow-up never arrives.
        await self.handle_thread_read({'thread_id': thread_id})

    async def handle_thread_read(self, data: Dict[str, Any]):
        """Clear the unread badge for whichever side is reading."""
        thread = await self.mark_read(data.get('thread_id'))
        if not thread:
            return

        payload = {'type': 'thread.updated', 'thread': thread}
        if self.is_editor:
            # This socket is in EDITOR_GROUP, so the fan-out covers it too -
            # sending directly as well would deliver the same update twice.
            await self.channel_layer.group_send(
                EDITOR_GROUP, {'type': 'chat_message', 'payload': payload},
            )
        else:
            await self.send(text_data=json.dumps(payload))

    async def handle_thread_resolve(self, data: Dict[str, Any]):
        """Editor-only: mark a conversation handled (or reopen it)."""
        if not self.is_editor:
            await self.send_error("Not permitted")
            return

        thread = await self.set_resolved(
            data.get('thread_id'), bool(data.get('resolved', True))
        )
        if thread:
            await self.channel_layer.group_send(
                EDITOR_GROUP,
                {'type': 'chat_message', 'payload': {
                    'type': 'thread.updated', 'thread': thread,
                }},
            )

    async def handle_typing_start(self, data: Dict[str, Any]):
        await self.broadcast_typing(data, True)

    async def handle_typing_stop(self, data: Dict[str, Any]):
        await self.broadcast_typing(data, False)

    async def handle_presence_ping(self, data: Dict[str, Any]):
        """Heartbeat. Answered so the client can tell a live socket from a
        half-open one that will not error until it tries to write."""
        await self.send(text_data=json.dumps({'type': 'presence.pong'}))

    async def broadcast_typing(self, data: Dict[str, Any], is_typing: bool):
        thread_id = data.get('thread_id')
        payload = {
            'type': 'typing.indicator',
            'thread_id': thread_id,
            'from_editor': self.is_editor,
            'is_typing': is_typing,
        }
        if self.is_editor:
            if not thread_id:
                return
            reader_id = await self.get_thread_reader(thread_id)
            if reader_id:
                await self.channel_layer.group_send(
                    f'ask_editor_user_{reader_id}',
                    {'type': 'chat_message', 'payload': payload},
                )
        else:
            await self.channel_layer.group_send(
                EDITOR_GROUP,
                {'type': 'chat_message', 'payload': payload},
            )

    # ---------------------------------------------------------- group handlers

    async def chat_message(self, event):
        """Relay a group_send payload straight through to this socket."""
        await self.send(text_data=json.dumps(event['payload']))

    # -------------------------------------------------------------- db helpers

    @database_sync_to_async
    def save_message(self, content: str, thread_id, as_editor: bool):
        """Persist a message and return it alongside refreshed thread state."""
        from core.models import EditorQuestionThread, EditorQuestionMessage

        if as_editor:
            thread = (
                EditorQuestionThread.objects
                .select_related('user')
                .filter(id=thread_id)
                .first()
            )
            if not thread:
                return None
        else:
            # Lazy creation: opening the widget and closing it leaves no row.
            thread, _ = EditorQuestionThread.objects.select_related('user').get_or_create(
                user=self.user
            )

        message = EditorQuestionMessage.objects.create(
            thread=thread,
            sender=self.user,
            is_from_editor=as_editor,
            content=content,
        )

        thread.last_message_at = message.created_at
        thread.last_message_preview = content[:200]
        if as_editor:
            thread.unread_for_user += 1
            # An editor replying is by definition caught up on this thread.
            thread.unread_for_editor = 0
        else:
            thread.unread_for_editor += 1
            thread.unread_for_user = 0
            # A new question reopens a conversation the editor had closed.
            thread.is_resolved = False
        thread.save(update_fields=[
            'last_message_at', 'last_message_preview',
            'unread_for_editor', 'unread_for_user', 'is_resolved', 'updated_at',
        ])

        return {
            'thread_id': thread.id,
            'reader_id': thread.user_id,
            'message': self._serialize_message(message),
            'thread': self._serialize_thread(thread),
        }

    @database_sync_to_async
    def get_thread_history(self, thread_id):
        from core.models import EditorQuestionThread

        thread = (
            EditorQuestionThread.objects
            .select_related('user')
            .filter(id=thread_id)
            .first()
        )
        if not thread:
            return None

        messages = thread.messages.select_related('sender').order_by('created_at')[:200]
        return {
            'thread': self._serialize_thread(thread),
            'messages': [self._serialize_message(m) for m in messages],
        }

    @database_sync_to_async
    def mark_read(self, thread_id):
        from core.models import EditorQuestionThread

        qs = EditorQuestionThread.objects.select_related('user')
        if self.is_editor:
            if not thread_id:
                return None
            thread = qs.filter(id=thread_id).first()
        else:
            # A reader can only ever clear their own badge, whatever they send.
            thread = qs.filter(user=self.user).first()
        if not thread:
            return None

        side = 'unread_for_editor' if self.is_editor else 'unread_for_user'
        if getattr(thread, side) == 0:
            return self._serialize_thread(thread)

        setattr(thread, side, 0)
        thread.save(update_fields=[side, 'updated_at'])
        thread.messages.filter(
            is_read=False,
            is_from_editor=not self.is_editor,
        ).update(is_read=True)
        return self._serialize_thread(thread)

    @database_sync_to_async
    def set_resolved(self, thread_id, resolved: bool):
        from core.models import EditorQuestionThread

        thread = (
            EditorQuestionThread.objects
            .select_related('user')
            .filter(id=thread_id)
            .first()
        )
        if not thread:
            return None
        thread.is_resolved = resolved
        thread.save(update_fields=['is_resolved', 'updated_at'])
        return self._serialize_thread(thread)

    @database_sync_to_async
    def get_thread_reader(self, thread_id):
        from core.models import EditorQuestionThread

        return (
            EditorQuestionThread.objects
            .filter(id=thread_id)
            .values_list('user_id', flat=True)
            .first()
        )

    @database_sync_to_async
    def get_initial_state(self):
        """Reader: their own conversation. Editor: the whole inbox."""
        from core.models import EditorQuestionThread

        if self.is_editor:
            threads = (
                EditorQuestionThread.objects
                .select_related('user')
                .order_by('-last_message_at')[:100]
            )
            return {
                'threads': [self._serialize_thread(t) for t in threads],
                'thread': None,
                'messages': [],
            }

        thread = (
            EditorQuestionThread.objects
            .select_related('user')
            .filter(user=self.user)
            .first()
        )
        if not thread:
            # No row yet - the widget opens on an empty conversation.
            return {'threads': [], 'thread': None, 'messages': []}

        messages = thread.messages.select_related('sender').order_by('created_at')[:200]
        return {
            'threads': [],
            'thread': self._serialize_thread(thread),
            'messages': [self._serialize_message(m) for m in messages],
        }

    @database_sync_to_async
    def queue_editor_alert(self, thread_id: int, message_id: int):
        """Hand the email off to Celery - send_mail must not block the loop.

        ignore_result=True keeps this off the Redis *result* backend, which
        nothing ever reads for a fire-and-forget email and which is what
        turns an unreachable Redis into a 20-attempt retry loop.
        """
        try:
            from core.tasks import notify_editor_question_task
            notify_editor_question_task.apply_async(
                args=[thread_id, message_id], ignore_result=True
            )
        except Exception as e:
            # A broker hiccup must not cost the reader their message - it is
            # already saved and already on its way to any live editor.
            logger.error(f"[ASK-EDITOR] could not queue email alert: {e}")

    # ------------------------------------------------------------- serializers

    @staticmethod
    def _serialize_message(message) -> Dict[str, Any]:
        sender = message.sender
        return {
            'id': message.id,
            'thread_id': message.thread_id,
            'content': message.content,
            'is_from_editor': message.is_from_editor,
            'is_read': message.is_read,
            'sender_name': (
                (sender.get_full_name() or sender.username) if sender else 'Deleted user'
            ),
            'created_at': message.created_at.isoformat(),
        }

    @staticmethod
    def _serialize_thread(thread) -> Dict[str, Any]:
        reader = thread.user
        return {
            'id': thread.id,
            'user_id': thread.user_id,
            'user_name': reader.get_full_name() or reader.username,
            'user_email': reader.email or '',
            'last_message_at': (
                thread.last_message_at.isoformat() if thread.last_message_at else None
            ),
            'last_message_preview': thread.last_message_preview,
            'unread_for_editor': thread.unread_for_editor,
            'unread_for_user': thread.unread_for_user,
            'is_resolved': thread.is_resolved,
        }

    # ------------------------------------------------------------------ helpers

    async def send_initial_state(self):
        state = await self.get_initial_state()
        await self.send(text_data=json.dumps({
            'type': 'initial.state',
            **state,
        }))

    async def send_error(self, message: str):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': message,
        }))
