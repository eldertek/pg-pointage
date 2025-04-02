const sharp = require('sharp');
const fs = require('fs').promises;
const path = require('path');

const ICON_SIZES = [
  16, 32, 72, 96, 128, 144, 152, 192, 384, 512
];

async function generateIcons() {
  // Créer le dossier icons s'il n'existe pas
  const iconsDir = path.join(__dirname, '../public/assets/icons');
  try {
    await fs.mkdir(iconsDir, { recursive: true });
  } catch (err) {
    if (err.code !== 'EEXIST') throw err;
  }

  // Utiliser l'icône SVG personnalisée
  const svgPath = path.join(__dirname, '../public/assets/icons/icon.svg');
  const svg = await fs.readFile(svgPath);

  // Générer les différentes tailles d'icônes
  for (const iconSize of ICON_SIZES) {
    await sharp(svg)
      .resize(iconSize, iconSize)
      .toFile(path.join(iconsDir, `icon-${iconSize}x${iconSize}.png`));
    
    console.log(`✓ Généré icon-${iconSize}x${iconSize}.png`);
  }

  // Générer le favicon.ico
  await sharp(svg)
    .resize(32, 32)
    .toFile(path.join(__dirname, '../public/favicon.ico'));
  
  console.log('✓ Généré favicon.ico');

  // Générer l'icône Safari Pinned Tab en noir
  await sharp(svg)
    .resize(512, 512)
    .toFile(path.join(iconsDir, 'safari-pinned-tab.svg'));
  
  console.log('✓ Généré safari-pinned-tab.svg');
}

generateIcons().catch(console.error); 