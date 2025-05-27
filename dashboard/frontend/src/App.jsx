import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import CadastroPage from "./pages/CadastroPage";
import Dashboard from "./pages/Dashboard";
import Creditos from "./pages/Creditos";
import WorkOrderAllocation from './pages/WorkOrderAllocation';
import Simulador from "./pages/Simulador";
import MinhasWOs from "./pages/MinhasWOs";
import MapaKMs from "./pages/MapaKMs";
import Perfil from "./pages/Perfil";
import Layout from "./components/Layout";
import ProtectedRoute from "./routes/ProtectedRoutes";
import EsqueciSenhaPage from "./pages/EsqueciSenhaPage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/cadastro" element={<CadastroPage />} />
        <Route path="/esqueci-senha" element={<EsqueciSenhaPage />} />
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/creditos" element={<Creditos />} />
          <Route path="/alocar-wo" element={<WorkOrderAllocation />} />
          <Route path="/simulador" element={<Simulador />} />
          <Route path="/wos" element={<MinhasWOs />} />
          <Route path="/mapa-kms" element={<MapaKMs />} />
          <Route path="/perfil" element={<Perfil />} />
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
