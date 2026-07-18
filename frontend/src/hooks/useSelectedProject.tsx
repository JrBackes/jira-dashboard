import { createContext, useContext, useState, type ReactNode } from 'react';

interface SelectedProjectContextValue {
  projectKey: string;
  setProjectKey: (key: string) => void;
}

const SelectedProjectContext = createContext<SelectedProjectContextValue | null>(null);

export function SelectedProjectProvider({ children }: { children: ReactNode }) {
  const [projectKey, setProjectKey] = useState('TEC');
  return (
    <SelectedProjectContext.Provider value={{ projectKey, setProjectKey }}>
      {children}
    </SelectedProjectContext.Provider>
  );
}

export function useSelectedProject() {
  const ctx = useContext(SelectedProjectContext);
  if (!ctx) throw new Error('useSelectedProject precisa estar dentro de SelectedProjectProvider');
  return ctx;
}
