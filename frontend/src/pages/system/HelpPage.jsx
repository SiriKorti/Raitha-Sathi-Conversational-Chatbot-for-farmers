import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  HelpCircle,
  Search,
  X,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  MessageSquare,
  CloudSun,
  Sprout,
  Camera,
  Building2,
  Volume2,
  Send
} from 'lucide-react';

import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import './HelpPage.css';

export const HelpPage = () => {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const { showToast } = useToast();

  const isKn = language === 'kn';

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [expandedFaqId, setExpandedFaqId] = useState('faq-1');
  const [copiedFaqId, setCopiedFaqId] = useState(null);

  // Categories
  const categories = [
    { id: 'all', label: isKn ? 'ಎಲ್ಲಾ ವಿಷಯಗಳು' : 'All Topics', icon: HelpCircle },
    { id: 'weather', label: isKn ? 'ಹವಾಮಾನ & ಸಿಂಪಡಣೆ' : 'Weather & Spray', icon: CloudSun },
    { id: 'crops', label: isKn ? 'ಬೆಳೆ & ನೀರಾವರಿ' : 'Crops & Irrigation', icon: Sprout },
    { id: 'diagnosis', label: isKn ? 'ಎಲೆ ರೋಗ ಪರೀಕ್ಷೆ' : 'Visual Diagnosis', icon: Camera },
    { id: 'schemes', label: isKn ? 'ಯೋಜನೆ & ಮಾರುಕಟ್ಟೆ' : 'Schemes & Mandi', icon: Building2 },
    { id: 'app', label: isKn ? 'ಆ್ಯಪ್ & ಧ್ವನಿ ಬಳಕೆ' : 'App & Voice Mode', icon: Volume2 },
  ];

  // Curated FAQs
  const faqs = [
    {
      id: 'faq-1',
      category: 'weather',
      tag: isKn ? 'ಹವಾಮಾನ & ಸಿಂಪಡಣೆ' : 'Weather & Spray Safety',
      question: isKn
        ? 'ವಿಜಯಪುರ ಅಥವಾ ನನ್ನ ಜಿಲ್ಲೆಯ ಇಂದಿನ ಹವಾಮಾನ ಮತ್ತು ಕೀಟನಾಶಕ ಸಿಂಪಡಣೆ ಸುರಕ್ಷತೆ ಪರಿಶೀಲಿಸುವುದು ಹೇಗೆ?'
        : 'How do I check today\'s weather and pesticide spray safety for Vijayapura or my district?',
      answer: isKn
        ? 'ರೈತ ಸಾಥಿ ಚಾಟ್‌ನಲ್ಲಿ (Ask Sathi) ಅಥವಾ "ಹವಾಮಾನ ಸಲಹೆ" ಪುಟದಲ್ಲಿ ನಿಮ್ಮ ಜಿಲ್ಲೆಯ ಹೆಸರು ಮತ್ತು ಸಿಂಪಡಣೆ ಬಗ್ಗೆ ಕೇಳಿ (ಉದಾ: "ವಿಜಯಪುರ ಜಿಲ್ಲೆಯಲ್ಲಿ ಇಂದಿನ ಹವಾಮಾನ ಹೇಗಿದೆ? ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸುವುದು ಸುರಕ್ಷಿತವೇ?"). ನಮ್ಮ ಸಿಸ್ಟಮ್ ಲೈವ್ ತಾಪಮಾನ, ಆರ್ದ್ರತೆ, ಗಾಳಿಯ ವೇಗ ಮತ್ತು ಮುಂದಿನ ೬ ಗಂಟೆಗಳ ಮಳೆಯ ಅಪಾಯವನ್ನು ಪರೀಕ್ಷಿಸಿ, ಕೀಟನಾಶಕ ಅಥವಾ ಗೊಬ್ಬರ ಸಿಂಪಡಿಸಲು ಸೂಕ್ತವೇ ಎಂದು ಸ್ಪಷ್ಟವಾಗಿ ತಿಳಿಸುತ್ತದೆ.'
        : 'Ask in Ask Sathi chat or visit the Weather Advisory page (e.g., "How is the weather in Vijayapura today? Is it safe to spray pesticide?"). Our agrometeorological engine retrieves real-time temperature, humidity, wind velocity, and evaluates the critical 6-hour rainfastness window to give an immediate safety recommendation.',
      prompt: isKn
        ? 'ವಿಜಯಪುರ ಜಿಲ್ಲೆಯಲ್ಲಿ ಇಂದಿನ ಹವಾಮಾನ ಹೇಗಿದೆ? ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸುವುದು ಸುರಕ್ಷಿತವೇ?'
        : 'How is the weather today in Vijayapura district? Is it safe to spray pesticides?'
    },
    {
      id: 'faq-2',
      category: 'crops',
      tag: isKn ? 'ಬೆಳೆ & ನೀರಾವರಿ' : 'Crops & Irrigation',
      question: isKn
        ? 'ಹೆಚ್ಚಿನ ತಾಪಮಾನ ಅಥವಾ ಮಳೆಗಾಲದಲ್ಲಿ ತೋಟಗಾರಿಕಾ ಬೆಳೆಗಳಿಗೆ ನೀರಾವರಿ ನಿರ್ವಹಣೆ ಹೇಗೆ ಮಾಡಬೇಕು?'
        : 'How should irrigation and heat stress be managed for horticultural crops during high temperatures?',
      answer: isKn
        ? 'ತಾಪಮಾನ ಹೆಚ್ಚಾದಾಗ (ಬೇಸಿಗೆ/ಬಿಸಿಲು): ೧) ಹನಿ ನೀರಾವರಿ (Drip) ಬಳಸಿ, ೨) ಮಧ್ಯಾಹ್ನ ನೀರುಣಿಸುವುದನ್ನು ತಪ್ಪಿಸಿ, ಮುಂಜಾನೆ (೬-೯) ಅಥವಾ ಸಂಜೆ (೫ ರ ನಂತರ) ನೀರುಣಿಸಿ, ೩) ಗಿಡಗಳ ಬುಡಕ್ಕೆ ಒಣಹುಲ್ಲು ಅಥವಾ ಕಬ್ಬಿನ ರೇಕಿನಿಂದ ಮಣ್ಣಿನ ಹೊದಿಕೆ (ಮಲ್ಚಿಂಗ್) ಮಾಡಿ ತೇವಾಂಶ ಸಂರಕ್ಷಿಸಿ, ೪) ತೋಟದ ತಾಪಮಾನ ತಗ್ಗಿಸಲು ಮಧ್ಯಾಹ್ನ ಲಘು ತುಂತುರು ನೀರಾವರಿ ಚಲಾಯಿಸಿ. ಸಾಥಿ ಚಾಟ್‌ನಲ್ಲಿ "ವಿಜಯಪುರ ತಾಪಮಾನ ಹೆಚ್ಚಾಗಿದ್ದರೆ ತೋಟಗಾರಿಕಾ ಬೆಳೆಗಳಿಗೆ ನೀರಾವರಿ ನಿರ್ವಹಣೆ ಹೇಗೆ ಮಾಡಬೇಕು?" ಎಂದು ಕೇಳಿದರೆ ಸಂಪೂರ್ಣ ಮಾರ್ಗದರ್ಶಿ ದೊರೆಯುತ್ತದೆ.'
        : 'Under extreme heat: 1) Deploy drip irrigation to conserve 40-50% root-zone moisture, 2) Avoid watering during scorching midday heat (11 AM–4 PM); schedule irrigation in early morning or late evening, 3) Apply 3–4 inches of organic mulch (paddy straw/sugarcane trash) to lower soil root temperature, 4) Run overhead micro-sprinklers for 15-20 min in high heat to drop orchard canopy temperatures.',
      prompt: isKn
        ? 'ವಿಜಯಪುರ ತಾಪಮಾನ ಹೆಚ್ಚಾಗಿದ್ದರೆ ತೋಟಗಾರಿಕಾ ಬೆಳೆಗಳಿಗೆ ನೀರಾವರಿ ನಿರ್ವಹಣೆ ಹೇಗೆ ಮಾಡಬೇಕು?'
        : 'If temperature is high in Vijayapura, how to manage irrigation for horticultural crops?'
    },
    {
      id: 'faq-3',
      category: 'diagnosis',
      tag: isKn ? 'ರೋಗ ಪರೀಕ್ಷೆ' : 'Visual Plant Diagnosis',
      question: isKn
        ? 'ಕ್ಯಾಮೆರಾ ಮೂಲಕ ಎಲೆಯ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಬೆಳೆ ರೋಗ ಪತ್ತೆ ಹಚ್ಚುವುದು ಹೇಗೆ?'
        : 'How do I use the Visual Diagnosis feature to identify plant diseases from a leaf photo?',
      answer: isKn
        ? 'ಎಡಭಾಗದ ಮೆನುವಿನಲ್ಲಿ "ಎಲೆ ರೋಗ ಪರೀಕ್ಷೆ" (Visual Diagnosis) ಕ್ಲಿಕ್ ಮಾಡಿ. ನಿಮ್ಮ ಮೊಬೈಲ್ ಕ್ಯಾಮೆರಾದಿಂದ ಬಾಧಿತ ಎಲೆ ಅಥವಾ ಕಾಯಿಯ ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆಯಿರಿ ಅಥವಾ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ. ಅಗತ್ಯವಿದ್ದರೆ ಬೆಳೆಯ ಹೆಸರನ್ನು ನಮೂದಿಸಿ "ಫೋಟೋ ಪರೀಕ್ಷಿಸಿ" ಬಟನ್ ಒತ್ತಿ. ಕಂಪ್ಯೂಟರ್ ವಿಷನ್ ಮತ್ತು AI ಮಾದರಿಯು ರೋಗದ ಲಕ್ಷಣ, ಶಿಲೀಂಧ್ರ/ಕೀಟ ಕಾರಣಗಳು, ಮತ್ತು ರಾಸಾಯನಿಕ ಹಾಗೂ ಸಾವಯವ ಔಷಧಗಳ ಶಿಫಾರಸುಗಳನ್ನು ನಿಖರವಾಗಿ ನೀಡುತ್ತದೆ.'
        : 'Navigate to "Visual Diagnosis" in the navigation bar. Upload or snap a well-lit close-up photograph of the diseased crop leaf, stem, or fruit. You can optionally specify the crop name. Click "Analyze Plant Image" to receive instant AI disease classification, observed symptoms, causative pathogen info, and actionable chemical/organic control measures.',
      prompt: isKn
        ? 'ದಾಳಿಂಬೆ ಬೆಳೆಯಲ್ಲಿ ದುಂಡಾಣು ಅಂಗಮಾರಿ (ಬ್ಯಾಕ್ಟೀರಿಯಲ್ ಬ್ಲೈಟ್) ರೋಗದ ಲಕ್ಷಣಗಳು ಮತ್ತು ನಿಯಂತ್ರಣ ಕ್ರಮಗಳು ಯಾವುವು?'
        : 'What are the symptoms and control measures for Bacterial Blight in pomegranate?'
    },
    {
      id: 'faq-4',
      category: 'schemes',
      tag: isKn ? 'ಸರ್ಕಾರಿ ಯೋಜನೆ' : 'Govt Schemes & Subsidies',
      question: isKn
        ? 'ಕರ್ನಾಟಕ ಭೂಮಿ ಆನ್‌ಲೈನ್ ಪಹಣಿ (RTC) ಮತ್ತು ಸರ್ಕಾರದ ಕೃಷಿ ಸಬ್ಸಿಡಿಗಳ ಮಾಹಿತಿ ಪಡೆಯುವುದು ಹೇಗೆ?'
        : 'How do I get information on Karnataka Bhoomi RTC, PM-Kisan, and agriculture subsidies?',
      answer: isKn
        ? 'ಮೆನುವಿನಲ್ಲಿರುವ "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು" ವಿಭಾಗದಲ್ಲಿ ಅಥವಾ ನೇರವಾಗಿ ಸಾಥಿ ಜೊತೆ ಚಾಟ್ ಮಾಡಿ ಕೇಳಿ (ಉದಾ: "ಕರ್ನಾಟಕ ಭೂಮಿ ಸೇವೆ ಆರ್‌ಟಿಸಿ ಪಹಣಿ ಅರ್ಜಿ ವಿಧಾನ ತಿಳಿಸಿ", "ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ೧೯ನೇ ಕಂತು", "ಹನಿ ನೀರಾವರಿಗೆ ಸಬ್ಸಿಡಿ ಪಡೆಯುವುದು ಹೇಗೆ?"). ಅರ್ಹತೆ, ಬೇಕಾಗುವ ದಾಖಲೆಗಳು, ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್ ಲಿಂಕ್‌ಗಳು ಮತ್ತು ಸಹಾಯವಾಣಿ ಸಂಖ್ಯೆಗಳನ್ನು ಕ್ಷಣಾರ್ಧದಲ್ಲಿ ಒದಗಿಸಲಾಗುತ್ತದೆ.'
        : 'Visit the "Govt Schemes" page or ask directly in chat (e.g., "Karnataka Bhoomi RTC online application procedure", "PM-Kisan subsidy eligibility", "Drip irrigation subsidy in Karnataka"). You will receive structured details covering subsidy percentage, eligibility criteria, required documents, and official portal links.',
      prompt: isKn
        ? 'ಕರ್ನಾಟಕ ಭೂಮಿ ಸೇವೆ (ಆರ್‌ಟಿಸಿ / ಪಹಣಿ) ಯೋಜನೆಯ ಅರ್ಹತೆ ಮತ್ತು ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಸಂಪೂರ್ಣ ವಿಧಾನ ತಿಳಿಸಿ.'
        : 'Explain Karnataka Bhoomi RTC service eligibility and step-by-step application procedure.'
    },
    {
      id: 'faq-5',
      category: 'schemes',
      tag: isKn ? 'ಮಾರುಕಟ್ಟೆ ದರ' : 'Mandi APMC Prices',
      question: isKn
        ? 'ಕರ್ನಾಟಕದ ವಿವಿಧ ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆಗಳಲ್ಲಿ ಇಂದಿನ ಬೆಳೆಗಳ ಧಾರಣೆ (Mandi Prices) ತಿಳಿಯುವುದು ಹೇಗೆ?'
        : 'How can I check current crop market prices across APMC mandis in Karnataka?',
      answer: isKn
        ? '"ಮಾರುಕಟ್ಟೆ ದರ" (Mandi Market) ಪುಟಕ್ಕೆ ಭೇಟಿ ನೀಡಿ ಜಿಲ್ಲೆ ಮತ್ತು ಬೆಳೆಯನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಿ, ಅಥವಾ ಚಾಟ್‌ನಲ್ಲಿ ನೇರವಾಗಿ ಕೇಳಿ: "ಗದಗ ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಈರುಳ್ಳಿ ಬೆಲೆ ಎಷ್ಟಿದೆ?" ಅಥವಾ "ವಿಜಯಪುರ ಜೋಳ ಕ್ವಿಂಟಾಲ್ ದರ ತಿಳಿಸಿ". ಆಯಾ ದಿನದ ಕನಿಷ್ಠ, ಗರಿಷ್ಠ ಮತ್ತು ಮಾದರಿ ದರಗಳ ನೈಜ ಮಾಹಿತಿ ಸಿಗುತ್ತದೆ.'
        : 'Visit the "Mandi Market" dashboard to filter by district and crop, or ask directly in chat: "What is the onion price in Gadag APMC today?" or "Current Jowar mandi price in Vijayapura". The system fetches min, max, and modal prices per quintal.',
      prompt: isKn
        ? 'ಗದಗ ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಇಂದಿನ ಈರುಳ್ಳಿ ಮತ್ತು ಹತ್ತಿ ಧಾರಣೆ ಎಷ್ಟಿದೆ?'
        : 'What is today\'s market price for onion and cotton in Gadag APMC?'
    },
    {
      id: 'faq-6',
      category: 'app',
      tag: isKn ? 'ಧ್ವನಿ ಸಂಭಾಷಣೆ' : 'Voice Mode & Audio',
      question: isKn
        ? 'ಕನ್ನಡದಲ್ಲೇ ಧ್ವನಿ (Voice / ಮೈಕ್ರೋಫೋನ್) ಮೂಲಕ ಮಾತನಾಡಿ ಪ್ರಶ್ನೆ ಕೇಳಬಹುದಾ?'
        : 'Can I speak in Kannada using the microphone to ask questions?',
      answer: isKn
        ? 'ಹೌದು! ರೈತ ಸಾಥಿ ಚಾಟ್‌ನಲ್ಲಿ ಸಂದೇಶ ಟೈಪ್ ಮಾಡುವ ಜಾಗದ ಪಕ್ಕದಲ್ಲಿರುವ ಮೈಕ್ರೋಫೋನ್ (🎙️) ಐಕಾನ್ ಒತ್ತಿ. ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ನೇರವಾಗಿ ಮಾತನಾಡಿ. ನಿಮ್ಮ ಧ್ವನಿಯನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಗ್ರಹಿಸಿ ಉತ್ತರ ನೀಡಲಾಗುತ್ತದೆ. ಅಲ್ಲದೆ ಉತ್ತರವನ್ನು ಧ್ವನಿ ಮೂಲಕ ಆಲಿಸಲು ಸ್ಪೀಕರ್ (🔊) ಬಟನ್ ಒತ್ತಬಹುದು.'
        : 'Yes! In the Ask Sathi chat composer, click the Microphone (🎙️) icon. Speak naturally in Kannada or English. The speech-to-text engine transcribes your voice query in real time. You can also listen to audio readouts of advice using the speaker icon.',
      prompt: isKn
        ? 'ನಮಸ್ಕಾರ ರೈತ ಸಾಥಿ, ತೆಂಗು ಬೆಳೆಯಲ್ಲಿ ನುಸಿ ರೋಗದ ನಿಯಂತ್ರಣಕ್ಕೆ ಯಾವ ಔಷಧಿ ಸಿಂಪಡಿಸಬೇಕು?'
        : 'Hello Raitha Sathi, what medicine should be sprayed to control mite disease in coconut?'
    },
    {
      id: 'faq-7',
      category: 'app',
      tag: isKn ? 'ಸಲಹೆ ಉಳಿಸಿ' : 'Saved Advice / Bookmarking',
      question: isKn
        ? 'ಉಪಯುಕ್ತ ಕೃಷಿ ಸಲಹೆಗಳನ್ನು ನಂತರ ಪರಿಶೀಲಿಸಲು ಉಳಿಸಿಕೊಳ್ಳುವುದು (Saved Advice) ಹೇಗೆ?'
        : 'How do I bookmark and access saved agricultural advisories for future reference?',
      answer: isKn
        ? 'ಚಾಟ್‌ನಲ್ಲಿ ಯಾವುದೇ ಉತ್ತರದ ಕೆಳಗೆ ಕಾಣುವ "ಸಲಹೆ ಉಳಿಸಿ" (🔖 Bookmark) ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ. ನಿಮ್ಮ ಎಲ್ಲಾ ಉಳಿಸಿದ ಸಲಹೆಗಳು ಎಡಭಾಗದ "ಉಳಿಸಿದ ಸಲಹೆಗಳು" (Saved Advice) ಪುಟದಲ್ಲಿ ಸುಲಭವಾಗಿ ದೊರೆಯುತ್ತವೆ. ಅಗತ್ಯವಿದ್ದಾಗ ಅಲ್ಲಿಂದಲೇ ಮತ್ತೆ ಓದಬಹುದು ಅಥವಾ ನಕಲಿಸಬಹುದು.'
        : 'Below any assistant response in chat or visual diagnosis, click the Bookmark icon (🔖 "Save Advice"). All your saved advisories will be cataloged on the "Saved Advice" page for offline access and quick reference.',
      prompt: isKn
        ? 'ದ್ರಾಕ್ಷಿ ಬೆಳೆಯಲ್ಲಿ ಡೌನಿ ಮಿಲ್ಡ್ಯೂ (ಬೂದಿ ರೋಗ) ರೋಗ ನಿರ್ವಹಣೆಗೆ ಮುನ್ನೆಚ್ಚರಿಕೆ ಕ್ರಮಗಳು ಯಾವುವು?'
        : 'What are preventive measures for Downy Mildew disease management in grapes?'
    },
    {
      id: 'faq-8',
      category: 'crops',
      tag: isKn ? 'ನನ್ನ ಜಮೀನು' : 'Farm Profile & Progress',
      question: isKn
        ? 'ನನ್ನ ಜಮೀನಿನ ವಿವರ (Farm Profile) ಮತ್ತು ಬೆಳೆ ಪ್ರಗತಿ ಹಂತಗಳನ್ನು ದಾಖಲಿಸುವುದು ಹೇಗೆ?'
        : 'How do I configure my farm profile and track crop growth progress?',
      answer: isKn
        ? '"ನನ್ನ ಜಮೀನು" (My Farm) ಮತ್ತು "ಬೆಳೆ ಹಂತಗಳು" (Crop Progress) ಪುಟಗಳಲ್ಲಿ ನಿಮ್ಮ ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ, ಮಣ್ಣಿನ ವಿಧ (ಕಪ್ಪು/ಕೆಂಪು ಮಣ್ಣು), ನೀರಾವರಿ ಮೂಲ (ಬೋರ್‌ವೆಲ್/ಕಾಲುವೆ) ಮತ್ತು ನೀವು ಬೆಳೆಯುವ ಬೆಳೆಗಳನ್ನು ಸೇರಿಸಿ. ರೈತ ಸಾಥಿ ನಿಮ್ಮ ಜಮೀನಿನ ಪರಿಸ್ಥಿತಿಗೆ ತಕ್ಕಂತೆ ಕಸ್ಟಮೈಸ್ ಮಾಡಿದ ಸಲಹೆಗಳನ್ನು ನೀಡುತ್ತದೆ.'
        : 'Use "My Farm" and "Crop Progress" in the sidebar to set your district, soil type (black/red soil), water source, and standing crops. Raitha Sathi personalizes pest, fertilizer, and irrigation advice based on your configured farm profile.',
      prompt: isKn
        ? 'ಕಪ್ಪು ಮಣ್ಣಿನಲ್ಲಿ ಹಿಂಗಾರು ಜೋಳ ಬಿತ್ತನೆಗೆ ಸೂಕ್ತ ಸಮಯ ಮತ್ತು ಬೀಜೋಪಚಾರ ವಿಧಾನ ತಿಳಿಸಿ.'
        : 'What is the ideal sowing time and seed treatment method for Rabi Jowar in black soil?'
    }
  ];

  // Filtered FAQs
  const filteredFaqs = useMemo(() => {
    return faqs.filter(faq => {
      const matchesCategory = activeCategory === 'all' || faq.category === activeCategory;
      const q = searchQuery.toLowerCase().trim();
      if (!q) return matchesCategory;

      const matchesSearch =
        faq.question.toLowerCase().includes(q) ||
        faq.answer.toLowerCase().includes(q) ||
        faq.tag.toLowerCase().includes(q);

      return matchesCategory && matchesSearch;
    });
  }, [faqs, activeCategory, searchQuery]);

  // Handlers
  const handleToggleFaq = (id) => {
    setExpandedFaqId(prev => (prev === id ? null : id));
  };

  const handleCopyFaq = async (faq) => {
    try {
      const textToCopy = `Q: ${faq.question}\n\nA: ${faq.answer}`;
      await navigator.clipboard.writeText(textToCopy);
      setCopiedFaqId(faq.id);
      showToast(isKn ? 'ಪ್ರಶ್ನೆ ಮತ್ತು ಉತ್ತರವನ್ನು ನಕಲಿಸಲಾಗಿದೆ.' : 'Question & answer copied to clipboard.', 'success');
      setTimeout(() => setCopiedFaqId(null), 2500);
    } catch {
      showToast(faq.question, 'info');
    }
  };

  const handleAskInChat = (promptText) => {
    navigate('/chat', { state: { prompt: promptText } });
  };

  return (
    <div className="help-page-container animate-fade-in">
      {/* ── Hero Header ─────────────────────────────────────── */}
      <Card glass={true} className="help-hero-card">
        <div className="help-hero-content">
          <div className="help-icon-wrapper">
            <HelpCircle size={36} />
          </div>
          <div className="help-hero-text">
            <div className="help-title-row">
              <h1 className="help-main-title">
                {isKn ? 'ಸಾಮಾನ್ಯ ಪ್ರಶ್ನೋತ್ತರಗಳು (FAQ)' : 'Frequently Asked Questions (FAQ)'}
              </h1>
              <span className="faq-count-badge">
                {filteredFaqs.length} {isKn ? 'ಪ್ರಶ್ನೆಗಳು' : 'Questions'}
              </span>
            </div>
            <p className="help-subtitle">
              {isKn
                ? 'ರೈತ ಸಾಥಿ ಬಳಕೆ, ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ, ರೋಗ ನಿರ್ಣಯ, ಮಾರುಕಟ್ಟೆ ದರ ಮತ್ತು ಕೃಷಿ ಸಲಹೆಗಳ ಬಗ್ಗೆ ಹೆಚ್ಚಾಗಿ ಕೇಳಲಾಗುವ ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಗಳು.'
                : 'Answers to frequently asked questions about using Raitha Sathi, weather forecasts, disease diagnosis, mandi rates, and crop advisories.'}
            </p>
          </div>
        </div>

        {/* ── Interactive Search Box ──────────────────────────── */}
        <div className="help-search-container">
          <div className="help-search-input-wrapper">
            <Search className="help-search-icon" size={20} />
            <input
              type="text"
              className="help-search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={
                isKn
                  ? 'ಪ್ರಶ್ನೆಗಳನ್ನು ಹುಡುಕಿ... (ಉದಾ: ಹವಾಮಾನ, ರೋಗ, ನೀರಾವರಿ, ಬೆಳೆ ವಿಮೆ, ಸಿಂಪಡಣೆ)'
                  : 'Search questions... (e.g., weather, spray, irrigation, disease, subsidy)'
              }
            />
            {searchQuery && (
              <button
                className="help-search-clear"
                onClick={() => setSearchQuery('')}
                title={isKn ? 'ಅಳಿಸಿ' : 'Clear'}
              >
                <X size={18} />
              </button>
            )}
          </div>
        </div>
      </Card>

      {/* ── Category Tabs ──────────────────────────────────── */}
      <div className="help-section">
        <div className="category-tabs-row">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const isActive = activeCategory === cat.id;
            return (
              <button
                key={cat.id}
                className={`category-pill ${isActive ? 'active' : ''}`}
                onClick={() => setActiveCategory(cat.id)}
              >
                <Icon size={16} />
                <span>{cat.label}</span>
              </button>
            );
          })}
        </div>

        {/* FAQ Accordion List */}
        {filteredFaqs.length === 0 ? (
          <Card className="help-empty-card">
            <HelpCircle size={40} className="empty-icon text-muted" />
            <h3>{isKn ? 'ಯಾವುದೇ ಪ್ರಶ್ನೆ ಕಂಡುಬಂದಿಲ್ಲ' : 'No matching questions found'}</h3>
            <p>
              {isKn
                ? 'ಬೇರೆ ಕೀವರ್ಡ್‌ನೊಂದಿಗೆ ಹುಡುಕಿ ಅಥವಾ ನೇರವಾಗಿ ಸಾಥಿ ಚಾಟ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಪ್ರಶ್ನೆ ಕೇಳಿ.'
                : 'Try searching with different keywords or ask your question directly in Ask Sathi.'}
            </p>
            <Button
              variant="primary"
              icon={MessageSquare}
              onClick={() => navigate('/chat')}
            >
              {isKn ? 'ಸಾಥಿ ಜೊತೆ ಚರ್ಚಿಸಿ' : 'Open Ask Sathi Chat'}
            </Button>
          </Card>
        ) : (
          <div className="faq-accordion-list">
            {filteredFaqs.map((faq) => {
              const isExpanded = expandedFaqId === faq.id;
              return (
                <div
                  key={faq.id}
                  className={`faq-item-card ${isExpanded ? 'expanded' : ''}`}
                >
                  <button
                    className="faq-question-btn"
                    onClick={() => handleToggleFaq(faq.id)}
                    aria-expanded={isExpanded}
                  >
                    <div className="faq-question-left">
                      <span className="faq-tag-pill">{faq.tag}</span>
                      <span className="faq-question-text">{faq.question}</span>
                    </div>
                    <div className="faq-expand-icon">
                      {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="faq-answer-pane animate-fade-in">
                      <p className="faq-answer-text">{faq.answer}</p>
                      
                      <div className="faq-answer-footer">
                        <div className="faq-footer-left">
                          <button
                            className="faq-action-btn"
                            onClick={() => handleCopyFaq(faq)}
                            title={isKn ? 'ನಕಲಿಸಿ' : 'Copy'}
                          >
                            {copiedFaqId === faq.id ? (
                              <>
                                <Check size={14} className="text-success" />
                                <span className="text-success">{isKn ? 'ನಕಲಿಸಲಾಗಿದೆ' : 'Copied'}</span>
                              </>
                            ) : (
                              <>
                                <Copy size={14} />
                                <span>{isKn ? 'ಪ್ರಶ್ನೋತ್ತರ ನಕಲಿಸಿ' : 'Copy Q&A'}</span>
                              </>
                            )}
                          </button>
                        </div>

                        {faq.prompt && (
                          <button
                            className="faq-ask-sathi-btn"
                            onClick={() => handleAskInChat(faq.prompt)}
                          >
                            <Send size={14} />
                            <span>{isKn ? 'ಸಾಥಿ ಜೊತೆ ಚರ್ಚಿಸಿ' : 'Ask in Sathi Chat'}</span>
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
export default HelpPage;
