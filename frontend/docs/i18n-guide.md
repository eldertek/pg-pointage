# Guide d'internationalisation (i18n)

Ce document explique comment utiliser le système d'internationalisation dans l'application.

## Structure

L'internationalisation est gérée par [vue-i18n](https://vue-i18n.intlify.dev/) et est configurée dans `src/plugins/i18n.js`.

Les fichiers de traduction se trouvent dans `src/locales/` :
- `fr.json` : Traductions en français
- `en.json` : Traductions en anglais

## Utilisation dans les templates Vue

### Méthode 1 : Directive `v-t`

```vue
<template>
  <div v-t="'common.save'"></div>
</template>
```

### Méthode 2 : Fonction `$t`

```vue
<template>
  <div>{{ $t('common.save') }}</div>
</template>
```

### Méthode 3 : Composant `Translation`

```vue
<template>
  <Translation keyPath="common.save" />
</template>
```

## Utilisation dans le code JavaScript

```js
import { useI18n } from 'vue-i18n';

export default {
  setup() {
    const { t, locale } = useI18n();
    
    // Obtenir une traduction
    const saveText = t('common.save');
    
    // Changer la langue
    locale.value = 'en';
    
    return { t, locale };
  }
}
```

## Structure des fichiers de traduction

Les fichiers de traduction sont organisés par sections :

```json
{
  "common": {
    "save": "Enregistrer",
    "cancel": "Annuler"
  },
  "users": {
    "title": "Utilisateurs"
  }
}
```

## Ajouter une nouvelle traduction

1. Identifiez la section appropriée dans les fichiers de traduction
2. Ajoutez votre clé et sa traduction dans `fr.json` et `en.json`
3. Utilisez la clé dans votre composant

## Paramètres dans les traductions

Vous pouvez utiliser des paramètres dans vos traductions :

```json
{
  "common": {
    "welcome": "Bienvenue, {name}!"
  }
}
```

```vue
<template>
  <div>{{ $t('common.welcome', { name: 'John' }) }}</div>
</template>
```

## Pluralisation

```json
{
  "common": {
    "items": "Aucun élément | Un élément | {count} éléments"
  }
}
```

```vue
<template>
  <div>{{ $tc('common.items', count, { count }) }}</div>
</template>
```

## Outils d'aide à la migration

Un script d'aide à la migration est disponible pour analyser les composants et suggérer des traductions :

```bash
node scripts/i18n-migration.js path/to/component.vue
```

## Bonnes pratiques

1. Utilisez des clés descriptives et organisées par section
2. Évitez les traductions dupliquées
3. Utilisez des paramètres pour les textes dynamiques
4. Testez vos traductions dans les deux langues
5. Utilisez le composant `Translation` pour les textes complexes
