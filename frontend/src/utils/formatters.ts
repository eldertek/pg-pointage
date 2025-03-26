/**
 * Formate un numéro de téléphone au format XX XX XX XX XX
 * @param phone Le numéro de téléphone à formater
 * @returns Le numéro de téléphone formaté
 */
export function formatPhoneNumber(phone: string): string {
    if (!phone) return '';
    
    // Supprimer tous les caractères non numériques
    const numbers = phone.replace(/\D/g, '');
    
    // Si le numéro n'a pas 10 chiffres, retourner le numéro original
    if (numbers.length !== 10) return phone;
    
    // Formater le numéro avec des espaces
    return numbers.replace(/(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/, '$1 $2 $3 $4 $5');
}

export function formatAddressForMaps(address: string, postalCode: string, city: string, country: string = 'France'): string {
  const fullAddress = `${address}, ${postalCode} ${city}, ${country}`;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(fullAddress)}`;
} 