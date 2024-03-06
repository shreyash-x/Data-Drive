import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import LoginPage from './Pages/LoginPage/LoginPage';
import HomePage from './Pages/HomePage/HomePage';
import NotFound from './Pages/NotFound/NotFound';
import PublicViewPage from './Pages/PublicViewPage/PublicViewPage';
const App = () => {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/notfound" element={<NotFound />} />
          <Route path="/*" element={<HomePage />} />
          <Route path="/public/*" element={<PublicViewPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
};

export default App;
