# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is **enabled** in this project using `babel-plugin-react-compiler` (target: 19) in [vite.config.js](file:///C:/Users/PC/Desktop/bon/chatbot/frontend/vite.config.js).

### Production Build Metrics (Measured)
- **Build Time**: ~476ms
- **JS Bundle**: 193.01 kB (Gzip: 60.93 kB)
- **CSS Bundle**: 1.36 kB (Gzip: 0.58 kB)
- **HTML**: 0.45 kB (Gzip: 0.29 kB)

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
