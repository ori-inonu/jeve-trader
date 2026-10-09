import React from 'react';
import {createRoot} from 'react-dom/client';
import {MultimarketRoot} from './MultimarketRoot';
import './style.css';
createRoot(document.getElementById('root')!).render(<React.StrictMode><MultimarketRoot/></React.StrictMode>);
