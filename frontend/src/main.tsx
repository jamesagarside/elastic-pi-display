// Fonts are bundled locally: the display may have no egress to CDNs.
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/roboto-mono/400.css';
import '@fontsource/roboto-mono/700.css';

import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';
import { registerIcons } from './theme/icons';

registerIcons();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
