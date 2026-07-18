import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { fetchSites } from '../api/sites';
import { useSelectedProject } from '../hooks/useSelectedProject';

export function OverviewPage() {
  const { projectKey, setProjectKey } = useSelectedProject();
  const { data: sites, isLoading, error } = useQuery({ queryKey: ['sites'], queryFn: fetchSites });

  return (
    <div>
      <h2>Visão Geral</h2>

      <label htmlFor="project-select">Projeto:</label>{' '}
      <select id="project-select" value={projectKey} onChange={(e) => setProjectKey(e.target.value)}>
        <option value="TEC">TEC — Sistema MBC</option>
        <option value="CAP">CAP — Capela</option>
      </select>

      {isLoading && <p>Carregando sites configurados...</p>}
      {error && <p>Nenhum site sincronizado ainda — rode o CLI de sync (ver README.md).</p>}
      {sites && sites.length === 0 && <p>Nenhum site sincronizado ainda — rode o CLI de sync (ver README.md).</p>}
      {sites && sites.length > 0 && (
        <ul>
          {sites.map((site) => (
            <li key={site.id}>{site.key} — {site.name}</li>
          ))}
        </ul>
      )}

      <nav className="overview-shortcuts">
        <Link to="/sprint-atual">Ver Sprint Atual →</Link>
        <Link to="/pessoas">Ver Por Pessoa →</Link>
      </nav>
    </div>
  );
}
