/**
 * Script pour automatiser la traduction des composants Vue
 *
 * Ce script parcourt tous les fichiers Vue du projet et remplace les textes statiques
 * par des appels à la fonction de traduction.
 *
 * Usage: node scripts/translate-components.js [--dry-run] [--verbose] [path/to/component.vue]
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Charger les fichiers de traduction
const frTranslations = require('../src/locales/fr.json');
const enTranslations = require('../src/locales/en.json');

// Options de ligne de commande
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const verbose = args.includes('--verbose');
const specificFile = args.find(arg => arg.endsWith('.vue') && !arg.startsWith('--'));

// Expressions régulières pour détecter les textes à traduire
const TEXT_PATTERNS = [
  // Texte dans les balises (contenu entre balises ouvrantes et fermantes)
  {
    pattern: /<(v-btn|v-card-title|v-card-text|v-list-item-title|v-list-item-subtitle|v-tab|h1|h2|h3|h4|h5|h6|p|span|div|label|button)[^>]*>\s*([^<>{]+?)\s*<\/\1>/g,
    extractText: (match) => match[2],
    createReplacement: (match, key) => {
      return match[0].replace(match[2], `{{ $t('${key}') }}`);
    }
  },
  // Texte dans les attributs label
  {
    pattern: /label="([^"]+)"/g,
    extractText: (match) => match[1],
    createReplacement: (match, key) => {
      return `:label="$t('${key}')"`;
    }
  },
  // Texte dans les attributs placeholder
  {
    pattern: /placeholder="([^"]+)"/g,
    extractText: (match) => match[1],
    createReplacement: (match, key) => {
      return `:placeholder="$t('${key}')"`;
    }
  },
  // Texte dans les attributs title
  {
    pattern: /title="([^"]+)"/g,
    extractText: (match) => match[1],
    createReplacement: (match, key) => {
      return `:title="$t('${key}')"`;
    }
  },
  // Texte dans les attributs text
  {
    pattern: /text="([^"]+)"/g,
    extractText: (match) => match[1],
    createReplacement: (match, key) => {
      return `:text="$t('${key}')"`;
    }
  },
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

// Fonction pour ajouter une traduction aux fichiers de traduction
function addTranslation(key, text) {
  const parts = key.split('.');
  const section = parts[0];
  const subKey = parts.slice(1).join('.');

  // Ajouter au fichier français
  if (!frTranslations[section]) {
    frTranslations[section] = {};
  }

  if (typeof frTranslations[section] === 'object') {
    frTranslations[section][subKey] = text;
  }

  // Ajouter au fichier anglais (même texte pour l'instant)
  if (!enTranslations[section]) {
    enTranslations[section] = {};
  }

  if (typeof enTranslations[section] === 'object') {
    enTranslations[section][subKey] = text;
  }
}

// Fonction pour sauvegarder les fichiers de traduction
function saveTranslationFiles() {
  if (dryRun) {
    console.log('Mode simulation: les fichiers de traduction ne sont pas modifiés');
    return;
  }

  fs.writeFileSync(
    path.join(__dirname, '../src/locales/fr.json'),
    JSON.stringify(frTranslations, null, 2),
    'utf8'
  );

  fs.writeFileSync(
    path.join(__dirname, '../src/locales/en.json'),
    JSON.stringify(enTranslations, null, 2),
    'utf8'
  );

  console.log('Fichiers de traduction mis à jour');
}

// Fonction pour traiter un composant
function processComponent(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const section = suggestSection(filePath);
    const suggestions = [];
    let modifiedContent = content;

    // Parcourir les patterns pour trouver les textes à traduire
    TEXT_PATTERNS.forEach(patternObj => {
      let match;
      patternObj.pattern.lastIndex = 0; // Réinitialiser l'index de recherche

      while ((match = patternObj.pattern.exec(content)) !== null) {
        const text = patternObj.extractText(match);
        const fullMatch = match[0];

        // Ignorer les textes courts ou qui semblent être des variables
        if (!text || text.length < 3 || text.includes('{{') || text.includes('}}') || text.trim() === '') {
          continue;
        }

        // Chercher si une traduction existe déjà
        let translationKey = findTranslationKey(text);

        if (!translationKey) {
          translationKey = suggestKey(text, section);
          addTranslation(translationKey, text);
        }

        // Créer le remplacement
        const replacement = patternObj.createReplacement(match, translationKey);

        suggestions.push({
          text,
          key: translationKey,
          original: fullMatch,
          replacement
        });

        // Remplacer dans le contenu modifié
        modifiedContent = modifiedContent.replace(fullMatch, replacement);
      }
    });

    // Vérifier si le composant utilise déjà useI18n
    const hasUseI18n = content.includes('useI18n');

    // Ajouter l'import useI18n si nécessaire
    if (!hasUseI18n && suggestions.length > 0) {
      const importPattern = /import\s+{([^}]+)}\s+from\s+['"]vue['"]|import\s+Vue\s+from\s+['"]vue['"]/;
      const setupPattern = /setup\s*\(\s*\)\s*{/;

      if (importPattern.test(modifiedContent)) {
        modifiedContent = modifiedContent.replace(
          importPattern,
          (match) => `import { useI18n } from 'vue-i18n'\n${match}`
        );
      }

      if (setupPattern.test(modifiedContent)) {
        modifiedContent = modifiedContent.replace(
          setupPattern,
          (match) => `${match}\n    const { t } = useI18n()`
        );
      }
    }

    // Afficher les résultats
    if (verbose || suggestions.length > 0) {
      console.log(`\nAnalyse du composant: ${filePath}`);
      console.log(`Section suggérée: ${section}`);
      console.log(`Textes à traduire: ${suggestions.length}`);
    }

    if (suggestions.length > 0 && verbose) {
      console.log('\nSuggestions de traduction:');

      suggestions.forEach(suggestion => {
        console.log(`"${suggestion.text}" -> "${suggestion.key}"`);
        console.log(`Remplacer: ${suggestion.original}`);
        console.log(`Par: ${suggestion.replacement}`);
        console.log('---');
      });
    }

    // Sauvegarder le fichier modifié
    if (suggestions.length > 0 && !dryRun) {
      fs.writeFileSync(filePath, modifiedContent, 'utf8');
      console.log(`Composant mis à jour: ${filePath}`);
    }

    return suggestions.length;
  } catch (error) {
    console.error(`Erreur lors du traitement du composant ${filePath}:`, error);
    return 0;
  }
}

// Fonction principale
function main() {
  console.log('Traduction automatique des composants Vue');
  console.log(`Mode: ${dryRun ? 'Simulation' : 'Réel'}`);

  let files;

  if (specificFile) {
    files = [specificFile];
  } else {
    files = glob.sync('src/**/*.vue', { cwd: path.join(__dirname, '..') });
    files = files.map(file => path.join(__dirname, '..', file));
  }

  console.log(`Nombre de fichiers à traiter: ${files.length}`);

  let totalTranslations = 0;

  files.forEach(file => {
    const count = processComponent(file);
    totalTranslations += count;
  });

  console.log(`\nTotal des traductions: ${totalTranslations}`);

  if (totalTranslations > 0) {
    saveTranslationFiles();
  }
}

main();
