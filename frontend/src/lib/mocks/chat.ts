import type { ChatMessage } from '../../types/api';

export const starterMessages: ChatMessage[] = [
  {
    id: 'msg-1',
    role: 'assistant',
    content: 'Hello! IΓÇÖm your Resolve AI assistant. Ask about performance, pain points, recurring issues, or customer sentiment.'
  }
];

export const exampleChatMessages: ChatMessage[] = [
  {
    id: 'msg-2',
    role: 'user',
    content: 'What are the biggest issues affecting customer satisfaction this week?'
  },
  {
    id: 'msg-3',
    role: 'assistant',
    content: 'The highest-impact issues are mobile app instability, billing confusion, and service outages in metro regions. These topics account for over 40% of negative sentiment.'
  }
];
