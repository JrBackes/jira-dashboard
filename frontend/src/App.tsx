import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { SelectedProjectProvider } from './hooks/useSelectedProject';
import { OverviewPage } from './pages/OverviewPage';
import { CurrentSprintPage } from './pages/CurrentSprintPage';
import { PeoplePage } from './pages/PeoplePage';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SelectedProjectProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<OverviewPage />} />
              <Route path="sprint-atual" element={<CurrentSprintPage />} />
              <Route path="pessoas" element={<PeoplePage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </SelectedProjectProvider>
    </QueryClientProvider>
  );
}

export default App;
