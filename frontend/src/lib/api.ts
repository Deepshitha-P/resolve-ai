export const API_BASE_URL = '/api';

export async function fetchDashboardMetrics() {
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard`);
    if (!response.ok) throw new Error('Failed to fetch dashboard metrics');
    return await response.json();
  } catch (error) {
    console.error('Error fetching dashboard metrics:', error);
    return null;
  }
}

export async function fetchPainPoints() {
  try {
    const response = await fetch(`${API_BASE_URL}/pain-points`);
    if (!response.ok) throw new Error('Failed to fetch pain points');
    return await response.json();
  } catch (error) {
    console.error('Error fetching pain points:', error);
    return { clusters: [], total: 0 };
  }
}

export async function sendChatMessage(query: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });
    if (!response.ok) throw new Error('Failed to send chat message');
    return await response.json();
  } catch (error) {
    console.error('Error sending chat message:', error);
    return { response: 'Sorry, I encountered an error.' };
  }
}

export async function fetchVoiceOfCustomer() {
  try {
    const response = await fetch(`${API_BASE_URL}/voice-of-customer`);
    if (!response.ok) throw new Error('Failed to fetch voice of customer');
    return await response.json();
  } catch (error) {
    console.error('Error fetching voice of customer:', error);
    return null;
  }
}

export async function fetchConversations() {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`);
    if (!response.ok) throw new Error('Failed to fetch conversations');
    return await response.json();
  } catch (error) {
    console.error('Error fetching conversations:', error);
    return { conversations: [] };
  }
}

export async function fetchChatHistory(limit: number = 50) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/history?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch chat history');
    return await response.json();
  } catch (error) {
    console.error('Error fetching chat history:', error);
    return { conversations: [], total: 0 };
  }
}

export async function clearChatHistory() {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/history`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to clear chat history');
    return await response.json();
  } catch (error) {
    console.error('Error clearing chat history:', error);
    return { status: 'error' };
  }
}

