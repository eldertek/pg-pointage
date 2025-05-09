import QRCode from 'qrcode'

interface QRCodeOptions {
  width?: number;
  height?: number;
  qrSize?: number;
  showFrame?: boolean;
  radius?: number;
}

export const generateStyledQRCode = async (site: {
  id: number;
  name: string;
  nfc_id: string;
}, options: QRCodeOptions = {}): Promise<string> => {
  const {
    width = 500,
    height = 700,
    qrSize = 400,
    showFrame = true,
    radius = 20
  } = options;

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    throw new Error('Could not get canvas context');
  }

  canvas.width = width;
  canvas.height = height;

  // Fond blanc
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, width, height);

  // Générer le QR Code avec qrcode
  const qrData = JSON.stringify({
    type: 'PG_SITE',
    site_id: site.id,
    nfc_id: site.nfc_id,
    name: site.name
  });

  try {
    // Charger le logo
    const logo = new Image();
    await new Promise<void>((resolve, reject) => {
      logo.onload = () => resolve();
      logo.onerror = (error) => reject(error);
      logo.src = '/assets/logo/logo.svg';
    });

    // Calculer la taille du logo (20% de la taille du QR code)
    const logoSize = qrSize * 0.2;
    const logoAspectRatio = logo.width / logo.height;
    const logoWidth = logoSize;
    const logoHeight = logoSize / logoAspectRatio;

    // Générer le QR code
    const qrCodeDataUrl = await QRCode.toDataURL(qrData, {
      width: qrSize,
      margin: 1,
      color: {
        dark: '#00346E',
        light: '#FFFFFF'
      }
    });

    const qrImage = new Image();
    await new Promise<void>((resolve, reject) => {
      qrImage.onload = () => resolve();
      qrImage.onerror = (error) => reject(error);
      qrImage.src = qrCodeDataUrl;
    });

    const qrX = (width - qrSize) / 2;
    const qrY = showFrame ? 50 : 0;
    ctx.drawImage(qrImage, qrX, qrY, qrSize, qrSize);

    // Dessiner le logo au centre du QR code
    const logoX = qrX + (qrSize - logoWidth) / 2;
    const logoY = qrY + (qrSize - logoHeight) / 2;

    // Créer un cercle blanc pour le fond du logo
    ctx.beginPath();
    ctx.arc(logoX + logoWidth/2, logoY + logoHeight/2, logoWidth/2 + 5, 0, Math.PI * 2);
    ctx.fillStyle = '#FFFFFF';
    ctx.fill();

    // Dessiner le logo
    ctx.drawImage(logo, logoX, logoY, logoWidth, logoHeight);

    if (showFrame) {
      ctx.strokeStyle = '#F78C48';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(100, 480);
      ctx.lineTo(width - 100, 480);
      ctx.stroke();

      // Configuration du texte
      ctx.fillStyle = '#F78C48';
      ctx.font = 'bold 24px Arial';
      ctx.textAlign = 'center';
      
      // Calculer la largeur maximale disponible pour le texte
      const maxWidth = width - 100;
      
      // Fonction pour découper le texte en lignes
      const getLines = (text: string, maxWidth: number): string[] => {
        const words = text.split(' ');
        const lines = [];
        let currentLine = words[0];

        for (let i = 1; i < words.length; i++) {
          const word = words[i];
          const width = ctx.measureText(currentLine + ' ' + word).width;
          if (width < maxWidth) {
            currentLine += ' ' + word;
          } else {
            lines.push(currentLine);
            currentLine = word;
          }
        }
        lines.push(currentLine);
        return lines;
      };

      // Découper le texte en lignes
      const lines = getLines(site.name, maxWidth - 40);
      
      // Calculer la hauteur totale du texte
      const lineHeight = 30;
      const totalHeight = lines.length * lineHeight;
      
      // Position de départ pour le texte
      let y = 530;
      
      // Ajuster la position verticale si nécessaire pour centrer le texte
      if (lines.length > 1) {
        y = y - (totalHeight / 2) + (lineHeight / 2);
      }
      
      // Dessiner chaque ligne
      lines.forEach((line, index) => {
        ctx.fillText(line, width / 2, y + (index * lineHeight));
      });
    }

    return canvas.toDataURL('image/png');
  } catch (error) {
    throw error;
  }
}; 