import { NavLink, Outlet } from 'react-router-dom';

const navItemClass = ({ isActive }: { isActive: boolean }) =>
  `nav-item${isActive ? ' nav-item--active' : ''}`;

export function AppLayout() {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1>Jira Dashboard MBC</h1>
        <nav>
          <NavLink to="/" end className={navItemClass}>Visão Geral</NavLink>
          <NavLink to="/sprint-atual" className={navItemClass}>Sprint Atual</NavLink>
          <NavLink to="/pessoas" className={navItemClass}>Por Pessoa</NavLink>
        </nav>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
