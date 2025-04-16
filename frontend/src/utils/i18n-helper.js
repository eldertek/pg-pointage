/**
 * Utilitaires pour l'internationalisation
 */

/**
 * Vérifie si une clé de traduction existe dans les fichiers de traduction
 * @param {Object} translations - Objet contenant les traductions
 * @param {string} key - Clé de traduction à vérifier (format: 'section.key' ou 'section.subsection.key')
 * @returns {boolean} - true si la clé existe, false sinon
 */
export const hasTranslationKey = (translations, key) => {
  if (!key || !translations) return false;
  
  const parts = key.split('.');
  let current = translations;
  
  for (const part of parts) {
    if (!current[part]) return false;
    current = current[part];
  }
  
  return true;
};

/**
 * Obtient la valeur d'une clé de traduction
 * @param {Object} translations - Objet contenant les traductions
 * @param {string} key - Clé de traduction (format: 'section.key' ou 'section.subsection.key')
 * @returns {string|null} - Valeur de la traduction ou null si la clé n'existe pas
 */
export const getTranslationValue = (translations, key) => {
  if (!key || !translations) return null;
  
  const parts = key.split('.');
  let current = translations;
  
  for (const part of parts) {
    if (!current[part]) return null;
    current = current[part];
  }
  
  return typeof current === 'string' ? current : null;
};

/**
 * Trouve la clé de traduction correspondant à un texte
 * @param {Object} translations - Objet contenant les traductions
 * @param {string} text - Texte à rechercher
 * @param {string} [section] - Section dans laquelle chercher (optionnel)
 * @returns {string|null} - Clé de traduction ou null si non trouvée
 */
export const findTranslationKey = (translations, text, section = null) => {
  if (!text || !translations) return null;
  
  // Fonction récursive pour parcourir l'objet de traduction
  const findInObject = (obj, prefix = '') => {
    for (const key in obj) {
      const currentPath = prefix ? `${prefix}.${key}` : key;
      
      if (typeof obj[key] === 'string' && obj[key] === text) {
        return currentPath;
      } else if (typeof obj[key] === 'object') {
        const result = findInObject(obj[key], currentPath);
        if (result) return result;
      }
    }
    return null;
  };
  
  // Si une section est spécifiée, chercher uniquement dans cette section
  if (section && translations[section]) {
    return findInObject(translations[section], section);
  }
  
  // Sinon, chercher dans tout l'objet
  return findInObject(translations);
};

/**
 * Suggère une clé de traduction pour un texte
 * @param {string} text - Texte pour lequel suggérer une clé
 * @param {string} section - Section dans laquelle placer la clé
 * @returns {string} - Suggestion de clé de traduction
 */
export const suggestTranslationKey = (text, section) => {
  if (!text || !section) return '';
  
  // Convertir le texte en camelCase
  const key = text
    .toLowerCase()
    .replace(/[^\w\s]/g, '') // Supprimer les caractères spéciaux
    .replace(/\s+/g, '_') // Remplacer les espaces par des underscores
    .replace(/_+/g, '_') // Éviter les underscores multiples
    .replace(/^_|_$/g, ''); // Supprimer les underscores au début et à la fin
  
  return `${section}.${key}`;
};

/**
 * Génère un code pour ajouter une traduction manquante
 * @param {string} key - Clé de traduction
 * @param {string} text - Texte à traduire
 * @returns {string} - Code pour ajouter la traduction
 */
export const generateTranslationCode = (key, text) => {
  const parts = key.split('.');
  const section = parts[0];
  const subKey = parts.slice(1).join('.');
  
  return `// Ajouter dans la section "${section}" du fichier de traduction:
"${subKey}": "${text}",`;
};
