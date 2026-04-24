/**
 * Chat layout strips the default dashboard padding so the chat UI
 * can fill the entire remaining viewport height.
 */
export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-col h-full -mx-8 -my-6">{children}</div>
}
