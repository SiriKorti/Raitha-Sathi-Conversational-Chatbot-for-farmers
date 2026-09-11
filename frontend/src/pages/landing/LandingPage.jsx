import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ChevronDown,
  Leaf,
  MessageSquare,
  BookOpen,
  Sprout,
  MapPin,
  Layers,
  Droplets,
  Globe,
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { ThemeSelector } from '../../components/common/ThemeSelector';
import farmerHeroImg from '../../assets/farmer_hero.jpg';
import './LandingPage.css';

/* ── Section reveal hook ─────────────────────────────────────── */
function useReveal(threshold = 0.18) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold }
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [threshold]);
  return [ref, visible];
}

/* ── Staggered children reveal ───────────────────────────────── */
function StaggerList({ items, renderItem }) {
  const [ref, visible] = useReveal(0.12);
  return (
    <div ref={ref} className={`stagger-list ${visible ? 'revealed' : ''}`}>
      {items.map((item, i) => (
        <div key={i} className="stagger-item" style={{ '--i': i }}>
          {renderItem(item, i)}
        </div>
      ))}
    </div>
  );
}

/* ── Sticky story section ────────────────────────────────────── */
function StoryStep({ step, icon: Icon, title, body, isActive, onSelect }) {
  return (
    <div
      className={`story-step ${isActive ? 'step-active' : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') onSelect?.(); }}
    >
      <div className="step-indicator">
        <span className="step-number">{String(step).padStart(2, '0')}</span>
      </div>
      <div className="step-content">
        <div className="step-icon-wrap">
          <Icon size={22} />
        </div>
        <h3 className="step-title">{title}</h3>
        <p className="step-body">{body}</p>
      </div>
    </div>
  );
}

/* ── Farmer question cards ───────────────────────────────────── */
const farmerQuestions = [
  { q: "ಎಲೆಗಳು ಹಳದಿ ಬಣ್ಣಕ್ಕೆ ತಿರುಗುತ್ತಿವೆ. ಕಾರಣ ಏನು?", en: "Why are my leaves turning yellow?" },
  { q: "ನೀರಾವರಿ ಯಾವಾಗ ಮಾಡಬೇಕು?", en: "When should I irrigate?" },
  { q: "ಮಣ್ಣಿನ ಗುಣಮಟ್ಟ ಸುಧಾರಿಸಲು ಏನು ಮಾಡಬೇಕು?", en: "How can I improve my soil?" },
  { q: "ಯಾವ ಗೊಬ್ಬರ ಉತ್ತಮ?", en: "Which fertilizer should I use?" },
];

/* ══════════════════════════════════════════════════════════════ */
export const LandingPage = () => {
  const navigate = useNavigate();
  const { language, setLanguage } = useLanguage();
  const isKn = language === 'kn';

  const [activeStep, setActiveStep] = useState(0);
  const storyRef = useRef(null);

  const storySteps = [
    {
      step: 1,
      icon: MessageSquare,
      title: isKn ? "ಕೇಳಿ (Ask)" : "Ask",
      body: isKn
        ? "ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಯನ್ನು ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಕೇಳಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ. ಯಾವುದೇ ಸಂಕೀರ್ಣ ಫಾರ್ಮ್‌ಗಳಿಲ್ಲ."
        : "Type or speak your farming question in Kannada or English. No forms. No complexity.",
    },
    {
      step: 2,
      icon: BookOpen,
      title: isKn ? "ಅರ್ಥೈಸಿಕೊಳ್ಳಿ (Understand)" : "Understand",
      body: isKn
        ? "ಉತ್ತರಿಸುವ ಮುನ್ನ ಸಾಥಿ ನಿಮ್ಮ ಬೆಳೆ ಮತ್ತು ಜಮೀನಿನ ಸನ್ನಿವೇಶವನ್ನು ಕೃಷಿ ಜ್ಞಾನಕೋಶದಿಂದ ಪರಿಶೀಲಿಸುತ್ತದೆ."
        : "Sathi searches agricultural knowledge to understand your field's context before responding.",
    },
    {
      step: 3,
      icon: Leaf,
      title: isKn ? "ಪರಿಹಾರ ಪಡೆಯಿರಿ (Respond)" : "Respond",
      body: isKn
        ? "ನಿಮ್ಮ ಬೆಳೆ, ಮಣ್ಣಿನ ವಿಧ ಮತ್ತು ಪ್ರಸ್ತುತ ಋತುವಿಗೆ ಸೂಕ್ತವಾದ ಸ್ಪಷ್ಟ, ಪ್ರಾಯೋಗಿಕ ಸಲಹೆಗಳನ್ನು ಪಡೆಯಿರಿ."
        : "Receive clear, practical guidance tailored to your crop, soil type, and current season.",
    },
    {
      step: 4,
      icon: Sprout,
      title: isKn ? "ಮುಂದುವರಿಸಿ (Continue)" : "Continue",
      body: isKn
        ? "ಸಹಜವಾಗಿ ಮುಂದಿನ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಿ. ಸಾಥಿ ನಿಮ್ಮ ಹಿಂದಿನ ಸಂಭಾಷಣೆಯನ್ನು ನೆನಪಿಟ್ಟುಕೊಳ್ಳುತ್ತದೆ."
        : "Ask follow-up questions naturally. Sathi remembers your conversation.",
    },
  ];

  const farmDetails = [
    { icon: MapPin, label: isKn ? "ಸ್ಥಳ" : "Location", value: isKn ? "ಮಂಡ್ಯ ಜಿಲ್ಲೆ, ಕರ್ನಾಟಕ" : "Mandya District, Karnataka" },
    { icon: Sprout, label: isKn ? "ಬೆಳೆ" : "Crop", value: isKn ? "ಕಬ್ಬು, ಭತ್ತ" : "Sugarcane, Paddy" },
    { icon: Layers, label: isKn ? "ಮಣ್ಣಿನ ವಿಧ" : "Soil Type", value: isKn ? "ಕಪ್ಪು ಹತ್ತಿ ಮಣ್ಣು" : "Black Cotton Soil" },
    { icon: Droplets, label: isKn ? "ನೀರಾವರಿ" : "Irrigation", value: isKn ? "ಹನಿ ನೀರಾವರಿ ಪದ್ಧತಿ" : "Drip System" },
  ];

  // Dynamic scroll & viewport focus tracking for Story Steps
  useEffect(() => {
    const calculateActiveStep = () => {
      if (!storyRef.current) return;
      const stepElements = storyRef.current.querySelectorAll('.story-step');
      if (!stepElements || stepElements.length === 0) return;

      const focusPoint = window.innerHeight * 0.45;
      let closestIndex = 0;
      let minDistance = Infinity;

      stepElements.forEach((el, index) => {
        const rect = el.getBoundingClientRect();
        const elementCenter = rect.top + rect.height / 2;
        const distance = Math.abs(elementCenter - focusPoint);

        if (distance < minDistance) {
          minDistance = distance;
          closestIndex = index;
        }
      });

      setActiveStep((prev) => (prev !== closestIndex ? closestIndex : prev));
    };

    window.addEventListener('scroll', calculateActiveStep, { passive: true });
    window.addEventListener('resize', calculateActiveStep, { passive: true });
    window.addEventListener('touchmove', calculateActiveStep, { passive: true });
    window.addEventListener('wheel', calculateActiveStep, { passive: true });

    calculateActiveStep();

    return () => {
      window.removeEventListener('scroll', calculateActiveStep);
      window.removeEventListener('resize', calculateActiveStep);
      window.removeEventListener('touchmove', calculateActiveStep);
      window.removeEventListener('wheel', calculateActiveStep);
    };
  }, []);

  // Reveal hooks
  const [heroRef, heroVisible] = useReveal(0.05);
  const [farmerRef, farmerVisible] = useReveal(0.15);
  const [meetRef, meetVisible] = useReveal(0.15);
  const [farmRef, farmVisible] = useReveal(0.15);
  const [ctaRef, ctaVisible] = useReveal(0.15);

  return (
    <div className="landing-root">

      {/* ── NAVBAR ────────────────────────────────────────────── */}
      <nav className="landing-nav" role="navigation" aria-label="Main navigation">
        <div className="landing-nav-inner">
          <a href="/" className="nav-brand" aria-label="Raitha Sathi home">
            <span className="nav-brand-leaf" aria-hidden="true">🌾</span>
            <span className="nav-brand-name">{isKn ? 'ರೈತ ಸಾಥಿ' : 'Raitha Sathi'}</span>
          </a>

          <div className="nav-links" role="list">
            <a href="#how-it-works" className="nav-link" role="listitem">
              {isKn ? 'ಕಾರ್ಯವೈಖರಿ' : 'How it Works'}
            </a>
            <a href="#features" className="nav-link" role="listitem">
              {isKn ? 'ವೈಶಿಷ್ಟ್ಯಗಳು' : 'Features'}
            </a>
            <a href="#about" className="nav-link" role="listitem">
              {isKn ? 'ನಮ್ಮ ಬಗ್ಗೆ' : 'About'}
            </a>
          </div>

          <div className="nav-actions">
            {/* Language Selection: EN / ಕನ್ನಡ */}
            <div className="landing-lang-toggle" role="group" aria-label="Language selection">
              <Globe size={14} className="landing-lang-icon" aria-hidden="true" />
              <button
                type="button"
                className={`landing-lang-btn ${!isKn ? 'active' : ''}`}
                onClick={() => setLanguage('en')}
                title="Switch to English"
              >
                EN
              </button>
              <button
                type="button"
                className={`landing-lang-btn ${isKn ? 'active' : ''}`}
                onClick={() => setLanguage('kn')}
                title="ಕನ್ನಡಕ್ಕೆ ಬದಲಾಯಿಸಿ"
              >
                ಕನ್ನಡ
              </button>
            </div>

            <ThemeSelector />

            <button
              className="nav-cta-btn"
              onClick={() => navigate('/login')}
              id="nav-get-started"
            >
              {isKn ? 'ಪ್ರಾರಂಭಿಸಿ' : 'Get Started'}
              <ArrowRight size={15} aria-hidden="true" />
            </button>
          </div>
        </div>
      </nav>

      {/* ── SECTION 1: HERO ───────────────────────────────────── */}
      <section
        ref={heroRef}
        className={`section-hero ${heroVisible ? 'revealed' : ''}`}
        id="hero"
        aria-label="Hero"
      >
        <div className="hero-inner">
          <div className="hero-text">
            <div className="hero-eyebrow">
              <span className="eyebrow-dot" aria-hidden="true" />
              {isKn ? 'ಕೃಷಿ AI ಸಹಾಯಕ' : 'Agricultural AI Companion'}
            </div>
            <h1 className="hero-headline">
              {isKn ? (
                <>
                  ಸ್ಮಾರ್ಟ್ ಕೃಷಿ ಮಾರ್ಗದರ್ಶನ,<br />
                  <em>ನಿಮ್ಮ ಜಮೀನಿನ ಸನ್ನಿವೇಶವನ್ನು<br />ಅರ್ಥೈಸಿಕೊಳ್ಳುವ ಒಡನಾಡಿಯೊಂದಿಗೆ.</em>
                </>
              ) : (
                <>
                  Smarter farming,<br />
                  <em>with a companion that<br />understands your field.</em>
                </>
              )}
            </h1>
            <p className="hero-subtext">
              {isKn
                ? 'ರೈತ ಸಾಥಿ ಕೃಷಿ ಜ್ಞಾನ, ನೈಸರ್ಗಿಕ ಸಂಭಾಷಣೆ ಮತ್ತು ಜಮೀನಿನ ನೈಜ ಸನ್ನಿವೇಶಕ್ಕೆ ತಕ್ಕ ಸಲಹೆಗಳನ್ನು ಒಂದೇ ಸೂರಿನಡಿ ಒದಗಿಸುತ್ತದೆ — ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ.'
                : 'Raitha Sathi brings agricultural knowledge, conversation, and farm-focused guidance together in one simple place — in Kannada, English, or both.'}
            </p>
            <div className="hero-actions">
              <button
                className="btn-hero-primary"
                onClick={() => navigate('/login')}
                id="hero-get-started"
              >
                {isKn ? 'ಪ್ರಾರಂಭಿಸಿ' : 'Get Started'}
                <ArrowRight size={16} aria-hidden="true" />
              </button>
              <a href="#how-it-works" className="btn-hero-secondary" id="hero-explore">
                {isKn ? 'ಪರಿಶೀಲಿಸಿ' : 'Explore'}
                <ChevronDown size={15} aria-hidden="true" />
              </a>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-image-card">
              <img
                src={farmerHeroImg}
                alt="Farmer in Karnataka fields using Raitha Sathi AI app"
                className="hero-farmer-img"
              />
              <div className="hero-image-overlay" />
              <div className="hero-badge-floating">
                <span className="badge-pulse" />
                <span className="badge-text">{isKn ? '🌾 30+ ಬೆಳೆಗಳ ಮಾರ್ಗದರ್ಶನ' : '🌾 30+ Crops Guidance'}</span>
              </div>
              <div className="illus-chat-bubble">
                <span className="illus-bubble-icon">💬</span>
                <span className="illus-bubble-text">
                  {isKn ? 'ಫಸಲು ಚೆನ್ನಾಗಿ ಬೆಳೆಯಲು ಏನು ಮಾಡಬೇಕು?' : 'ಫಸಲು ಚೆನ್ನಾಗಿ ಬೆಳೆಯಲು ಏನು ಮಾಡಬೇಕು?'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 2: FARMER'S DAY ──────────────────────────── */}
      <section
        ref={farmerRef}
        className={`section-farmer ${farmerVisible ? 'revealed' : ''}`}
        id="features"
        aria-label="Farmer's questions"
      >
        <div className="section-inner centered">
          <div className="section-label">{isKn ? 'ಪ್ರತಿಯೊಂದು ಹೊಲಕ್ಕೂ ಒಂದು ಕಥೆಯಿದೆ' : 'Every Field Has a Story'}</div>
          <h2 className="section-headline">
            {isKn ? (
              <>ರೈತರು ಪ್ರತಿದಿನವೂ<br />ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳುತ್ತಾರೆ.</>
            ) : (
              <>Farmers ask questions<br />every single day.</>
            )}
          </h2>
          <p className="section-subtext">
            {isKn
              ? 'ಬೆಳಗಿನ ಮೊದಲ ಹೊಲದ ಕೆಲಸದಿಂದ ಸಂಜೆಯ ಮಾರುಕಟ್ಟೆಯವರೆಗೆ — ನಿಖರವಾದ ಮಾರ್ಗದರ್ಶನ ಯಶಸ್ಸಿಗೆ ಕಾರಣವಾಗುತ್ತದೆ.'
              : 'From the first crop in the morning to the market at sunset — good guidance makes the difference.'}
          </p>

          <StaggerList
            items={farmerQuestions}
            renderItem={(item) => (
              <div className="question-card">
                <span className="question-kannada">{item.q}</span>
                <span className="question-english">{item.en}</span>
              </div>
            )}
          />
        </div>
      </section>

      {/* ── SECTION 3: MEET SATHI ────────────────────────────── */}
      <section
        ref={meetRef}
        className={`section-meet ${meetVisible ? 'revealed' : ''}`}
        aria-label="Meet Sathi"
        id="about"
      >
        <div className="section-inner">
          <div className="meet-layout">
            <div className="meet-text">
              <div className="section-label">{isKn ? 'ನಿಮ್ಮ ಡಿಜಿಟಲ್ ಒಡನಾಡಿ' : 'The Companion'}</div>
              <h2 className="section-headline">{isKn ? 'ಸಾಥಿ ಅವರ ಭೇಟಿ.' : 'Meet Sathi.'}</h2>
              <p className="section-subtext">
                {isKn
                  ? 'ನೀವು ನೇರವಾಗಿ ಮಾತನಾಡಬಹುದಾದ ಕೃಷಿ ಮಾರ್ಗದರ್ಶಿ. ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಪ್ರಶ್ನಿಸಿ. ಸಾಥಿ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಂಡು, ಕೃಷಿ ಜ್ಞಾನದ ಆಧಾರದಲ್ಲಿ ಸ್ಪಷ್ಟ ಉತ್ತರ ನೀಡುತ್ತದೆ.'
                  : 'An agricultural companion you can talk to. Ask in Kannada or English. Sathi understands your question, looks through agricultural knowledge, and responds in a language you are comfortable with.'}
              </p>
              <p className="section-subtext">
                {isKn
                  ? 'ಯಾವುದೇ ಕಠಿಣ ಫಾರ್ಮ್‌ಗಳಿಲ್ಲ, ತಾಂತ್ರಿಕ ಕ್ಲಿಷ್ಟತೆಯಿಲ್ಲ. ನಿಮ್ಮ ಹೊಲ, ಬೆಳೆ ಮತ್ತು ಸಮಸ್ಯೆಗಳ ಕುರಿತು ಸರಳ ಸಂಭಾಷಣೆ.'
                  : 'No complicated forms. No technical jargon. Just a conversation about your farm, your crops, and your challenges.'}
              </p>
            </div>

            <div className="meet-chat-preview" aria-label="Illustrative conversation preview">
              <div className="chat-preview-label">{isKn ? 'ಉದಾಹರಣೆ ಸಂಭಾಷಣೆ' : 'Illustrative Preview'}</div>
              <div className="chat-preview-card">
                <div className="chat-msg farmer-msg">
                  <div className="chat-avatar farmer-avatar" aria-hidden="true">🧑‍🌾</div>
                  <div className="chat-bubble farmer-bubble">
                    <p>ಟೊಮೇಟೊ ಎಲೆಗಳು ಸುರಳಿ ತಿರುಗುತ್ತಿವೆ. ಏನು ಮಾಡಬೇಕು?</p>
                    <span className="bubble-translation">My tomato leaves are curling. What should I do?</span>
                  </div>
                </div>
                <div className="chat-msg sathi-msg">
                  <div className="chat-avatar sathi-avatar" aria-hidden="true">🌿</div>
                  <div className="chat-bubble sathi-bubble">
                    <p>ಎಲೆಯ ಕೆಳಭಾಗ ಪರಿಶೀಲಿಸಿ. ಉಣ್ಣಿ ಕಾಟ ಅಥವಾ ತೇವಾಂಶ ಕೊರತೆ ಕಾರಣ ಆಗಿರಬಹುದು.</p>
                    <span className="bubble-translation">Check the underside of the leaves. It may be mites or moisture stress.</span>
                  </div>
                </div>
                <div className="chat-msg farmer-msg">
                  <div className="chat-avatar farmer-avatar" aria-hidden="true">🧑‍🌾</div>
                  <div className="chat-bubble farmer-bubble">
                    <p>ಏನು ಔಷಧ ಹಾಕಬೇಕು?</p>
                    <span className="bubble-translation">What medicine should I apply?</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 4: HOW SATHI HELPS (sticky visual) ───────── */}
      <section
        className="section-story"
        id="how-it-works"
        aria-label="How Sathi helps"
        ref={storyRef}
      >
        <div className="story-inner">
          {/* Sticky visual */}
          <div className="story-visual-col" aria-hidden="true">
            <div className="story-sticky-visual">
              <div className="story-visual-card">
                <div className="story-visual-icon" key={activeStep}>
                  {storySteps[activeStep]?.icon &&
                    React.createElement(storySteps[activeStep].icon, { size: 34 })}
                </div>
                <div className="story-visual-step-badge">
                  {isKn ? `ಹಂತ ${storySteps[activeStep]?.step} / ${storySteps.length}` : `Step ${storySteps[activeStep]?.step} of ${storySteps.length}`}
                </div>
                <h3 className="story-visual-title">{storySteps[activeStep]?.title}</h3>
                <p className="story-visual-body">{storySteps[activeStep]?.body}</p>
                <div className="story-visual-progress">
                  {storySteps.map((_, i) => (
                    <div
                      key={i}
                      className={`progress-dot ${i === activeStep ? 'dot-current' : i < activeStep ? 'dot-active' : ''}`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Scrolling steps */}
          <div className="story-steps-col">
            <div className="section-label">{isKn ? 'ಕಾರ್ಯವೈಖರಿ' : 'How It Works'}</div>
            <h2 className="section-headline" style={{ marginBottom: '3rem' }}>
              {isKn ? (
                <>ಉತ್ತಮ ಕೃಷಿಗಾಗಿ<br />ನಾಲ್ಕು ಸರಳ ಹಂತಗಳು.</>
              ) : (
                <>Four simple steps<br />to better farming.</>
              )}
            </h2>
            {storySteps.map((step, i) => (
              <StoryStep
                key={i}
                {...step}
                isActive={i === activeStep}
                onSelect={() => setActiveStep(i)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ── SECTION 5: YOUR FARM ─────────────────────────────── */}
      <section
        ref={farmRef}
        className={`section-farm ${farmVisible ? 'revealed' : ''}`}
        aria-label="Your farm"
      >
        <div className="section-inner">
          <div className="farm-layout">
            <div className="farm-text">
              <div className="section-label">{isKn ? 'ನಿಮ್ಮ ಕೃಷಿ ಮಾಹಿತಿ' : 'Your Context'}</div>
              <h2 className="section-headline">
                {isKn ? (
                  <>ನಿಮ್ಮ ಜಮೀನು.<br />ನಿಮ್ಮ ಸನ್ನಿವೇಶ.<br />ಒಂದೇ ವೇದಿಕೆಯಲ್ಲಿ.</>
                ) : (
                  <>Your farm.<br />Your context.<br />One place.</>
                )}
              </h2>
              <p className="section-subtext">
                {isKn
                  ? 'ನಿಮ್ಮ ಜಮೀನಿನ ವಿವರವನ್ನು ಒಮ್ಮೆ ಸಾಥಿಗೆ ತಿಳಿಸಿ. ಸ್ಥಳ, ಬೆಳೆಗಳು, ಮಣ್ಣಿನ ಪ್ರಕಾರ ಮತ್ತು ನೀರಾವರಿ ವಿಧಾನ. ಪ್ರತಿಯೊಂದು ಸಲಹೆಯೂ ನಿಮ್ಮ ಜಮೀನಿಗೆ ತಕ್ಕಂತೆ ಇರುತ್ತದೆ.'
                  : 'Tell Sathi about your farm once. Location, crops, soil type, and irrigation method. Every answer becomes more relevant to your specific situation.'}
              </p>
            </div>

            <div className="farm-card-preview" aria-label="Illustrative farm profile preview">
              <div className="farm-preview-header">
                <div className="farm-preview-label">{isKn ? 'ಉದಾಹರಣೆ ಮಾಹಿತಿ' : 'Illustrative Preview'}</div>
                <span className="farm-preview-title">{isKn ? 'ಜಮೀನಿನ ವಿವರ' : 'Farm Profile'}</span>
              </div>
              <div className="farm-preview-grid">
                {farmDetails.map(({ icon: Icon, label, value }) => (
                  <div key={label} className="farm-detail-row">
                    <div className="farm-detail-icon"><Icon size={15} /></div>
                    <div className="farm-detail-info">
                      <span className="farm-detail-label">{label}</span>
                      <span className="farm-detail-value">{value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 6: FINAL CTA ─────────────────────────────── */}
      <section
        ref={ctaRef}
        className={`section-cta ${ctaVisible ? 'revealed' : ''}`}
        aria-label="Call to action"
      >
        <div className="section-inner centered">
          <div className="section-label">{isKn ? 'ಪ್ರಾರಂಭಿಸಿ' : 'Get Started'}</div>
          <h2 className="cta-headline">
            {isKn ? (
              <>ಒಟ್ಟಾಗಿ ಸ್ಮಾರ್ಟ್ ಕೃಷಿ<br />ಮಾಡೋಣ.</>
            ) : (
              <>Let's grow smarter,<br />together.</>
            )}
          </h2>
          <p className="cta-subtext">
            {isKn ? (
              <>ಒಂದು ಪ್ರಶ್ನೆಯೊಂದಿಗೆ ಪ್ರಾರಂಭಿಸಿ.<br />ಸಾಥಿ ಮುಂದಿನ ಹಂತಕ್ಕೆ ನಿಮಗೆ ಮಾರ್ಗದರ್ಶನ ನೀಡುತ್ತದೆ.</>
            ) : (
              <>Start with a question.<br />Let Sathi help you take the next step.</>
            )}
          </p>
          <button
            className="btn-cta-primary"
            onClick={() => navigate('/login')}
            id="cta-get-started"
          >
            {isKn ? 'ಪ್ರಾರಂಭಿಸಿ' : 'Get Started'}
            <ArrowRight size={16} aria-hidden="true" />
          </button>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────── */}
      <footer className="landing-footer" role="contentinfo">
        <div className="footer-inner">
          <div className="footer-brand">
            <span className="footer-leaf" aria-hidden="true">🌾</span>
            <span className="footer-name">{isKn ? 'ರೈತ ಸಾಥಿ' : 'Raitha Sathi'}</span>
          </div>
          <p className="footer-tagline">
            {isKn ? 'ಕರ್ನಾಟಕದ ರೈತರಿಗಾಗಿ ಕೃಷಿ AI ಒಡನಾಡಿ' : 'Agricultural AI Companion for Karnataka Farmers'}
          </p>
          <p className="footer-copy">
            {isKn
              ? '© 2025 ರೈತ ಸಾಥಿ. ಕರ್ನಾಟಕದ ಕೃಷಿ ಸಮುದಾಯಕ್ಕಾಗಿ ನಿರ್ಮಿಸಲಾಗಿದೆ.'
              : "© 2025 Raitha Sathi. Built for Karnataka's farming community."}
          </p>
        </div>
      </footer>

    </div>
  );
};
