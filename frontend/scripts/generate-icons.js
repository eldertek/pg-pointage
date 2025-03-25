const sharp = require('sharp');
const fs = require('fs').promises;
const path = require('path');

const ICON_SIZES = [
  16, 32, 72, 96, 128, 144, 152, 192, 384, 512
];

async function generateIcons() {
  // Créer le dossier icons s'il n'existe pas
  const iconsDir = path.join(__dirname, '../public/icons');
  try {
    await fs.mkdir(iconsDir, { recursive: true });
  } catch (err) {
    if (err.code !== 'EEXIST') throw err;
  }

  // Créer une image de base avec du texte
  const size = 512; // Taille de base
  const svg = `
    <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="#1976D2"/>
      <text x="50%" y="50%" font-family="Arial" font-size="200" 
            fill="white" text-anchor="middle" dominant-baseline="middle">
        PG
      </text>
    </svg>
  `;

  // Générer les différentes tailles d'icônes
  for (const iconSize of ICON_SIZES) {
    await sharp(Buffer.from(svg))
      .resize(iconSize, iconSize)
      .toFile(path.join(iconsDir, `icon-${iconSize}x${iconSize}.png`));
    
    console.log(`✓ Généré icon-${iconSize}x${iconSize}.png`);
  }

  // Générer le favicon.ico
  await sharp(Buffer.from(svg))
    .resize(32, 32)
    .toFile(path.join(__dirname, '../public/favicon.ico'));
  
  console.log('✓ Généré favicon.ico');

  // Générer l'icône Safari Pinned Tab
  const svgPinnedTab = `
    <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
      <text x="50%" y="50%" font-family="Arial" font-size="200" 
            fill="black" text-anchor="middle" dominant-baseline="middle">
        PG
      </text>
    </svg>
  `;

  await fs.writeFile(
    path.join(iconsDir, 'safari-pinned-tab.svg'),
    svgPinnedTab
  );
  
  console.log('✓ Généré safari-pinned-tab.svg');
}

generateIcons().catch(console.error); 