import { useState } from 'react';
import { ForumMessage as ForumMessageType } from '@/hooks/useForumWebSocket';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface ForumMessageProps {
  message: ForumMessageType;
  currentUserId?: number;
  isAdmin?: boolean;
  onEdit?: (messageId: number, content: string) => void;
  onDelete?: (messageId: number) => void;
  onReply?: (messageId: number) => void;
}

export function ForumMessage({
  message,
  currentUserId,
  isAdmin = false,
  onEdit,
  onDelete,
  onReply,
}: ForumMessageProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);

  const isOwnMessage = currentUserId === message.user.id;
  const canDelete = isOwnMessage || isAdmin;
  const isDeleted = message.is_deleted;

  const handleSaveEdit = () => {
    if (editContent.trim() && onEdit) {
      onEdit(message.id, editContent.trim());
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    setEditContent(message.content);
    setIsEditing(false);
  };

  if (isDeleted) {
    return (
      <Card variant="glass-card" className="opacity-50">
        <CardContent className="py-3">
          <div className="text-sm text-slate-500 italic">
            This message has been deleted
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="glass-card" className={isOwnMessage ? 'border-l-2 border-gold-400' : ''}>
      <CardContent className="py-3">
        {/* Message Header */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold-400 to-copper-400 flex items-center justify-center text-white text-sm font-bold">
              {message.user.full_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="font-semibold text-white text-sm">
                {message.user.full_name}
                {isOwnMessage && (
                  <span className="ml-2 text-xs text-gold-400">(You)</span>
                )}
              </div>
              <div className="text-xs text-slate-400">
                {new Date(message.created_at).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
                {message.is_edited && (
                  <span className="ml-2 italic">(edited)</span>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          {(isOwnMessage || canDelete) && !isEditing && (
            <div className="flex items-center gap-1">
              {/* Edit button - only for own messages */}
              {isOwnMessage && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsEditing(true)}
                  className="h-7 px-2 text-xs"
                >
                  <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Edit
                </Button>
              )}
              {/* Delete button - for own messages or admins */}
              {canDelete && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete?.(message.id)}
                  className="h-7 px-2 text-xs text-red-400 hover:text-red-300"
                >
                  <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Delete
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Message Content */}
        {isEditing ? (
          <div className="space-y-2">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-gold-400"
              rows={3}
              maxLength={5000}
            />
            <div className="flex items-center gap-2">
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveEdit}
                disabled={!editContent.trim() || editContent === message.content}
              >
                Save
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancelEdit}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <>
            <p className="text-slate-200 text-sm whitespace-pre-wrap break-words">
              {message.content}
            </p>

            {/* Reply Button */}
            {onReply && !isOwnMessage && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onReply(message.id)}
                className="mt-2 h-7 px-2 text-xs text-slate-400 hover:text-white"
              >
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                </svg>
                Reply
              </Button>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
