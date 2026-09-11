import React from 'react';
import { Outlet } from 'react-router-dom';
import { TopBar } from './TopBar';
import { DesktopSidebar } from './DesktopSidebar';
import { MobileNav } from './MobileNav';
import { Toast } from '../common/Toast';
import './AppLayout.css';

export const AppLayout = () => {
  return (
    <div className="app-viewport">
      <TopBar />
      <div className="app-main-layout">
        <DesktopSidebar />
        <main className="app-content-area">
          <Outlet />
        </main>
      </div>
      <MobileNav />
      <Toast />
    </div>
  );
};
