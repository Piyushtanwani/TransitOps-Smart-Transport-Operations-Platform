import { useState } from 'react';

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ id: string, text: string, sender: 'user' | 'bot' }[]>([
    { id: 'm1', text: 'Hi, I am TransitOps AI. How can I help you today?', sender: 'bot' }
  ]);
  const [inputText, setInputText] = useState('');

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    // Add user message
    const newMsg = { id: Date.now().toString(), text: inputText, sender: 'user' as const };
    setMessages(prev => [...prev, newMsg]);
    setInputText('');

    // Mock bot response after a short delay
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        text: 'I am a mock AI assistant. I cannot perform real actions yet!',
        sender: 'bot'
      }]);
    }, 800);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {isOpen && (
        <div className="w-80 h-96 bg-surface-0 border border-line rounded-xl shadow-xl flex flex-col overflow-hidden mb-4 transition-all origin-bottom-right">
          {/* Header */}
          <div className="bg-surface-2 border-b border-line px-4 py-3 flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-ok rounded-full"></div>
              <h3 className="font-semibold text-sm text-ink">TransitOps AI</h3>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-ink-mute hover:text-ink transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-surface-1/50">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                  msg.sender === 'user' 
                    ? 'bg-signal text-white rounded-br-none' 
                    : 'bg-surface-2 border border-line text-ink rounded-bl-none'
                }`}>
                  {msg.text}
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="p-3 border-t border-line bg-surface-0">
            <form onSubmit={handleSend} className="flex items-center space-x-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 h-9 rounded-md border border-line bg-surface-1 px-3 text-sm focus:border-signal focus:outline-none text-ink"
              />
              <button 
                type="submit"
                disabled={!inputText.trim()}
                className="h-9 w-9 rounded-md bg-signal text-white flex items-center justify-center disabled:opacity-50 hover:bg-signal/90 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </form>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 bg-signal rounded-full shadow-lg flex items-center justify-center text-white hover:bg-signal/90 hover:scale-105 transition-all focus:outline-none focus:ring-4 focus:ring-signal/30"
      >
        {isOpen ? (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        )}
      </button>
    </div>
  );
}
