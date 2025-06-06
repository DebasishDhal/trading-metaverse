import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Signup from './components/Signup';
import LandingPage from './components/LandingPage';
import Introduction from './components/Introduction';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/signup" element={<Signup />} />
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/introduction" element={<Introduction />} />
        <Route path="/" element={<Navigate to="/introduction" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
