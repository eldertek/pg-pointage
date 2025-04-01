module.exports = {
  root: true,
  env: {
    node: true,
    browser: true,
    es2021: true,
  },
  extends: [
    'plugin:vue/vue3-recommended',
    'eslint:recommended',
    'prettier'
  ],
  parserOptions: {
    ecmaVersion: 2021,
    parser: '@typescript-eslint/parser'
  },
  plugins: [
    '@typescript-eslint',
    'vue'
  ],
  rules: {
    'no-unused-vars': 'warn',
    '@typescript-eslint/no-unused-vars': ['warn', {
      'argsIgnorePattern': '^_',
      'varsIgnorePattern': '^_',
      'caughtErrorsIgnorePattern': '^_'
    }],
    'vue/no-unused-components': 'warn',
    'vue/no-unused-vars': 'warn',
    'vue/no-unused-properties': 'warn',
    'vue/no-unused-refs': 'warn',
    'vue/multi-word-component-names': 'warn',
    'vue/valid-v-slot': ['error', {
      'allowModifiers': true
    }],
    'no-undef': 'error',
    'no-redeclare': 'error'
  }
} 