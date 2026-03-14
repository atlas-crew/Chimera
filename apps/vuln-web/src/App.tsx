import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { SettingsProvider } from './components/SettingsProvider'
import { ConnectivityProvider } from './components/ConnectivityProvider'
import { RequestInspectorProvider } from './components/RequestInspectorProvider'
import { Home } from './pages/Home'
import { HealthcareDashboard } from './pages/HealthcareDashboard'
import { BankingDashboard } from './pages/BankingDashboard'
import { EcommerceDashboard } from './pages/EcommerceDashboard'
import { SaasDashboard } from './pages/SaasDashboard'
import { GovernmentDashboard } from './pages/GovernmentDashboard'
import { TelecomDashboard } from './pages/TelecomDashboard'
import { EnergyDashboard } from './pages/EnergyDashboard'
import { IcsOtDashboard } from './pages/IcsOtDashboard'
import { InsuranceDashboard } from './pages/InsuranceDashboard'
import { LoyaltyDashboard } from './pages/LoyaltyDashboard'
import { AdminDashboard } from './pages/AdminDashboard'
import { AiResearchLab } from './pages/AiResearchLab'

function App() {
  return (
    <SettingsProvider>
      <ConnectivityProvider>
        <RequestInspectorProvider>
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/healthcare" element={<HealthcareDashboard />} />
                <Route path="/banking" element={<BankingDashboard />} />
                <Route path="/ecommerce" element={<EcommerceDashboard />} />
                <Route path="/saas" element={<SaasDashboard />} />
                <Route path="/government" element={<GovernmentDashboard />} />
                <Route path="/telecom" element={<TelecomDashboard />} />
                <Route path="/energy" element={<EnergyDashboard />} />
                <Route path="/ics-ot" element={<IcsOtDashboard />} />
                <Route path="/insurance" element={<InsuranceDashboard />} />
                <Route path="/loyalty" element={<LoyaltyDashboard />} />
                <Route path="/admin" element={<AdminDashboard />} />
                <Route path="/ai-lab" element={<AiResearchLab />} />
              </Routes>
            </Layout>
          </Router>
        </RequestInspectorProvider>
      </ConnectivityProvider>
    </SettingsProvider>
  )
}

export default App