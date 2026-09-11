/**
 * Verified Government Schemes Dataset
 * Matches database/schemes.json loaded by SchemeService
 * Fully supports Kannada (kn) and English (en)
 */

export const SCHEMES_DATA = [
  {
    id: 'krishi-bhagya',
    nameEn: 'Krishi Bhagya Scheme',
    nameKn: 'ಕೃಷಿ ಭಾಗ್ಯ ಯೋಜನೆ',
    categoryEn: 'Water & Rainwater Harvesting',
    categoryKn: 'ನೀರಾವರಿ ಮತ್ತು ಮಳೆ ನೀರು ಕೊಯ್ಲು',
    descriptionEn:
      'Provides financial assistance for constructing Krishi Hondas (farm ponds) to harvest rainwater. Promotes dryland agriculture and water security in rainfed regions of Karnataka.',
    descriptionKn:
      'ಮಳೆ ನೀರನ್ನು ಸಂಗ್ರಹಿಸಲು ಕೃಷಿ ಹೊಂಡಗಳನ್ನು ನಿರ್ಮಿಸಲು ಆರ್ಥಿಕ ನೆರವು ನೀಡುತ್ತದೆ. ಕರ್ನಾಟಕದ ಮಳೆಯಾಶ್ರಿತ ಪ್ರದೇಶಗಳಲ್ಲಿ ಒಣಭೂಮಿ ಕೃಷಿ ಮತ್ತು ನೀರಿನ ಭದ್ರತೆಯನ್ನು ಉತ್ತೇಜಿಸುತ್ತದೆ.',
    eligibilityEn: 'Farmers with dryland agriculture in Karnataka. Must have an Aadhaar card and RTC (Pahani).',
    eligibilityKn: 'ಕರ್ನಾಟಕದ ಒಣಭೂಮಿ ಪ್ರದೇಶದ ರೈತರು. ಆಧಾರ್ ಕಾರ್ಡ್ ಮತ್ತು ಜಮೀನಿನ ಪಹಣಿ (RTC) ಹೊಂದಿರಬೇಕು.',
    benefitsEn: 'Subsidy up to 80% for farm ponds, diesel pumpsets, polythene lining, and micro/drip irrigation systems.',
    benefitsKn: 'ಕೃಷಿ ಹೊಂಡ, ಡೀಸೆಲ್ ಪಂಪ್‌ಸೆಟ್, ಪಾಲಿಥೀನ್ ಹೊದಿಕೆ ಮತ್ತು ಹನಿ/ತುಂತುರು ನೀರಾವರಿ ಘಟಕಗಳಿಗೆ ಶೇ. 80 ರವರೆಗೆ ಸಬ್ಸಿಡಿ ನೀಡಲಾಗುತ್ತದೆ.',
    applicationProcessEn:
      'Apply at the nearest Raitha Samparka Kendra (RSK) or through the Farmer Registration and Unified Beneficiary Information System (FRUITS) portal.',
    applicationProcessKn:
      'ಹತ್ತಿರದ ರೈತ ಸಂಪರ್ಕ ಕೇಂದ್ರ (RSK) ಅಥವಾ ರೈತ ನೋಂದಣಿ ಮತ್ತು ಏಕೀಕೃತ ಫಲಾನುಭವಿ ಮಾಹಿತಿ ವ್ಯವಸ್ಥೆ (FRUITS) ಪೋರ್ಟಲ್ ಮೂಲಕ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.',
    samplePromptsEn: [
      'How to apply for Krishi Bhagya farm pond subsidy in Karnataka?',
      'What are the eligibility criteria and documents for Krishi Bhagya scheme?',
    ],
    samplePromptsKn: [
      'ಕೃಷಿ ಭಾಗ್ಯ ಯೋಜನೆಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಬೇಕಾದ ದಾಖಲೆಗಳು ಯಾವುವು?',
      'ಕೃಷಿ ಹೊಂಡ ನಿರ್ಮಾಣಕ್ಕೆ ಸಬ್ಸಿಡಿ ಪಡೆಯುವುದು ಹೇಗೆ?',
    ],
    get schemeName() { return this.nameKn; },
    get category() { return this.categoryKn; },
    get description() { return this.descriptionKn; },
    get eligibility() { return this.eligibilityKn; },
    get benefits() { return this.benefitsKn; },
    get applicationProcess() { return this.applicationProcessKn; },
    get samplePrompts() { return this.samplePromptsKn; },
  },
  {
    id: 'pm-kisan',
    nameEn: 'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
    nameKn: 'ಪಿಎಂ-ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ (PM-KISAN)',
    categoryEn: 'Direct Income Support',
    categoryKn: 'ನೇರ ಆದಾಯ ಬೆಂಬಲ',
    descriptionEn:
      'A central government scheme offering minimum financial support to all cultivable landholding farmer families across India.',
    descriptionKn:
      'ದೇಶದ ಎಲ್ಲಾ ಸಾಗುವಳಿ ಭೂಮಿ ಹೊಂದಿರುವ ರೈತ ಕುಟುಂಬಗಳಿಗೆ ಕನಿಷ್ಠ ಆರ್ಥಿಕ ನೆರವು ನೀಡುವ ಕೇಂದ್ರ ಸರ್ಕಾರದ ಯೋಜನೆ.',
    eligibilityEn: 'All landholding farmers with cultivable land holding in their names, verified with Aadhaar and e-KYC.',
    eligibilityKn: 'ತಮ್ಮ ಹೆಸರಿನಲ್ಲಿ ಸಾಗುವಳಿ ಜಮೀನು ಹೊಂದಿರುವ ಎಲ್ಲಾ ರೈತರು. ಆಧಾರ್ ಮತ್ತು ಇ-ಕೆವೈಸಿ (e-KYC) ಪೂರ್ಣಗೊಂಡಿರಬೇಕು.',
    benefitsEn: '₹6,000 per year paid in three equal installments of ₹2,000 directly to the farmer bank account via DBT.',
    benefitsKn: 'ವರ್ಷಕ್ಕೆ ₹6,000 ಆರ್ಥಿಕ ನೆರವು. ತಲಾ ₹2,000 ರ ಮೂರು ಕಂತುಗಳಲ್ಲಿ ನೇರವಾಗಿ ರೈತರ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ (DBT) ಜಮೆಯಾಗುತ್ತದೆ.',
    applicationProcessEn:
      'Register via the PM-KISAN portal online (pmkisan.gov.in) or visit the local Grama One / Common Service Center (CSC) / Revenue Officer.',
    applicationProcessKn:
      'ಪಿಎಂ-ಕಿಸಾನ್ ಅಧಿಕೃತ ಪೋರ್ಟಲ್ (pmkisan.gov.in) ಅಥವಾ ಸ್ಥಳೀಯ ಗ್ರಾಮ ಒನ್ / ಸಿಎಸ್‌ಸಿ (CSC) ಕೇಂದ್ರದಲ್ಲಿ ನೋಂದಾಯಿಸಿ.',
    samplePromptsEn: [
      'How to check PM-KISAN installment status and eligibility?',
      'What is the e-KYC process for PM-KISAN scheme?',
    ],
    samplePromptsKn: [
      'PM-KISAN ಯೋಜನೆಯ ಕಂತು ಮತ್ತು ಇ-ಕೆವೈಸಿ (e-KYC) ಪ್ರಕ್ರಿಯೆ ಹೇಗೆ?',
      'ಪಿಎಂ ಕಿಸಾನ್ ಹಣ ಜಮೆ ಆಗಿದೆಯೇ ಎಂದು ಪರಿಶೀಲಿಸುವುದು ಹೇಗೆ?',
    ],
    get schemeName() { return this.nameKn; },
    get category() { return this.categoryKn; },
    get description() { return this.descriptionKn; },
    get eligibility() { return this.eligibilityKn; },
    get benefits() { return this.benefitsKn; },
    get applicationProcess() { return this.applicationProcessKn; },
    get samplePrompts() { return this.samplePromptsKn; },
  },
  {
    id: 'bhoomi',
    nameEn: 'Karnataka Bhoomi Portal (Land Records / RTC)',
    nameKn: 'ಕರ್ನಾಟಕ ಭೂಮಿ ಸೇವೆ (ಆರ್‌ಟಿಸಿ / ಪಹಣಿ)',
    categoryEn: 'Digital Land Records',
    categoryKn: 'ಡಿಜಿಟಲ್ ಭೂ ದಾಖಲೆಗಳು',
    descriptionEn:
      'A crucial Karnataka state digital portal allowing farmers and landowners to view and download authentic land records (RTC, Mutation status, Tippan) online.',
    descriptionKn:
      'ರೈತರು ತಮ್ಮ ಜಮೀನಿನ ಅಧಿಕೃತ ಪಹಣಿ (RTC), ಖಾತೆ ಬದಲಾವಣೆ (ಮ್ಯುಟೇಶನ್) ಮತ್ತು ಟಿಪ್ಪಣಿ ದಾಖಲೆಗಳನ್ನು ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ವೀಕ್ಷಿಸಲು ಮತ್ತು ಡೌನ್‌ಲೋಡ್ ಮಾಡಲು ಕರ್ನಾಟಕ ಸರ್ಕಾರದ ಪ್ರಮುಖ ಸೇವೆ.',
    eligibilityEn: 'Any agricultural landowner in Karnataka.',
    eligibilityKn: 'ಕರ್ನಾಟಕದ ಎಲ್ಲಾ ಕೃಷಿ ಭೂಮಾಲೀಕರು.',
    benefitsEn: 'Instant online access to RTC (Pahani) documents required for agricultural bank loans, crop loss compensation, and crop insurance claims.',
    benefitsKn: 'ಬ್ಯಾಂಕ್ ಕೃಷಿ ಸಾಲ, ಬೆಳೆ ಪರಿಹಾರ ಮತ್ತು ಬೆಳೆ ವಿಮೆಗೆ ಅಗತ್ಯವಿರುವ ಪಹಣಿ ದಾಖಲೆಗಳನ್ನು ತಕ್ಷಣ ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಪಡೆಯಬಹುದು.',
    applicationProcessEn: 'Visit the Karnataka Bhoomi online portal (landrecords.karnataka.gov.in) or your nearest Nada Kacheri / Grama One center.',
    applicationProcessKn: 'ಕರ್ನಾಟಕ ಭೂಮಿ ಪೋರ್ಟಲ್ (landrecords.karnataka.gov.in) ಅಥವಾ ಹತ್ತಿರದ ನಾಡ ಕಚೇರಿ / ಗ್ರಾಮ ಒನ್ ಕೇಂದ್ರಕ್ಕೆ ಭೇಟಿ ನೀಡಿ.',
    samplePromptsEn: [
      'How to download RTC (Pahani) document from Bhoomi portal online?',
      'How to check land mutation status on Karnataka Bhoomi?',
    ],
    samplePromptsKn: [
      'ಭೂಮಿ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಪಹಣಿ (RTC) ಡೌನ್‌ಲೋಡ್ ಮಾಡುವುದು ಹೇಗೆ?',
      'ಜಮೀನಿನ ಮ್ಯುಟೇಶನ್ ಸ್ಥಿತಿ ಪರಿಶೀಲಿಸುವುದು ಹೇಗೆ?',
    ],
    get schemeName() { return this.nameKn; },
    get category() { return this.categoryKn; },
    get description() { return this.descriptionKn; },
    get eligibility() { return this.eligibilityKn; },
    get benefits() { return this.benefitsKn; },
    get applicationProcess() { return this.applicationProcessKn; },
    get samplePrompts() { return this.samplePromptsKn; },
  },
  {
    id: 'pmfby',
    nameEn: 'Karnataka Raitha Suraksha Pradhana Mantri Fasal Bima Yojana (PMFBY)',
    nameKn: 'ಕರ್ನಾಟಕ ರೈತ ಸುರಕ್ಷಾ ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ (PMFBY)',
    categoryEn: 'Crop Insurance',
    categoryKn: 'ಬೆಳೆ ವಿಮೆ',
    descriptionEn:
      'Comprehensive crop insurance scheme providing financial compensation to farmers in case of crop loss due to non-preventable natural calamities, drought, flood, pests, or diseases.',
    descriptionKn:
      'ಅನಾವೃಷ್ಟಿ, ಅತಿವೃಷ್ಟಿ, ಕೀಟಬಾಧೆ ಅಥವಾ ರೋಗಗಳಿಂದ ಬೆಳೆ ಹಾನಿಯಾದರೆ ರೈತರಿಗೆ ಆರ್ಥಿಕ ಪರಿಹಾರ ಒದಗಿಸುವ ಸಮಗ್ರ ಬೆಳೆ ವಿಮಾ ಯೋಜನೆ.',
    eligibilityEn: 'All farmers (loanee and non-loanee) growing notified crops in notified panchayat/taluk areas in Karnataka.',
    eligibilityKn: 'ಕರ್ನಾಟಕದ ಅಧಿಸೂಚಿತ ಪ್ರದೇಶಗಳಲ್ಲಿ ಅಧಿಸೂಚಿತ ಬೆಳೆ ಬೆಳೆಯುವ ಎಲ್ಲಾ ರೈತರು (ಸಾಲ ಪಡೆದ ಮತ್ತು ಸಾಲ ಪಡೆಯದ ರೈತರು).',
    benefitsEn: 'Coverage for localized calamities, mid-season adversity, and post-harvest losses. Premium share is low (2% for Kharif, 1.5% for Rabi crops).',
    benefitsKn: 'ಸ್ಥಳೀಯ ವಿಪತ್ತುಗಳು, ಬರ, ಪ್ರವಾಹ ಮತ್ತು ಕೊಯ್ಲಿನ ನಂತರದ ಹಾನಿಗೆ ವಿಮಾ ರಕ್ಷಣೆ. ಅತ್ಯಂತ ಕಡಿಮೆ ಪ್ರೀಮಿಯಂ (ಖಾರೀಫ್ ಬೆಳೆಗೆ 2%, ಹಿಂಗಾರು ಬೆಳೆಗೆ 1.5%).',
    applicationProcessEn:
      'Apply through banks, Common Service Centers (CSCs), Samrakshane portal (belavime.karnataka.gov.in) before the cutoff deadline for each season.',
    applicationProcessKn:
      'ಬ್ಯಾಂಕ್‌ಗಳು, ಸಿಎಸ್‌ಸಿ ಕೇಂದ್ರಗಳು ಅಥವಾ ಸಂರಕ್ಷಣೆ ಪೋರ್ಟಲ್ (belavime.karnataka.gov.in) ಮೂಲಕ ಕೊನೆಯ ದಿನಾಂಕದೊಳಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.',
    samplePromptsEn: [
      'What are the eligibility and claims rules for PMFBY crop insurance in Karnataka?',
      'What is the last date to apply for crop insurance in Karnataka?',
    ],
    samplePromptsKn: [
      'ಬೆಳೆ ವಿಮೆ (PMFBY) ನೋಂದಣಿ ಕೊನೆಯ ದಿನಾಂಕ ಮತ್ತು ಪರಿಹಾರ ಮಾಹಿತಿ ತಿಳಿಸಿ',
      'ಬೆಳೆ ಹಾನಿಯಾದಾಗ ವಿಮಾ ಕ್ಲೈಮ್ ಮಾಡುವುದು ಹೇಗೆ?',
    ],
    get schemeName() { return this.nameKn; },
    get category() { return this.categoryKn; },
    get description() { return this.descriptionKn; },
    get eligibility() { return this.eligibilityKn; },
    get benefits() { return this.benefitsKn; },
    get applicationProcess() { return this.applicationProcessKn; },
    get samplePrompts() { return this.samplePromptsKn; },
  },
  {
    id: 'ganga-kalyana',
    nameEn: 'Ganga Kalyana Scheme',
    nameKn: 'ಗಂಗಾ ಕಲ್ಯಾಣ ಯೋಜನೆ',
    categoryEn: 'Irrigation & Borewell Assistance',
    categoryKn: 'ನೀರಾವರಿ ಮತ್ತು ಕೊಳವೆಬಾವಿ ನೆರವು',
    descriptionEn:
      'Provides open wells or borewells with motor pump sets and electrification for small and marginal farmers in Karnataka.',
    descriptionKn:
      'ಸಣ್ಣ ಮತ್ತು ಅತಿ ಸಣ್ಣ ರೈತರ ಕೃಷಿ ಜಮೀನಿಗೆ ನೀರಾವರಿ ಒದಗಿಸಲು ಉಚಿತ ಕೊಳವೆಬಾವಿ, ಪಂಪ್‌ಸೆಟ್ ಮತ್ತು ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ಕಲ್ಪಿಸುವ ಯೋಜನೆ.',
    eligibilityEn: 'Small and marginal farmers in Karnataka belonging to eligible backward and minority categories with requisite land holding.',
    eligibilityKn: 'ಕರ್ನಾಟಕದ ಸಣ್ಣ ಮತ್ತು ಅತಿ ಸಣ್ಣ ರೈತರು, ನಿಗದಿತ ವರ್ಗಗಳ ಫಲಾನುಭವಿಗಳು.',
    benefitsEn: 'Free borewell drilling, submersible pump installation, and power grid energization.',
    benefitsKn: 'ಉಚಿತವಾಗಿ ಕೊಳವೆಬಾವಿ ಕೊರೆಯುವುದು, ಪಂಪ್‌ಸೆಟ್ ಅಳವಡಿಕೆ ಮತ್ತು ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ಕಲ್ಪಿಸುವುದು.',
    applicationProcessEn: 'Apply through Karnataka Seva Sindhu portal (sevasindhu.karnataka.gov.in) or respective development corporation offices.',
    applicationProcessKn: 'ಕರ್ನಾಟಕ ಸೇವಾ ಸಿಂಧು ಪೋರ್ಟಲ್ (sevasindhu.karnataka.gov.in) ಅಥವಾ ಸಂಬಂಧಪಟ್ಟ ಅಭಿವೃದ್ಧಿ ನಿಗಮದ ಕಚೇರಿಗಳಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.',
    samplePromptsEn: [
      'How to apply for Ganga Kalyana borewell scheme in Karnataka?',
      'What documents are needed for Ganga Kalyana scheme?',
    ],
    samplePromptsKn: [
      'ಗಂಗಾ ಕಲ್ಯಾಣ ಯೋಜನೆಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?',
      'ಗಂಗಾ ಕಲ್ಯಾಣ ಕೊಳವೆಬಾವಿ ಯೋಜನೆಗೆ ಬೇಕಾಗುವ ದಾಖಲೆಗಳು ಯಾವುವು?',
    ],
    get schemeName() { return this.nameKn; },
    get category() { return this.categoryKn; },
    get description() { return this.descriptionKn; },
    get eligibility() { return this.eligibilityKn; },
    get benefits() { return this.benefitsKn; },
    get applicationProcess() { return this.applicationProcessKn; },
    get samplePrompts() { return this.samplePromptsKn; },
  },
  {
    id: 'raitha-siri',
    nameEn: 'Raitha Siri Scheme (Millet Incentive)',
    nameKn: 'ರೈತ ಸಿರಿ ಯೋಜನೆ (ಸಿರಿಧಾನ್ಯ ಪ್ರೋತ್ಸಾಹ ಧನ)',
    categoryEn: 'Millet Cultivation Support',
    categoryKn: 'ಸಿರಿಧಾನ್ಯ ಬೆಳೆ ಪ್ರೋತ್ಸಾಹ',
    descriptionEn:
      'Special incentive program promoting minor millet cultivation (Ragi, Foxtail, Little millet, etc.) to enhance nutritional security and drought resistance.',
    descriptionKn:
      'ಕರ್ನಾಟಕದಲ್ಲಿ ಸಿರಿಧಾನ್ಯಗಳ (ರಾಗಿ, ನವಣೆ, ಸಾಮೆ, ಹಾರಕ, ಕೊರಲೆ ಇತ್ಯಾದಿ) ಉತ್ಪಾದನೆ ಹೆಚ್ಚಿಸಲು ಮತ್ತು ರೈತರ ಆದಾಯ ಹೆಚ್ಚಿಸಲು ನೀಡಲಾಗುವ ಪ್ರೋತ್ಸಾಹಕ ಯೋಜನೆ.',
    eligibilityEn: 'Farmers cultivating recognized minor millets in Karnataka, registered on the FRUITS portal.',
    eligibilityKn: 'ಕರ್ನಾಟಕದಲ್ಲಿ ಸಿರಿಧಾನ್ಯ ಬೆಳೆಯುವ ಹಾಗೂ FRUITS ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ನೋಂದಾಯಿತರಾದ ಎಲ್ಲಾ ರೈತರು.',
    benefitsEn: 'Direct financial assistance of up to ₹10,000 per hectare directly credited to the farmer bank account.',
    benefitsKn: 'ಸಿರಿಧಾನ್ಯ ಬೆಳೆಯುವ ರೈತರಿಗೆ ಪ್ರತಿ ಹೆಕ್ಟೇರ್‌ಗೆ ₹10,000 ವರೆಗೆ ನೇರ ಪ್ರೋತ್ಸಾಹ ಧನ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ಜಮೆಯಾಗುತ್ತದೆ.',
    applicationProcessEn: 'Register crop details through the FRUITS portal or visit your local Raitha Samparka Kendra during the sowing window.',
    applicationProcessKn: 'ಬಿತ್ತನೆ ಸಮಯದಲ್ಲಿ ಹತ್ತಿರದ ರೈತ ಸಂಪರ್ಕ ಕೇಂದ್ರ (RSK) ಅಥವಾ FRUITS ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಬೆಳೆ ಸಮೀಕ್ಷೆ ವಿವರ ನೋಂದಾಯಿಸಿ.',
    samplePromptsEn: [
      'What is the subsidy under Raitha Siri millet scheme?',
      'How to get Rs 10000 per hectare under Raitha Siri scheme?',
    ],
    samplePromptsKn: [
      'ರೈತ ಸಿರಿ ಸಿರಿಧಾನ್ಯ ಪ್ರೋತ್ಸಾಹ ಧನ ಪಡೆಯುವುದು ಹೇಗೆ?',
      'ರೈತ ಸಿರಿ ಯೋಜನೆಯ ಅರ್ಹತಾ ನಿಯಮಗಳೇನು?',
    ],
    get schemeName() { return this.nameKn; },
    get category() { return this.categoryKn; },
    get description() { return this.descriptionKn; },
    get eligibility() { return this.eligibilityKn; },
    get benefits() { return this.benefitsKn; },
    get applicationProcess() { return this.applicationProcessKn; },
    get samplePrompts() { return this.samplePromptsKn; },
  },
];
