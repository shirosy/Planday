export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const formatSessionId = (sessionId: string): string => {
  return sessionId.substring(0, 8) + '...';
};

export const isValidSessionId = (sessionId: string): boolean => {
  return /^session_\d+_[a-z0-9]+$/.test(sessionId);
};