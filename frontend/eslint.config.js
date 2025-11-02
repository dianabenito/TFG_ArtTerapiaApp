import js from "@eslint/js";
import globals from "globals";
import pluginVue from "eslint-plugin-vue";
import { defineConfig } from "eslint/config";

export default defineConfig([
  {
    files: ["**/*.{js,mjs,cjs,vue}"],
    plugins: { js },
    extends: ["js/recommended"],
    languageOptions: { globals: globals.browser },
  },
  pluginVue.configs["flat/essential"], // mantener config de Vue
  {
    files: ["**/*.vue"], // aplicar solo a archivos .vue
    rules: {
      "vue/no-multiple-template-root": "off",
    },
  },
]);
