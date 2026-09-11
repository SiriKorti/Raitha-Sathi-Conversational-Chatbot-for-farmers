import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { FoundationPlaceholder } from '../pages/system/FoundationPlaceholder';
import { HomePage } from '../pages/home/HomePage';
import { ChatPage } from '../pages/chat/ChatPage';
import { HistoryPage } from '../pages/history/HistoryPage';
import { FarmPage } from '../pages/farm/FarmPage';
import { LandingPage } from '../pages/landing/LandingPage';
import { LoginPage } from '../pages/auth/LoginPage';
import { RegistrationPage } from '../pages/auth/RegistrationPage';
import { ForgotPasswordPage } from '../pages/auth/ForgotPasswordPage';
import { CropsPage } from '../pages/crops/CropsPage';
import { SchemesPage } from '../pages/schemes/SchemesPage';
import { ExplorePage } from '../pages/explore/ExplorePage';
import { WeatherPage } from '../pages/weather/WeatherPage';
import { MandiPage } from '../pages/mandi/MandiPage';
import { ProgressPage } from '../pages/progress/ProgressPage';
import { SavedAdvicePage } from '../pages/saved/SavedAdvicePage';
import { DiagnosisPage } from '../pages/diagnosis/DiagnosisPage';
import { SettingsPage } from '../pages/system/SettingsPage';
import { HelpPage } from '../pages/system/HelpPage';
import {
  Home,
  MessageSquare,
  History,
  Sprout,
  BookOpen,
  TrendingUp,
  CloudSun,
  Coins,
  ShieldCheck,
  Compass,
  Camera,
  Bookmark,
  Bell,
  User,
  Settings,
  HelpCircle,
  LogIn,
  UserPlus
} from 'lucide-react';

export const router = createBrowserRouter([
  // 1. First Screen when opening the app: 3D Storytelling Experience
  {
    path: '/',
    element: <LandingPage />
  },
  {
    path: '/landing',
    element: <LandingPage />
  },
  {
    path: '/story',
    element: <LandingPage />
  },

  // 2. Second Screen: Farmer Login & Authentication
  {
    path: '/login',
    element: <LoginPage />
  },
  {
    path: '/register',
    element: <RegistrationPage />
  },
  {
    path: '/forgot-password',
    element: <ForgotPasswordPage />
  },

  // 3. Third Screen & Main Application: ChatGPT-like Conversational Workspace
  {
    path: '/app',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/chat" replace />
      },
      {
        path: 'chat',
        element: <ChatPage />
      },
      {
        path: 'chat/:conversationId',
        element: <ChatPage />
      },
      {
        path: 'home',
        element: <HomePage />
      },
      {
        path: 'history',
        element: <HistoryPage />
      },
      {
        path: 'farm',
        element: <FarmPage />
      }
    ]
  },

  // Root level routes inside AppLayout for direct URL navigation
  {
    element: <AppLayout />,
    children: [
      {
        path: '/chat',
        element: <ChatPage />
      },
      {
        path: '/chat/:conversationId',
        element: <ChatPage />
      },
      {
        path: '/dashboard',
        element: <HomePage />
      },
      {
        path: '/history',
        element: <HistoryPage />
      },
      {
        path: '/farm',
        element: <FarmPage />
      },
      {
        path: '/diary',
        element: (
          <FoundationPlaceholder
            pageTitle="Farm Diary"
            pageKey="nav.diary"
            icon={BookOpen}
            phaseTarget="Phase 3"
            isBackendDependent={true}
            backendRequirement="Requires exposing REST endpoints `GET/POST /api/farm/diary/{userId}` in `app/api/routes/farm.py` (which hooks into `app.conversation.farm_diary:FarmDiary`)."
          />
        )
      },
      {
        path: '/crops',
        element: <CropsPage />
      },
      {
        path: '/schemes',
        element: <SchemesPage />
      },
      {
        path: '/explore',
        element: <ExplorePage />
      },
      {
        path: '/weather',
        element: <WeatherPage />
      },
      {
        path: '/mandi',
        element: <MandiPage />
      },
      {
        path: '/progress',
        element: <ProgressPage />
      },
      {
        path: '/diagnosis',
        element: <DiagnosisPage />
      },
      {
        path: '/saved',
        element: <SavedAdvicePage />
      },
      {
        path: '/notifications',
        element: (
          <FoundationPlaceholder
            pageTitle="Alerts & Notifications"
            pageKey="nav.notifications"
            icon={Bell}
            phaseTarget="Phase 3"
          />
        )
      },
      {
        path: '/profile',
        element: (
          <FoundationPlaceholder
            pageTitle="Farmer Profile"
            pageKey="nav.profile"
            icon={User}
            phaseTarget="Phase 3"
          />
        )
      },
      {
        path: '/settings',
        element: <SettingsPage />
      },
      {
        path: '/help',
        element: <HelpPage />
      }
    ]
  },

  // Fallback redirect
  {
    path: '*',
    element: <Navigate to="/" replace />
  }
]);
