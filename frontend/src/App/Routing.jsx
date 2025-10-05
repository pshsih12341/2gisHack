import React from 'react';
import {BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import Layout from '../Shared/Layout';
import HomePage from '../Pages/HomePage';
import ProfilePage from '../Pages/ProfilePage';
import NotFoundPage from '../Pages/NotFoundPage';

import {Navigate} from 'react-router-dom';
import {useStore} from './Store';

const ProtectedRoute = ({children}) => {
  const {user} = useStore();

  if (!user) {
    return <Navigate to='/login' replace />;
  }

  return children;
};

const Routing = () => {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<Layout />}>
          <Route index element={<HomePage />} />
        </Route>
        <Route path='profile' element={<ProfilePage />} />
        <Route path='*' element={<NotFoundPage />} />
      </Routes>
    </Router>
  );
};

export default Routing;
