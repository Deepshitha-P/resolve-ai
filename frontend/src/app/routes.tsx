import { Navigate, Route, Routes } from 'react-router-dom';
import DashboardPage from '../features/dashboard/DashboardPage';
import AnalyticsOverviewPage from '../features/analytics/AnalyticsOverviewPage';
import PainPointsPage from '../features/pain-points/PainPointsPage';
import VoiceOfCustomerPage from '../features/voice-of-customer/VoiceOfCustomerPage';
import CopilotPage from '../features/copilot/CopilotPage';
import PlaceholderPage from '../features/placeholder/PlaceholderPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/kpis" element={<AnalyticsOverviewPage />} />
      <Route path="/spikes" element={<PainPointsPage />} />
      <Route path="/sentiment" element={<VoiceOfCustomerPage />} />
      <Route path="/rag" element={<CopilotPage />} />
      <Route path="*" element={<PlaceholderPage title="Page Not Found" description="This route has not been created yet." />} />
    </Routes>
  );
}
