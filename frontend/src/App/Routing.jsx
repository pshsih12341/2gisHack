import React from 'react';
import {BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import Layout from '../Shared/Layout';
import HomePage from '../Pages/HomePage';
import ProfilePage from '../Pages/ProfilePage';
import ChatPage from '../Pages/ChatPage';
import NotFoundPage from '../Pages/NotFoundPage';

import {Navigate} from 'react-router-dom';
import {useStore} from './store';

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
        <Route path='chat' element={<ChatPage />} />
        <Route path='*' element={<NotFoundPage />} />
      </Routes>
    </Router>
  );
};

export default Routing;
