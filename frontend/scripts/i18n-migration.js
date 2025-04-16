/**
 * Script pour aider à la migration des composants vers l'internationalisation
 * 
 * Ce script analyse un fichier Vue et suggère les modifications à apporter
 * pour utiliser les traductions.
 * 
 * Usage: node scripts/i18n-migration.js path/to/component.vue
 */

const fs = require('fs');
const path = require('path');

// Charger les fichiers de traduction
const frTranslations = require('../src/locales/fr.json');
const enTranslations = require('../src/locales/en.json');

// Expressions régulières pour détecter les textes à traduire
const TEXT_PATTERNS = [
  // Texte dans les balises
  /<(v-btn|v-card-title|v-card-text|v-list-item-title|v-list-item-subtitle|v-tab|h1|h2|h3|h4|h5|h6|p|span|div|label|button)[^>]*>\s*([^<>{]+?)\s*<\/\1>/g,
  // Texte dans les attributs label
  /label="([^"]+)"/g,
  // Texte dans les attributs placeholder
  /placeholder="([^"]+)"/g,
  // Texte dans les attributs title
  /title="([^"]+)"/g,
  // Texte dans les attributs text
  /text="([^"]+)"/g,
];

// Fonction pour trouver une clé de traduction existante
function findTranslationKey(text) {
  // Parcourir l'objet de traduction pour trouver une correspondance exacte
  function searchInObject(obj, prefix = '') {
    for (const key in obj) {
      const currentPath = prefix ? `${prefix}.${key}` : key;
      
      if (typeof obj[key] === 'string' && obj[key] === text) {
        return currentPath;
      } else if (typeof obj[key] === 'object') {
        const result = searchInObject(obj[key], currentPath);
        if (result) return result;
      }
    }
    return null;
  }
  
  return searchInObject(frTranslations);
}

// Fonction pour suggérer une section de traduction basée sur le nom du composant
function suggestSection(filePath) {
  const fileName = path.basename(filePath, '.vue');
  
  if (filePath.includes('/mobile/')) {
    return 'mobile';
  } else if (filePath.includes('/dashboard/')) {
    return 'dashboard';
  } else if (filePath.includes('/auth/')) {
    return 'auth';
  } else if (fileName.includes('User') || fileName.includes('Users')) {
    return 'users';
  } else if (fileName.includes('Site') || fileName.includes('Sites')) {
    return 'sites';
  } else if (fileName.includes('Planning') || fileName.includes('Plannings')) {
    return 'plannings';
  } else if (fileName.includes('Timesheet') || fileName.includes('Timesheets')) {
    return 'timesheets';
  } else if (fileName.includes('Anomaly') || fileName.includes('Anomalies')) {
    return 'anomalies';
  } else if (fileName.includes('Organization') || fileName.includes('Organizations')) {
    return 'organizations';
  } else if (fileName.includes('Report') || fileName.includes('Reports')) {
    return 'reports';
  } else if (fileName.includes('Profile') || fileName.includes('Settings')) {
    return 'profile';
  } else {
    return 'common';
  }
}

// Fonction pour suggérer une clé de traduction
function suggestKey(text, section) {
  // Convertir le texte en camelCase
  const key = text
    .toLowerCase()
    .replace(/[^\w\s]/g, '') // Supprimer les caractères spéciaux
    .replace(/\s+/g, '_') // Remplacer les espaces par des underscores
    .replace(/_+/g, '_') // Éviter les underscores multiples
    .replace(/^_|_$/g, ''); // Supprimer les underscores au début et à la fin
  
  return `${section}.${key}`;
}

// Fonction principale
function analyzeComponent(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const section = suggestSection(filePath);
    const suggestions = [];
    
    // Parcourir les patterns pour trouver les textes à traduire
    TEXT_PATTERNS.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        const text = match[1] || match[2];
        
        // Ignorer les textes courts ou qui semblent être des variables
        if (text.length < 3 || text.includes('{{') || text.includes('}}') || text.trim() === '') {
          continue;
        }
        
        // Chercher si une traduction existe déjà
        const existingKey = findTranslationKey(text);
        
        if (existingKey) {
          suggestions.push({
            text,
            key: existingKey,
            original: match[0],
            replacement: match[0].replace(text, `{{ $t('${existingKey}') }}`),
            exists: true
          });
        } else {
          const suggestedKey = suggestKey(text, section);
          suggestions.push({
            text,
            key: suggestedKey,
            original: match[0],
            replacement: match[0].replace(text, `{{ $t('${suggestedKey}') }}`),
            exists: false
          });
        }
      }
    });
    
    // Afficher les résultats
    console.log(`\nAnalyse du composant: ${filePath}`);
    console.log(`Section suggérée: ${section}`);
    console.log(`Textes à traduire: ${suggestions.length}`);
    
    if (suggestions.length > 0) {
      console.log('\nSuggestions de traduction:');
      
      // Regrouper par clé de traduction
      const groupedByKey = {};
      suggestions.forEach(suggestion => {
        if (!groupedByKey[suggestion.key]) {
          groupedByKey[suggestion.key] = [];
        }
        groupedByKey[suggestion.key].push(suggestion);
      });
      
      // Afficher les suggestions
      Object.keys(groupedByKey).forEach(key => {
        const items = groupedByKey[key];
        const item = items[0];
        
        console.log(`\n${item.exists ? '[Existant]' : '[Nouveau]'} "${item.text}" -> "${key}"`);
        
        if (!item.exists) {
          console.log(`Ajouter dans fr.json: "${key.split('.')[1]}": "${item.text}",`);
          console.log(`Ajouter dans en.json: "${key.split('.')[1]}": "${item.text}",`);
        }
        
        items.forEach(suggestion => {
          console.log(`Remplacer: ${suggestion.original}`);
          console.log(`Par: ${suggestion.replacement}`);
        });
      });
    }
    
    return suggestions;
  } catch (error) {
    console.error(`Erreur lors de l'analyse du composant ${filePath}:`, error);
    return [];
  }
}

// Point d'entrée du script
const filePath = process.argv[2];
if (!filePath) {
  console.error('Veuillez spécifier un chemin de fichier');
  process.exit(1);
}

analyzeComponent(filePath);
