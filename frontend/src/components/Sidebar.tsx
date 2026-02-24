import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  const links = [
    { to: '/', label: '메일 입력', icon: '📝' },
    { to: '/emails', label: '메일 목록', icon: '📋' },
    { to: '/chat', label: 'Q&A 채팅', icon: '💬' },
  ];

  return (
    <aside className="w-64 bg-slate-800 text-white flex flex-col h-full border-r border-slate-700 shadow-lg">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-xl font-bold tracking-tight">📧 Mail Assistant</h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-slate-700 text-white shadow-md transform scale-[1.02]'
                  : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'
              }`
            }
          >
            <span className="text-xl">{link.icon}</span>
            <span className="font-medium">{link.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-700 text-xs text-slate-500 text-center">
        v0.1.0 Alpha
      </div>
    </aside>
  );
};

export default Sidebar;
