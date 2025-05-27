import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import TestSessionTimeout from "./components/TestSessionTimeout";

function TestApp() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<TestSessionTimeout />} />
      </Routes>
    </Router>
  );
}

export default TestApp;
