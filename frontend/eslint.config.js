import js from '@eslint/js';
export default [{ignores:['dist/**','node_modules/**']},js.configs.recommended,{files:['**/*.jsx'],languageOptions:{ecmaVersion:'latest',sourceType:'module',parserOptions:{ecmaFeatures:{jsx:true}},globals:{React:'readonly',document:'readonly',fetch:'readonly',setTimeout:'readonly',console:'readonly',window:'readonly'}},rules:{'no-unused-vars':'warn'}}];
