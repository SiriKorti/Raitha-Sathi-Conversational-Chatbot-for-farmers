import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  TrendingUp,
  Plus,
  Calendar,
  Clock,
  Sprout,
  AlertCircle,
  Layers,
  Leaf,
  Info,
  Trash2,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useToast } from '../../context/ToastContext';
import { farmService } from '../../services/farmService';
import { PageHeader } from '../../components/common/PageHeader';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { ErrorState } from '../../components/common/ErrorState';
import { Modal } from '../../components/common/Modal';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import './ProgressPage.css';

// Bilingual Crop Names Dictionary
const CROP_NAME_MAP = {
  ragi: { en: 'Finger Millet (Ragi)', kn: 'ರಾಗಿ' },
  'finger millet': { en: 'Finger Millet (Ragi)', kn: 'ರಾಗಿ' },
  rice: { en: 'Paddy / Rice', kn: 'ಭತ್ತ' },
  paddy: { en: 'Paddy / Rice', kn: 'ಭತ್ತ' },
  maize: { en: 'Maize / Corn', kn: 'ಮೆಕ್ಕೆಜೋಳ' },
  corn: { en: 'Maize / Corn', kn: 'ಮೆಕ್ಕೆಜೋಳ' },
  sugarcane: { en: 'Sugarcane', kn: 'ಕಬ್ಬು' },
  cotton: { en: 'Cotton', kn: 'ಹತ್ತಿ' },
  arecanut: { en: 'Arecanut', kn: 'ಅಡಿಕೆ' },
  coconut: { en: 'Coconut', kn: 'ತೆಂಗು' },
  coffee: { en: 'Coffee', kn: 'ಕಾಫಿ' },
  groundnut: { en: 'Groundnut / Peanut', kn: 'ಕಡಲೆಕಾಯಿ / ಶೇಂಗಾ' },
  peanut: { en: 'Groundnut / Peanut', kn: 'ಕಡಲೆಕಾಯಿ / ಶೇಂಗಾ' },
  sunflower: { en: 'Sunflower', kn: 'ಸೂರ್ಯಕಾಂತಿ' },
  turmeric: { en: 'Turmeric', kn: 'ಅರಿಶಿನ' },
  chickpea: { en: 'Chickpea / Bengal Gram', kn: 'ಕಡಲೆ' },
  bengalgram: { en: 'Chickpea / Bengal Gram', kn: 'ಕಡಲೆ' },
  redgram: { en: 'Redgram / Pigeonpea', kn: 'ತೊಗರಿ' },
  pigeonpea: { en: 'Redgram / Pigeonpea', kn: 'ತೊಗರಿ' },
  jowar: { en: 'Sorghum / Jowar', kn: 'ಜೋಳ' },
  sorghum: { en: 'Sorghum / Jowar', kn: 'ಜೋಳ' },
  bajra: { en: 'Pearl Millet / Bajra', kn: 'ಸಜ್ಜೆ' },
  pearlmillet: { en: 'Pearl Millet / Bajra', kn: 'ಸಜ್ಜೆ' },
  tomato: { en: 'Tomato', kn: 'ಟೊಮೆಟೊ' },
  onion: { en: 'Onion', kn: 'ಈರುಳ್ಳಿ' },
  potato: { en: 'Potato', kn: 'ಆಲೂಗಡ್ಡೆ' },
  chilli: { en: 'Chilli', kn: 'ಮೆಣಸಿನಕಾಯಿ' },
  wheat: { en: 'Wheat', kn: 'ಗೋಧಿ' },
  ginger: { en: 'Ginger', kn: 'ಶುಂಠಿ' },
  garlic: { en: 'Garlic', kn: 'ಬೆಳ್ಳುಳ್ಳಿ' },
  banana: { en: 'Banana', kn: 'ಬಾಳೆ' },
  mango: { en: 'Mango', kn: 'ಮಾವು' },
  // Kannada inputs
  'ರಾಗಿ': { en: 'Finger Millet (Ragi)', kn: 'ರಾಗಿ' },
  'ಭತ್ತ': { en: 'Paddy / Rice', kn: 'ಭತ್ತ' },
  'ಮೆಕ್ಕೆಜೋಳ': { en: 'Maize / Corn', kn: 'ಮೆಕ್ಕೆಜೋಳ' },
  'ಕಬ್ಬು': { en: 'Sugarcane', kn: 'ಕಬ್ಬು' },
  'ಹತ್ತಿ': { en: 'Cotton', kn: 'ಹತ್ತಿ' },
  'ಅಡಿಕೆ': { en: 'Arecanut', kn: 'ಅಡಿಕೆ' },
  'ತೆಂಗು': { en: 'Coconut', kn: 'ತೆಂಗು' },
  'ಕಾಫಿ': { en: 'Coffee', kn: 'ಕಾಫಿ' },
  'ಕಡಲೆಕಾಯಿ': { en: 'Groundnut / Peanut', kn: 'ಕಡಲೆಕಾಯಿ' },
  'ಶೇಂಗಾ': { en: 'Groundnut / Peanut', kn: 'ಶೇಂಗಾ' },
  'ಸೂರ್ಯಕಾಂತಿ': { en: 'Sunflower', kn: 'ಸೂರ್ಯಕಾಂತಿ' },
  'ಅರಿಶಿನ': { en: 'Turmeric', kn: 'ಅರಿಶಿನ' },
  'ಕಡಲೆ': { en: 'Chickpea / Bengal Gram', kn: 'ಕಡಲೆ' },
  'ತೊಗರಿ': { en: 'Redgram / Pigeonpea', kn: 'ತೊಗರಿ' },
  'ಜೋಳ': { en: 'Sorghum / Jowar', kn: 'ಜೋಳ' },
  'ಸಜ್ಜೆ': { en: 'Pearl Millet / Bajra', kn: 'ಸಜ್ಜೆ' },
  'ಟೊಮೆಟೊ': { en: 'Tomato', kn: 'ಟೊಮೆಟೊ' },
  'ಟೊಮೇಟೊ': { en: 'Tomato', kn: 'ಟೊಮೇಟೊ' },
  'ಈರುಳ್ಳಿ': { en: 'Onion', kn: 'ಈರುಳ್ಳಿ' },
  'ಆಲೂಗಡ್ಡೆ': { en: 'Potato', kn: 'ಆಲೂಗಡ್ಡೆ' },
  'ಮೆಣಸಿನಕಾಯಿ': { en: 'Chilli', kn: 'ಮೆಣಸಿನಕಾಯಿ' },
  'ಗೋಧಿ': { en: 'Wheat', kn: 'ಗೋಧಿ' },
};

// Growth Stage Translations
const STAGE_PATTERNS = [
  {
    patterns: [/germination/i, /seedling/i, /emergence/i],
    knName: 'ಮೊಳಕೆಯೊಡೆಯುವಿಕೆ ಮತ್ತು ಸಸಿ ಹಂತ',
    enName: 'Germination & Seedling',
    knDesc: 'ಬಿತ್ತನೆಯಿಂದ ಬೀಜ ಮೊಳಕೆಯೊಡೆದು ಸಸಿ ನೆಲೆಯೂರುವ ಆರಂಭಿಕ ಹಂತ.',
    enDesc: 'From sowing to emergence and establishment of seedlings.',
  },
  {
    patterns: [/tillering/i, /tiller/i],
    knName: 'ಕವಲೊಡೆಯುವ ಹಂತ (ಟಿಲ್ಲರಿಂಗ್)',
    enName: 'Tillering Stage',
    knDesc: 'ಗಿಡದಲ್ಲಿ ಹೊಸ ಕವಲುಗಳು ಮತ್ತು ಉಪಕಾಂಡಗಳು ಹುಟ್ಟುವ ಹಂತ.',
    enDesc: 'Formation of side shoots (tillers) from the main stem.',
  },
  {
    patterns: [/grand growth/i, /stem elongation/i, /jointing/i],
    knName: 'ಕಾಂಡ ವಿಸ್ತರಣೆ ಮತ್ತು ಚುರುಕಾದ ಬೆಳವಣಿಗೆ ಹಂತ',
    enName: 'Stem Elongation & Grand Growth',
    knDesc: 'ಕಾಂಡಗಳು ವೇಗವಾಗಿ ಎತ್ತರ ಬೆಳೆದು ಗಿಡ ಸದೃಢವಾಗುವ ಸಮಯ.',
    enDesc: 'Rapid lengthening of stems and vigorous vegetative development.',
  },
  {
    patterns: [/vegetative/i],
    knName: 'ಸಸ್ಯಕ ಬೆಳವಣಿಗೆಯ ಹಂತ (ವೆಜಿಟೇಟಿವ್)',
    enName: 'Vegetative Stage',
    knDesc: 'ಎಲೆಗಳು ಮತ್ತು ಕವಲುಗಳು ಹುಲುಸಾಗಿ ಬೆಳೆಯುವ ನಿರ್ಣಾಯಕ ಹಂತ.',
    enDesc: 'Vigorous leaf and canopy development prior to flowering.',
  },
  {
    patterns: [/panicle initiation/i, /booting/i, /boot stage/i],
    knName: 'ತೆನೆ ಬಸಿರಾಗುವ ಹಂತ (ಬೂಟಿಂಗ್)',
    enName: 'Booting / Panicle Initiation',
    knDesc: 'ಕಾಂಡದೊಳಗೆ ತೆನೆ ರೂಪುಗೊಂಡು ಹೊರಬರಲು ಸಿದ್ಧವಾಗುವ ಸೂಕ್ಷ್ಮ ಹಂತ.',
    enDesc: 'Panicle develops within the flag leaf sheath prior to heading.',
  },
  {
    patterns: [/flowering/i, /anthesis/i, /bloom/i, /heading/i],
    knName: 'ಹೂ ಬಿಡುವ ಹಂತ (ಫ್ಲವರಿಂಗ್)',
    enName: 'Flowering & Anthesis',
    knDesc: 'ತೆನೆ ಅಥವಾ ಹೂವು ಅರಳಿ ಪರಾಗಸ್ಪರ್ಶ ನಡೆಯುವ ಅತಿ ಮುಖ್ಯ ಹಂತ.',
    enDesc: 'Heading, blooming, and pollination take place.',
  },
  {
    patterns: [/milky/i, /milk stage/i, /grain filling/i, /grain formation/i],
    knName: 'ಹಾಲು ತುಂಬುವ ಮತ್ತು ಕಾಳು ಕಟ್ಟುವ ಹಂತ',
    enName: 'Grain Filling & Milk Stage',
    knDesc: 'ಕಾಳುಗಳಲ್ಲಿ ಹಾಲು ತುಂಬಿ ನಂತರ ಗಟ್ಟಿಯಾಗುವ ಕಾಳು ಕಟ್ಟುವ ಹಂತ.',
    enDesc: 'Nutrients accumulate in developing kernels/grains in liquid to dough state.',
  },
  {
    patterns: [/dough stage/i],
    knName: 'ಹಿಟ್ಟು ಕಟ್ಟುವ ಹಂತ (ಡಫ್ ಸ್ಟೇಜ್)',
    enName: 'Dough Stage',
    knDesc: 'ಕಾಳುಗಳು ಗಟ್ಟಿಯಾಗಿ ತೇವಾಂಶ ಕಡಿಮೆಯಾಗುವ ಹಂತ.',
    enDesc: 'Grains solidify from soft to hard dough consistency.',
  },
  {
    patterns: [/ripening/i, /physiological maturity/i, /maturity/i],
    knName: 'ಮಾಗುವ ಮತ್ತು ಬಲಿಯುವ ಹಂತ',
    enName: 'Ripening & Maturity',
    knDesc: 'ತೆನೆ ಮತ್ತು ಎಲೆಗಳು ಬಂಗಾರದ ಬಣ್ಣಕ್ಕೆ ತಿರುಗಿ ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾಗುವ ಹಂತ.',
    enDesc: 'Crops turn golden-yellow and attain harvest moisture levels.',
  },
  {
    patterns: [/harvest/i],
    knName: 'ಕೊಯ್ಲು ಹಂತ',
    enName: 'Harvesting Stage',
    knDesc: 'ಬೆಳೆಯು ಸಂಪೂರ್ಣವಾಗಿ ಮಾಗಿದ್ದು ಕಟಾವು ಮಾಡಲು ಸಿದ್ಧವಾಗಿದೆ.',
    enDesc: 'Crop is fully mature and ready for harvesting.',
  },
  {
    patterns: [/pod/i],
    knName: 'ಕಾಯಿ ಕಟ್ಟುವ ಮತ್ತು ಬೆಳೆಯುವ ಹಂತ',
    enName: 'Pod Development Stage',
    knDesc: 'ಹೂವುಗಳು ಕಾಯಿಯಾಗಿ ಪರಿವರ್ತನೆಗೊಂಡು ಬೀಜಗಳು ದಪ್ಪಗಾಗುವ ಹಂತ.',
    enDesc: 'Pods develop and seeds enlarge within the pods.',
  },
  {
    patterns: [/boll/i],
    knName: 'ಹತ್ತಿ ಕಾಯಿ ಕಟ್ಟುವ ಹಂತ (ಬೋಲ್ ಡೆವಲಪ್ಮೆಂಟ್)',
    enName: 'Boll Development Stage',
    knDesc: 'ಹತ್ತಿಯ ಕಾಯಿಗಳು (ಬೋಲ್ಸ್) ರೂಪುಗೊಂಡು ಬೆಳೆಯುವ ಹಂತ.',
    enDesc: 'Cotton bolls develop and mature.',
  },
  {
    patterns: [/establishment/i, /nursery/i, /planting/i],
    knName: 'ನಾಟಿ ಮತ್ತು ಸ್ಥಾಪನೆ ಹಂತ',
    enName: 'Field Establishment Stage',
    knDesc: 'ಸಸಿ ನೆಟ್ಟು ಬೇರು ಬಿಟ್ಟು ಜಮೀನಿನಲ್ಲಿ ನೆಲೆಯೂರುವ ಆರಂಭಿಕ ಹಂತ.',
    enDesc: 'Transplanting, root establishment, and early field adaptation.',
  },
  {
    patterns: [/juvenile/i, /canopy/i],
    knName: 'ಸಸ್ಯಕ ಮತ್ತು ಬೆಳವಣಿಗೆ ಹಂತ',
    enName: 'Juvenile Vegetative Growth',
    knDesc: 'ಕಾಂಡ ಸದೃಢವಾಗಿ ಬೆಳೆದು ಎಲೆಗಳ ಗರಿಗಳು ವಿಸ್ತರಿಸುವ ಹಂತ.',
    enDesc: 'Trunk formation and canopy frond expansion prior to bearing.',
  },
  {
    patterns: [/spadix/i, /inflorescence/i],
    knName: 'ಹೂಗೊಂಚಲು (ಸ್ಪ್ಯಾಡಿಕ್ಸ್) ಮತ್ತು ಪ್ರಥಮ ಇಳುವರಿ ಹಂತ',
    enName: 'Spadix & First Bearing',
    knDesc: 'ಮೊದಲ ಹೂಗೊಂಚಲು ಅರಳಿ ಕಾಯಿ ಕಟ್ಟುವ ಪ್ರಕ್ರಿಯೆ ಪ್ರಾರಂಭವಾಗುವ ಹಂತ.',
    enDesc: 'First inflorescence emergence and initial fruit setting.',
  },
  {
    patterns: [/bearing/i, /production/i],
    knName: 'ವಾರ್ಷಿಕ ಇಳುವರಿ ಮತ್ತು ಕಟಾವು ಹಂತ',
    enName: 'Full Economic Bearing',
    knDesc: 'ಮರವು ಪೂರ್ಣವಾಗಿ ಬಲಿತು ಪ್ರತಿವರ್ಷ ನಿಯಮಿತವಾಗಿ ಕಾಯಿಗಳ ಗೊಂಚಲು ಬಿಡುವ ಹಂತ.',
    enDesc: 'Mature palm with regular annual commercial bunch production.',
  },
  {
    patterns: [/scheduled/i, /ನಿಗದಿಯಾಗಿದೆ/i],
    knName: 'ಬಿತ್ತನೆ ನಿಗದಿಯಾಗಿದೆ',
    enName: 'Sowing Scheduled',
    knDesc: 'ಬಿತ್ತನೆ ದಿನಾಂಕ ಭವಿಷ್ಯದಲ್ಲಿದೆ. ಬಿತ್ತನೆಯ ನಂತರ ಬೆಳವಣಿಗೆಯ ಲೆಕ್ಕಾಚಾರ ಪ್ರಾರಂಭವಾಗುತ್ತದೆ.',
    enDesc: 'Sowing date is in the future. Growth tracking begins after planting.',
  },
];

const QUICK_CROPS = [
  { en: 'Ragi', kn: 'ರಾಗಿ' },
  { en: 'Paddy', kn: 'ಭತ್ತ' },
  { en: 'Maize', kn: 'ಮೆಕ್ಕೆಜೋಳ' },
  { en: 'Sugarcane', kn: 'ಕಬ್ಬು' },
  { en: 'Cotton', kn: 'ಹತ್ತಿ' },
  { en: 'Arecanut', kn: 'ಅಡಿಕೆ' },
  { en: 'Tomato', kn: 'ಟೊಮೆಟೊ' },
  { en: 'Groundnut', kn: 'ಕಡಲೆಕಾಯಿ' },
];

export const ProgressPage = () => {
  const { user } = useAuth();
  const { language } = useLanguage();
  const { showToast } = useToast();
  const isKn = language === 'kn';

  const userId = user?.id || 'user_123';

  const [crops, setCrops] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    crop_name: '',
    sowing_date: '',
    variety: '',
  });
  const [formError, setFormError] = useState('');

  // Delete Crop State
  const [cropToDelete, setCropToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch crop progress from backend
  const fetchProgress = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await farmService.getProgress(userId);
      if (response && response.status === 'success') {
        setCrops(response.crops || []);
      } else {
        throw new Error(response?.message || 'Failed to fetch crop progress');
      }
    } catch (err) {
      console.error('Failed to load crop progress:', err);
      setError(
        isKn
          ? 'ಬೆಳೆ ಪ್ರಗತಿ ಸರ್ವರ್ ಸಂಪರ್ಕಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.'
          : err.message || 'Could not connect to the farm progress service.'
      );
    } finally {
      setIsLoading(false);
    }
  }, [userId, isKn]);

  useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  // Form Handlers
  const handleOpenModal = () => {
    setFormData({
      crop_name: '',
      sowing_date: new Date().toISOString().split('T')[0],
      variety: '',
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    if (!isSaving) {
      setIsModalOpen(false);
      setFormError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    const cropName = formData.crop_name.trim();
    const sowingDate = formData.sowing_date.trim();

    if (!cropName) {
      setFormError(isKn ? 'ದಯವಿಟ್ಟು ಬೆಳೆಯ ಹೆಸರನ್ನು ನಮೂದಿಸಿ' : 'Please enter a crop name');
      return;
    }

    if (!sowingDate) {
      setFormError(isKn ? 'ದಯವಿಟ್ಟು ಬಿತ್ತನೆ ದಿನಾಂಕವನ್ನು ಆಯ್ಕೆಮಾಡಿ' : 'Please select a sowing date');
      return;
    }

    setIsSaving(true);
    try {
      const payload = {
        crop_name: cropName,
        sowing_date: sowingDate,
        variety: formData.variety.trim() || null,
      };

      const response = await farmService.saveProgress(userId, payload);
      if (response && response.status === 'success') {
        setCrops(response.crops || []);
        showToast(
          isKn ? 'ಬೆಳೆ ಪ್ರಗತಿ ವಿವರವನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಉಳಿಸಲಾಗಿದೆ!' : 'Crop progress saved successfully!',
          'success'
        );
        setIsModalOpen(false);
      } else {
        throw new Error(response?.message || 'Failed to save crop progress');
      }
    } catch (err) {
      console.error('Failed to save crop progress:', err);
      setFormError(
        err.message ||
          (isKn ? 'ಬೆಳೆ ಪ್ರಗತಿ ಉಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.' : 'Failed to save crop progress.')
      );
    } finally {
      setIsSaving(false);
    }
  };

  // Helper formatting functions
  const formatDate = (dateString) => {
    if (!dateString) return null;
    try {
      const dateObj = new Date(dateString);
      return dateObj.toLocaleDateString(isKn ? 'kn-IN' : 'en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const getLocalizedCropName = (rawName) => {
    if (!rawName) return '';
    const key = rawName.trim().toLowerCase();
    if (CROP_NAME_MAP[key]) {
      return isKn ? CROP_NAME_MAP[key].kn : CROP_NAME_MAP[key].en;
    }
    // Also check Kannada characters directly
    if (CROP_NAME_MAP[rawName.trim()]) {
      return isKn ? CROP_NAME_MAP[rawName.trim()].kn : CROP_NAME_MAP[rawName.trim()].en;
    }
    return rawName.charAt(0).toUpperCase() + rawName.slice(1);
  };

  const handleRequestDelete = (crop) => {
    setCropToDelete(crop);
  };

  const handleConfirmDelete = async () => {
    if (!cropToDelete) return;
    setIsDeleting(true);
    try {
      const response = await farmService.deleteCrop(userId, cropToDelete.crop_name);
      if (response && response.status === 'success') {
        setCrops(response.crops || []);
        showToast(
          isKn
            ? `"${getLocalizedCropName(cropToDelete.crop_name)}" ಬೆಳೆಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ತೆಗೆದುಹಾಕಲಾಗಿದೆ!`
            : `"${cropToDelete.crop_name}" removed successfully!`,
          'success'
        );
        setCropToDelete(null);
      } else {
        throw new Error(response?.message || 'Failed to remove crop');
      }
    } catch (err) {
      console.error('Failed to remove crop:', err);
      showToast(
        err.message || (isKn ? 'ಬೆಳೆ ತೆಗೆದುಹಾಕಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.' : 'Failed to remove crop.'),
        'error'
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const getLocalizedStage = (stage) => {
    if (!stage) return null;
    const stageName = stage.name || '';
    const matched = STAGE_PATTERNS.find((item) =>
      item.patterns.some((p) => p.test(stageName))
    );
    if (matched) {
      return {
        name: isKn ? matched.knName : (stage.name || matched.enName),
        description: isKn ? matched.knDesc : (stage.description || matched.enDesc),
      };
    }
    return {
      name: stage.name,
      description: stage.description,
    };
  };

  const getLocalizedNotes = (notes) => {
    if (!notes) return null;
    if (!isKn) return notes;
    const n = notes.toLowerCase();
    if (n.includes('duration varies') || n.includes('early-maturing') || n.includes('long-duration')) {
      return 'ಬೆಳೆಯ ಅವಧಿಯು ತಳಿಯ ಪ್ರಕಾರ (ಅಲ್ಪಾವಧಿ 60-70 ದಿನಗಳು ಅಥವಾ ದೀರ್ಘಾವಧಿ 135 ದಿನಗಳವರೆಗೆ), ಬೆಳೆಯುವ ಪ್ರದೇಶ ಮತ್ತು ಹವಾಮಾನಕ್ಕೆ ಅನುಗುಣವಾಗಿ ಬದಲಾಗುತ್ತದೆ.';
    }
    if (n.includes('season') || n.includes('climate') || n.includes('variety')) {
      return 'ಬೆಳೆಯ ಅವಧಿಯು ತಳಿ, ಮಣ್ಣು, ಬೆಳೆಯುವ ಪ್ರದೇಶ ಮತ್ತು ಹವಾಮಾನಕ್ಕೆ ಅನುಗುಣವಾಗಿ ಬದಲಾಗುತ್ತದೆ.';
    }
    return notes;
  };

  return (
    <div className="progress-page-container">
      {/* Page Header */}
      <PageHeader
        title={isKn ? 'ಬೆಳೆ ಪ್ರಗತಿ ಟ್ರ್ಯಾಕರ್' : 'Crop Progress Tracker'}
        subtitle={
          isKn
            ? 'ನಿಮ್ಮ ಜಮೀನಿನ ಬೆಳೆಗಳ ಬಿತ್ತನೆ ದಿನಾಂಕ, ಬೆಳವಣಿಗೆಯ ಹಂತಗಳು ಮತ್ತು ನಿರೀಕ್ಷಿತ ಕೊಯ್ಲು ದಿನಾಂಕಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.'
            : 'Track crop growth stages, days elapsed, and estimated harvest timelines dynamically.'
        }
        icon={TrendingUp}
        action={
          <Button
            variant="primary"
            icon={Plus}
            onClick={handleOpenModal}
            aria-label={isKn ? 'ಹೊಸ ಬೆಳೆ ಸೇರಿಸಿ' : 'Add Crop'}
          >
            {isKn ? 'ಬೆಳೆ ಸೇರಿಸಿ' : 'Add Crop'}
          </Button>
        }
      />

      {/* Main Content Area */}
      {isLoading ? (
        <div className="progress-loading-wrapper">
          <LoadingSpinner />
          <p className="progress-loading-text">
            {isKn
              ? 'ಬೆಳೆ ಪ್ರಗತಿ ವಿವರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...'
              : 'Loading crop progress and agronomic insights...'}
          </p>
        </div>
      ) : error ? (
        <ErrorState
          message={error}
          onRetry={fetchProgress}
        />
      ) : crops.length === 0 ? (
        <EmptyState
          icon={TrendingUp}
          title={isKn ? 'ಯಾವುದೇ ಬೆಳೆ ಪ್ರಗತಿ ನಮೂದಿಸಿಲ್ಲ' : 'No Crop Progress Tracked Yet'}
          description={
            isKn
              ? 'ನಿಮ್ಮ ಜಮೀನಿನ ಮೊದಲ ಬೆಳೆಯನ್ನು ಸೇರಿಸಿ, ಅದರ ಬೆಳವಣಿಗೆ ಮತ್ತು ಕೊಯ್ಲಿನ ದಿನಾಂಕಗಳನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಲು ಪ್ರಾರಂಭಿಸಿ.'
              : 'Add your first crop with its sowing date to monitor its growth cycle and projected harvest window.'
          }
          action={
            <Button variant="primary" icon={Plus} onClick={handleOpenModal}>
              {isKn ? 'ಮೊದಲ ಬೆಳೆ ಸೇರಿಸಿ' : 'Add First Crop'}
            </Button>
          }
        />
      ) : (
        <div className="crops-progress-grid">
          {crops.map((crop, index) => {
            const isFuture = Boolean(crop.is_future);
            const isPerennial = Boolean(crop.is_perennial);
            const isMature = Boolean(crop.is_mature);

            const hasDuration = crop.duration_days_min !== null && crop.duration_days_max !== null;
            const hasProgress = crop.progress_percentage_min !== null && crop.progress_percentage_max !== null;
            const hasHarvest = crop.estimated_harvest_date_min !== null || crop.estimated_harvest_date_max !== null;
            const hasDaysRemaining = crop.days_until_harvest_min !== null && crop.days_until_harvest_max !== null;
            const localizedStage = getLocalizedStage(crop.current_stage);
            const localizedCropName = getLocalizedCropName(crop.crop_name);
            const localizedNotes = getLocalizedNotes(crop.notes || crop.source);

            const minPct = isFuture ? 0 : hasProgress ? Math.min(100, Math.max(0, crop.progress_percentage_min)) : 0;
            const maxPct = isFuture ? 0 : hasProgress ? Math.min(100, Math.max(0, crop.progress_percentage_max)) : 0;

            return (
              <div key={`${crop.crop_name}_${index}`} className="crop-progress-card glass-panel">
                {/* Top Card Bar */}
                <div className="card-top-header">
                  <div className="crop-title-group">
                    <div className="crop-icon-badge">
                      <Sprout size={20} className="crop-sprout-icon" />
                    </div>
                    <div>
                      <h2 className="crop-name-heading">{localizedCropName}</h2>
                      {crop.variety && (
                        <span className="crop-variety-pill">
                          {crop.variety}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="card-top-right-actions">
                    <div className={`days-elapsed-tag ${isFuture ? 'future-tag' : ''}`} style={isFuture ? { background: 'rgba(255, 179, 0, 0.15)', color: '#ffb300' } : undefined}>
                      <Clock size={14} />
                      <span>
                        {isFuture
                          ? (isKn ? `${crop.days_until_planting} ದಿನಗಳಲ್ಲಿ ಬಿತ್ತನೆ` : `Sowing in ${crop.days_until_planting} days`)
                          : isPerennial && crop.days_elapsed >= 365
                            ? `${Math.floor(crop.days_elapsed / 365)} ${isKn ? 'ವರ್ಷ' : 'yrs'} ${Math.floor((crop.days_elapsed % 365) / 30)} ${isKn ? 'ತಿಂಗಳು' : 'mos'} (${crop.days_elapsed} ${isKn ? 'ದಿನ' : 'd'})`
                            : `${crop.days_elapsed} ${isKn ? 'ದಿನಗಳು ಕಳೆದಿವೆ' : 'Days Elapsed'}`}
                      </span>
                    </div>

                    <button
                      type="button"
                      className="crop-delete-btn"
                      onClick={() => handleRequestDelete(crop)}
                      title={isKn ? 'ಬೆಳೆ ತೆಗೆದುಹಾಕಿ' : 'Remove crop'}
                      aria-label={isKn ? 'ಬೆಳೆ ತೆಗೆದುಹಾಕಿ' : 'Remove crop'}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                {/* Sowing Date Pill */}
                <div className="card-meta-row">
                  <span className="sowing-date-label">
                    <Calendar size={14} />
                    <span>{isKn ? 'ಬಿತ್ತನೆ ದಿನಾಂಕ:' : 'Sown on:'}</span>
                    <strong>{formatDate(crop.sowing_date)}</strong>
                  </span>

                  <span className="duration-label">
                    <Layers size={14} />
                    <span>{isKn ? 'ಅವಧಿ:' : 'Duration:'}</span>
                    <strong>
                      {isPerennial
                        ? (isKn ? 'ಬಹುವಾರ್ಷಿಕ (30+ ವರ್ಷ)' : 'Perennial (30+ yrs)')
                        : hasDuration
                          ? (crop.duration_days_min === crop.duration_days_max
                              ? `${crop.duration_days_min} ${isKn ? 'ದಿನಗಳು' : 'days'}`
                              : `${crop.duration_days_min}–${crop.duration_days_max} ${isKn ? 'ದಿನಗಳು' : 'days'}`)
                          : (isKn ? 'ಅಂದಾಜು ಅವಧಿ' : 'Estimated duration')}
                    </strong>
                  </span>
                </div>

                {/* Progress Bar Section */}
                <div className="progress-meter-section">
                  <div className="progress-meter-header">
                    <span className="progress-meter-title">
                      {isFuture
                        ? (isKn ? 'ಬೆಳೆ ಪ್ರಗತಿ (ನಿಗದಿಯಾಗಿದೆ)' : 'Growth Progress (Scheduled)')
                        : isPerennial
                          ? (isMature
                              ? (isKn ? 'ಇಳುವರಿ ಸ್ಥಿತಿ' : 'Production Status')
                              : (isKn ? 'ಪ್ರಥಮ ಇಳುವರಿ ಪ್ರಗತಿ' : 'Establishment Progress'))
                          : (isKn ? 'ಬೆಳೆ ಪ್ರಗತಿ' : 'Growth Progress')}
                    </span>
                    <span className="progress-percentage-val">
                      {isFuture ? (
                        '0%'
                      ) : isMature ? (
                        `100% (${isKn ? 'ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾಗಿದೆ' : 'Ready for Harvest'})`
                      ) : hasProgress ? (
                        crop.progress_percentage_min === crop.progress_percentage_max ? (
                          `${crop.progress_percentage_min}%`
                        ) : (
                          `${crop.progress_percentage_min}% – ${crop.progress_percentage_max}%`
                        )
                      ) : (
                        <span className="unavailable-text">
                          {isKn ? 'ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ' : 'Unavailable'}
                        </span>
                      )}
                    </span>
                  </div>

                  {hasProgress || isFuture ? (
                    <div
                      className="progress-track"
                      role="progressbar"
                      aria-valuenow={minPct}
                      aria-valuemin="0"
                      aria-valuemax="100"
                      aria-label={`${localizedCropName} growth progress`}
                    >
                      <div
                        className="progress-fill-solid"
                        style={{ width: `${minPct}%` }}
                      />
                      {maxPct > minPct && (
                        <div
                          className="progress-fill-range"
                          style={{ left: `${minPct}%`, width: `${maxPct - minPct}%` }}
                        />
                      )}
                    </div>
                  ) : (
                    <div className="progress-unavailable-box">
                      <AlertCircle size={14} />
                      <span>
                        {isKn
                          ? 'ಈ ಬೆಳೆಗೆ ಪ್ರಗತಿ ಶೇಕಡಾವಾರು ಲಭ್ಯವಿಲ್ಲ'
                          : 'Progress calculation unavailable for this crop'}
                      </span>
                    </div>
                  )}
                </div>

                {/* Current Growth Stage */}
                <div className="stage-status-section">
                  <div className="stage-label-heading">
                    <Leaf size={15} />
                    <span>{isKn ? 'ಪ್ರಸ್ತುತ ಹಂತ' : 'Current Stage'}</span>
                  </div>
                  {localizedStage ? (
                    <div className="stage-info-content">
                      <span className="stage-name-badge">
                        {localizedStage.name}
                      </span>
                      {localizedStage.description && (
                        <p className="stage-description-text">
                          {localizedStage.description}
                        </p>
                      )}
                    </div>
                  ) : (
                    <span className="stage-unavailable-text">
                      {isKn ? 'ಹಂತದ ವಿವರ ಲಭ್ಯವಿಲ್ಲ' : 'Stage information unavailable'}
                    </span>
                  )}
                </div>

                {/* Harvest Estimation Window */}
                <div className="harvest-window-section">
                  <div className="harvest-date-box">
                    <span className="harvest-title">
                      {isPerennial
                        ? (isMature
                            ? (isKn ? 'ವಾರ್ಷಿಕ ಕಟಾವು ಸಮಯ' : 'Annual Harvest Season')
                            : (isKn ? 'ನಿರೀಕ್ಷಿತ ಪ್ರಥಮ ಇಳುವರಿ' : 'Estimated First Bearing'))
                        : (isKn ? 'ನಿರೀಕ್ಷಿತ ಕೊಯ್ಲು ದಿನಾಂಕ' : 'Estimated Harvest')}
                    </span>
                    <span className="harvest-value">
                      {crop.harvest_season_description && (isPerennial || isMature) ? (
                        crop.harvest_season_description
                      ) : hasHarvest ? (
                        crop.estimated_harvest_date_min === crop.estimated_harvest_date_max ? (
                          formatDate(crop.estimated_harvest_date_min)
                        ) : (
                          `${formatDate(crop.estimated_harvest_date_min)} – ${formatDate(crop.estimated_harvest_date_max)}`
                        )
                      ) : (
                        <span className="unavailable-text">
                          {isKn ? 'ದಿನಾಂಕ ಲಭ್ಯವಿಲ್ಲ' : 'Window unavailable'}
                        </span>
                      )}
                    </span>
                  </div>

                  <div className="countdown-box">
                    <span className="countdown-title">
                      {isFuture
                        ? (isKn ? 'ಬಿತ್ತನೆಗೆ ಬಾಕಿ' : 'To Sowing')
                        : (isKn ? 'ಬಾಕಿ' : 'Remaining')}
                    </span>
                    <span className="countdown-value">
                      {isFuture ? (
                        `${crop.days_until_planting} ${isKn ? 'ದಿನ' : 'days'}`
                      ) : isMature ? (
                        `${isKn ? 'ಕಟಾವಿಗೆ ಸಿದ್ಧ' : 'Ready to Harvest'}`
                      ) : isPerennial && crop.days_until_harvest_min !== null ? (
                        crop.days_until_harvest_min > 365
                          ? `${(crop.days_until_harvest_min / 365).toFixed(1)} ${isKn ? 'ವರ್ಷ' : 'yrs'}`
                          : `${crop.days_until_harvest_min} ${isKn ? 'ದಿನ' : 'days'}`
                      ) : hasDaysRemaining ? (
                        crop.days_until_harvest_min === crop.days_until_harvest_max ? (
                          `${crop.days_until_harvest_min} ${isKn ? 'ದಿನ' : 'days'}`
                        ) : (
                          `${crop.days_until_harvest_min}–${crop.days_until_harvest_max} ${isKn ? 'ದಿನ' : 'days'}`
                        )
                      ) : (
                        '—'
                      )}
                    </span>
                  </div>
                </div>

                {/* Provenance & Notes */}
                {localizedNotes && (
                  <div className="card-reference-footer">
                    <Info size={12} />
                    <span>{localizedNotes}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add Crop Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={isKn ? 'ಹೊಸ ಬೆಳೆ ಸೇರಿಸಿ' : 'Add Crop Progress'}
        maxWidth="460px"
      >
        <form onSubmit={handleSubmit} className="add-crop-form">
          <p className="modal-instruction-text">
            {isKn
              ? 'ನಿಮ್ಮ ಜಮೀನಿನ ಬೆಳೆಯ ಹೆಸರು ಮತ್ತು ಬಿತ್ತನೆ ಮಾಡಿದ ದಿನಾಂಕವನ್ನು ನಮೂದಿಸಿ.'
              : 'Enter your crop name and sowing date. Agronomic timelines are dynamically matched by AI.'}
          </p>

          {/* Quick Crop Selector Chips */}
          <div className="quick-crop-chips-row" style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' }}>
            {QUICK_CROPS.map((c, i) => (
              <button
                key={i}
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: '0.78rem', padding: '4px 10px', borderRadius: '16px' }}
                onClick={() => setFormData((prev) => ({ ...prev, crop_name: isKn ? c.kn : c.en }))}
              >
                🌱 {isKn ? c.kn : c.en}
              </button>
            ))}
          </div>

          {formError && (
            <div className="form-error-banner animate-fade-in" role="alert">
              <AlertCircle size={16} />
              <span>{formError}</span>
            </div>
          )}

          <div className="form-field-wrapper">
            <Input
              label={isKn ? 'ಬೆಳೆಯ ಹೆಸರು *' : 'Crop Name *'}
              id="crop_name"
              placeholder={isKn ? 'ಉದಾ: ರಾಗಿ, ಭತ್ತ, ಮೆಕ್ಕೆಜೋಳ, ಟೊಮೆಟೊ...' : 'e.g., Ragi, Paddy, Tomato...'}
              value={formData.crop_name}
              onChange={(e) => setFormData((prev) => ({ ...prev, crop_name: e.target.value }))}
              required
              disabled={isSaving}
              autoFocus
            />
          </div>

          <div className="form-field-wrapper">
            <Input
              label={isKn ? 'ಬಿತ್ತನೆ ದಿನಾಂಕ *' : 'Sowing Date *'}
              id="sowing_date"
              type="date"
              value={formData.sowing_date}
              onChange={(e) => setFormData((prev) => ({ ...prev, sowing_date: e.target.value }))}
              required
              disabled={isSaving}
            />
          </div>

          <div className="form-field-wrapper">
            <Input
              label={isKn ? 'ತಳಿ (ಐಚ್ಛಿಕ)' : 'Variety (Optional)'}
              id="variety"
              placeholder={isKn ? 'ಉದಾ: ಜಿಪಿಯು-28, ಜ್ಯೋತಿ, ಹೈಬ್ರಿಡ್...' : 'e.g., GPU-28, Hybrid...'}
              value={formData.variety}
              onChange={(e) => setFormData((prev) => ({ ...prev, variety: e.target.value }))}
              disabled={isSaving}
            />
          </div>

          <div className="modal-actions-row">
            <Button
              type="button"
              variant="secondary"
              onClick={handleCloseModal}
              disabled={isSaving}
            >
              {isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel'}
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSaving}
              disabled={isSaving}
            >
              {isKn ? 'ಉಳಿಸಿ' : 'Save Crop'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Remove Crop Confirmation Modal */}
      <Modal
        isOpen={Boolean(cropToDelete)}
        onClose={() => !isDeleting && setCropToDelete(null)}
        title={isKn ? 'ಬೆಳೆ ತೆಗೆದುಹಾಕಿ' : 'Remove Crop'}
      >
        <div className="delete-crop-modal-content">
          <p className="delete-crop-modal-text">
            {isKn
              ? `ನೀವು ನಿಜವಾಗಿಯೂ "${cropToDelete ? getLocalizedCropName(cropToDelete.crop_name) : ''}" ಬೆಳೆಯನ್ನು ನಿಮ್ಮ ಟ್ರ್ಯಾಕರ್‌ನಿಂದ ತೆಗೆದುಹಾಕಲು ಬಯಸುವಿರಾ?`
              : `Are you sure you want to remove "${cropToDelete ? getLocalizedCropName(cropToDelete.crop_name) : ''}" from your crop progress tracker?`}
          </p>

          <div className="delete-crop-modal-actions">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setCropToDelete(null)}
              disabled={isDeleting}
            >
              {isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel'}
            </Button>

            <Button
              type="button"
              variant="danger"
              onClick={handleConfirmDelete}
              isLoading={isDeleting}
              disabled={isDeleting}
            >
              {isKn ? 'ತೆಗೆದುಹಾಕಿ' : 'Remove'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
