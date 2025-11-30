import { ForumUser } from '@/hooks/useForumWebSocket';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

interface OnlineUsersProps {
  users: ForumUser[];
  typingUsers: ForumUser[];
}

export function OnlineUsers({ users, typingUsers }: OnlineUsersProps) {
  const getUserTypeVariant = (userType?: string) => {
    const variants: Record<string, 'gold' | 'copper' | 'slate'> = {
      'investor': 'gold',
      'analyst': 'copper',
      'company': 'slate',
    };
    return variants[userType || ''] || 'slate';
  };

  const getUserTypeLabel = (userType?: string) => {
    if (!userType) return 'User';
    return userType.charAt(0).toUpperCase() + userType.slice(1);
  };

  return (
    <Card variant="glass-card" className="sticky top-4">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Online Users</CardTitle>
          <Badge variant="gold" className="text-xs">
            {users.length}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {users.length === 0 ? (
          <div className="text-center py-8">
            <svg className="w-12 h-12 mx-auto text-slate-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p className="text-slate-400 text-sm">No users online</p>
          </div>
        ) : (
          <div className="space-y-2">
            {users.map((user) => {
              const isTyping = typingUsers.some((u) => u.id === user.id);

              return (
                <div
                  key={user.id}
                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors"
                >
                  {/* Avatar */}
                  <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-copper-400 flex items-center justify-center text-white font-bold">
                      {user.full_name.charAt(0).toUpperCase()}
                    </div>
                    {/* Online indicator */}
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-slate-900 rounded-full"></div>
                  </div>

                  {/* User info */}
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-white text-sm truncate">
                      {user.full_name}
                    </div>
                    <div className="text-xs text-slate-400 truncate">
                      @{user.username}
                    </div>
                    {isTyping && (
                      <div className="flex items-center gap-1 mt-1">
                        <div className="flex gap-1">
                          <div className="w-1.5 h-1.5 bg-gold-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                          <div className="w-1.5 h-1.5 bg-gold-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                          <div className="w-1.5 h-1.5 bg-gold-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                        <span className="text-xs text-gold-400 italic">typing...</span>
                      </div>
                    )}
                  </div>

                  {/* User type badge */}
                  <Badge variant={getUserTypeVariant(user.user_type)} className="text-xs">
                    {getUserTypeLabel(user.user_type)}
                  </Badge>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
