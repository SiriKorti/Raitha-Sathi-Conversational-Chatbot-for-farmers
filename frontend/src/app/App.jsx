import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import { AppProviders } from './providers';
import { FloatingBackground } from '../components/common/FloatingBackground';

export const App = () => {
  return (
    <AppProviders>
      <FloatingBackground />
      <RouterProvider router={router} />
    </AppProviders>
  );
};

