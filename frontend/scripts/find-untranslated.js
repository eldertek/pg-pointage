/**
 * Script pour trouver les chaînes de texte non traduites dans les fichiers Vue
 *
 * Usage: node scripts/find-untranslated.js [path/to/file.vue]
 * Options:
 *   --export=<filename.json> : Exporte les résultats dans un fichier JSON
 *   --min-length=<number>    : Longueur minimale des textes à rechercher (défaut: 3)
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Traitement des arguments
const args = process.argv.slice(2);
const exportFile = args.find(arg => arg.startsWith('--export='))?.split('=')[1] || null;
const minLength = parseInt(args.find(arg => arg.startsWith('--min-length='))?.split('=')[1] || '3', 10);
const specificFile = args.find(arg => !arg.startsWith('--')) || null;

// Expressions régulières pour détecter les textes non traduits
const TEXT_PATTERNS = [
  // Texte dans les balises
  /<(v-btn|v-card-title|v-card-text|v-list-item-title|v-list-item-subtitle|v-tab|h1|h2|h3|h4|h5|h6|p|span|div|label|button)[^>]*>\s*([^<>{$]+?)\s*<\/\1>/g,
  // Texte dans les attributs label
  /label="([^"$][^"]+)"/g,
  // Texte dans les attributs placeholder
  /placeholder="([^"$][^"]+)"/g,
  // Texte dans les attributs title
  /title="([^"$][^"]+)"/g,
  // Texte dans les attributs text
  /text="([^"$][^"]+)"/g,
  // Texte dans les attributs message
  /message="([^"$][^"]+)"/g,
  // Texte dans les attributs error-message
  /error-message="([^"$][^"]+)"/g,
  // Texte dans les règles de validation
  /v => !!v \|\| ['"]([^'"]+)['"]/g,
  // Texte dans les no-data-text et loading-text
  /:no-data-text="([^"$][^"]+)"/g,
  /:loading-text="([^"$][^"]+)"/g,
  // Texte dans les items-per-page-text
  /:items-per-page-text="([^"$][^"]+)"/g,
  // Texte dans les page-text
  /:page-text="([^"$][^"]+)"/g,
  // Texte dans les titres de dialogues
  /state\.title = ['"]([^'"]+)['"]/g,
  /state\.message = ['"]([^'"]+)['"]/g,
  /state\.confirmText = ['"]([^'"]+)['"]/g,
  /state\.cancelText = ['"]([^'"]+)['"]/g,
  // Texte dans les variables computed qui retournent du texte
  /computed\(\(\) => ['"]([^'"]+)['"]\)/g,
  // Texte dans les définitions de variables
  /const [\w]+ = ['"]([^'"]+)['"]/g,
  // Texte dans les snackbars
  /showSuccess\(['"]([^'"]+)['"]\)/g,
  /showError\(['"]([^'"]+)['"]\)/g,
  /snackbar\.text = ['"]([^'"]+)['"]/g,
  // Messages d'alerte et d'erreur
  /alert\(['"]([^'"]+)['"]\)/g,
  /console\.log\(['"]([^}]*?)['"]/g,
  /console\.error\(['"]([^}]*?)['"]/g,
  // Titres de pages
  /title\.value = ['"]([^'"]+)['"]/g,
  // Messages d'information et de confirmation
  /confirm\(['"]([^'"]+)['"]\)/g,
  /prompt\(['"]([^'"]+)['"]\)/g,
  // Texte dans les fonctions d'affichage d'erreur/succès
  /showMessage\(['"]([^'"]+)['"]\)/g,
  /displayError\(['"]([^'"]+)['"]\)/g,
];

// Expressions régulières pour les textes à ignorer
const IGNORE_PATTERNS = [
  /\{\{[^}]+\}\}/,  // Expressions Vue
  /\$t\(/,          // Appels à $t()
  /v-t=/,           // Directive v-t
  /^[0-9\s.,]+$/,   // Chiffres et espaces uniquement
  /^[a-zA-Z0-9_]+$/, // Identifiants simples
  /^[<>=!&|]+$/,    // Opérateurs
  /^\s*$/,          // Espaces uniquement
  /^https?:\/\//,   // URLs
  /^\/[a-zA-Z0-9/]+$/, // Routes
  /^#[a-fA-F0-9]{3,6}$/, // Couleurs hexadécimales
  /^mdi-/,          // Icônes Material Design
  /^dd\/MM\/yyyy/,  // Formats de date
  /\[.*?\]\[.*?\]/, // Messages de log avec des balises
  /\.[a-zA-Z]+$/,   // Extensions de fichiers
  /^v=>/,           // Fonctions lambda
];

// Fonction pour analyser un fichier
function analyzeFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const untranslatedTexts = [];

    // Parcourir les patterns pour trouver les textes non traduits
    TEXT_PATTERNS.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        // Récupération du texte selon le pattern qui a matché
        const text = match[1] || match[2];

        // Ignorer les textes courts ou qui semblent être des variables
        if (!text || text.length < minLength) {
          continue;
        }

        // Ignorer les textes qui correspondent aux patterns à ignorer
        if (IGNORE_PATTERNS.some(ignorePattern => ignorePattern.test(text))) {
          continue;
        }

        // Pour les logs de console, on isole seulement la partie message, pas les parties techniques
        if (pattern.toString().includes('console')) {
          // Ignorer les messages de logs techniques
          if (text.includes('[') && text.includes(']')) {
            continue;
          }
        }

        untranslatedTexts.push({
          text,
          context: match[0]
        });
      }
    });

    // Rechercher tous les tooltips dans le fichier
    const tooltipPatterns = [
      // Format standard des tooltips
      /<v-tooltip[^>]*>\s*([^<>{$]+?)\s*<\/v-tooltip>/g,
      // Tooltips avec activator="parent"
      /<v-tooltip[^>]*activator="parent"[^>]*>\s*([^<>{$]+?)\s*<\/v-tooltip>/g,
      // Tooltips avec expression conditionnelle
      /<v-tooltip[^>]*activator="parent"[^>]*>\s*\{\{\s*([^}]*?)\s*\?\s*['"]([^'"]+)['"]\s*:\s*['"]([^'"]+)['"]\s*\}\}\s*<\/v-tooltip>/g,
      // Capture les textes entre les balises tooltip même s'ils sont sur plusieurs lignes
      /<v-tooltip[^>]*>[\s\n]*([^<>{$]+?)[\s\n]*<\/v-tooltip>/g,
    ];

    tooltipPatterns.forEach(tooltipPattern => {
      let tooltipMatch;
      while ((tooltipMatch = tooltipPattern.exec(content)) !== null) {
        // Dans le cas d'une expression conditionnelle, on capture les deux textes
        const text1 = tooltipMatch[1]?.trim();
        const text2 = tooltipMatch[2]?.trim();
        const text3 = tooltipMatch[3]?.trim();
        
        const textsToCheck = [text1, text2, text3].filter(Boolean);
        
        textsToCheck.forEach(text => {
          // Ignorer les textes courts, vides ou qui sont déjà traduits
          if (!text || text.length < minLength || text.includes('$t(') || text.includes('{{')) {
            return;
          }
          
          // Ignorer les textes qui correspondent aux patterns à ignorer
          if (IGNORE_PATTERNS.some(ignorePattern => ignorePattern.test(text))) {
            return;
          }
          
          // Vérifier si ce texte n'est pas déjà dans la liste
          if (!untranslatedTexts.some(item => item.text === text)) {
            untranslatedTexts.push({
              text,
              context: tooltipMatch[0]
            });
          }
        });
      }
    });

    // Rechercher les textes dans les affectations de variables constantes
    const constAssignmentPattern = /const\s+(\w+)\s*=\s*['"](.*?)['"];?/g;
    let constMatch;
    while ((constMatch = constAssignmentPattern.exec(content)) !== null) {
      const varName = constMatch[1];
      const text = constMatch[2];

      // Ignorer les variables qui ne contiennent probablement pas de texte à traduire
      if (varName.includes('URL') || varName.includes('PATH') || varName.includes('ROUTE') || 
          varName.includes('KEY') || varName.includes('ID') || varName.includes('FORMAT') ||
          varName.includes('Icon') || varName.includes('Color')) {
        continue;
      }

      // Ignorer les textes courts, vides ou déjà traduits
      if (!text || text.length < minLength || text.includes('$t(') || text.includes('{{')) {
        continue;
      }

      // Ignorer les textes qui correspondent aux patterns à ignorer
      if (IGNORE_PATTERNS.some(ignorePattern => ignorePattern.test(text))) {
        continue;
      }

      // Vérifier si ce texte n'est pas déjà dans la liste
      if (!untranslatedTexts.some(item => item.text === text)) {
        untranslatedTexts.push({
          text,
          context: constMatch[0]
        });
      }
    }

    return untranslatedTexts;
  } catch (error) {
    console.error(`Erreur lors de l'analyse du fichier ${filePath}:`, error);
    return [];
  }
}

// Fonction principale
function main() {
  console.log(`Options:`);
  console.log(`  - Longueur minimale des textes: ${minLength} caractères`);
  if (exportFile) {
    console.log(`  - Export vers: ${exportFile}`);
  }
  if (specificFile) {
    console.log(`  - Analyse du fichier spécifique: ${specificFile}`);
  }
  console.log();

  let files;
  if (specificFile) {
    files = [specificFile];
  } else {
    files = glob.sync('src/**/*.vue', { cwd: path.join(__dirname, '..') });
    files = files.map(file => path.join(__dirname, '..', file));
  }

  console.log(`Analyse de ${files.length} fichiers...`);

  let totalUntranslated = 0;
  const fileResults = [];
  const allUntranslatedTexts = new Set();

  files.forEach(file => {
    const untranslatedTexts = analyzeFile(file);
    if (untranslatedTexts.length > 0) {
      fileResults.push({
        file,
        untranslatedTexts,
        count: untranslatedTexts.length
      });
      totalUntranslated += untranslatedTexts.length;

      // Ajouter les textes au set pour l'export
      untranslatedTexts.forEach(item => {
        allUntranslatedTexts.add(item.text);
      });
    }
  });

  // Trier les résultats par nombre de textes non traduits (décroissant)
  fileResults.sort((a, b) => b.count - a.count);

  // Afficher les résultats
  console.log(`\nTotal des textes non traduits: ${totalUntranslated}`);
  console.log('Textes uniques:', allUntranslatedTexts.size);
  console.log('\nFichiers avec des textes non traduits:');

  fileResults.forEach(result => {
    const relativePath = path.relative(process.cwd(), result.file);
    console.log(`\n${relativePath} (${result.count} textes non traduits):`);

    result.untranslatedTexts.forEach((item, index) => {
      if (index < 10) { // Limiter à 10 exemples par fichier pour éviter de surcharger la console
        console.log(`  - "${item.text}"`);
      } else if (index === 10) {
        console.log(`  - ... et ${result.count - 10} autres`);
      }
    });
  });

  // Exporter les résultats si demandé
  if (exportFile) {
    try {
      // Trier les textes par ordre alphabétique
      const sortedTexts = Array.from(allUntranslatedTexts).sort();
      
      // Créer un objet avec les textes comme clés et des valeurs vides
      const translationObject = {};
      sortedTexts.forEach(text => {
        translationObject[text] = '';
      });
      
      // Créer également un format pour i18n avec français comme langue par défaut
      const i18nObject = {
        fr: {},
        en: {}
      };
      
      sortedTexts.forEach(text => {
        // Générer une clé basée sur le texte (en supprimant les caractères spéciaux)
        const key = text
          .toLowerCase()
          .replace(/[^a-zA-Z0-9_]/g, '_')
          .replace(/_+/g, '_')
          .replace(/^_|_$/g, '');
        
        i18nObject.fr[key] = text;  // Le texte français reste le même
        i18nObject.en[key] = '';    // À traduire en anglais
      });
      
      // Écrire les deux formats
      fs.writeFileSync(exportFile, JSON.stringify(translationObject, null, 2));
      
      // Écrire le format i18n dans un second fichier
      const i18nFileName = exportFile.replace('.json', '_i18n.json');
      fs.writeFileSync(i18nFileName, JSON.stringify(i18nObject, null, 2));
      
      console.log(`\nExport terminé:`);
      console.log(`- Format simple: ${exportFile}`);
      console.log(`- Format i18n: ${i18nFileName}`);
    } catch (error) {
      console.error(`Erreur lors de l'export des résultats:`, error);
    }
  }
}

main();
