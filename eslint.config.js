export default [
  {
    files: ['**/*.js'],
    ignores: ['node_modules/**', 'app/static/dist/**'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
    },
    plugins: {
    },
    rules: {
      quotes: ['error', 'single'],
      semi: ['error', 'always'],
      'no-unused-vars': ['warn'],
      'no-console': 'off'
    }
  }
];
